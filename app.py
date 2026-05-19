\
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import conectar, iniciar_banco
from pdf import gerar_pdf_orcamento
from datetime import datetime
from functools import wraps
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


def moeda(valor):
    return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


app.jinja_env.filters["moeda"] = moeda


def parse_valor(valor):
    if valor is None or str(valor).strip() == "":
        return 0.0
    return float(str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip())


def login_obrigatorio(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def criar_admin_padrao():
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario=%s", (admin_user,))
    existe = cur.fetchone()

    if not existe:
        cur.execute(
            "INSERT INTO usuarios (usuario, senha_hash) VALUES (%s, %s)",
            (admin_user, generate_password_hash(admin_password)),
        )
        conn.commit()

    cur.close()
    conn.close()


@app.before_request
def preparar():
    iniciar_banco()
    criar_admin_padrao()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario=%s", (usuario,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user["senha_hash"], senha):
            session["usuario"] = usuario
            return redirect(url_for("dashboard"))

        flash("Usuário ou senha inválidos.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_obrigatorio
def dashboard():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(valor),0) AS total FROM financeiro WHERE tipo='receita'")
    receitas = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(valor),0) AS total FROM financeiro WHERE tipo='despesa'")
    despesas = cur.fetchone()["total"]

    saldo = float(receitas) - float(despesas)

    cur.execute("SELECT COALESCE(SUM(lucro_estimado),0) AS total FROM orcamentos")
    lucro_orcamentos = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM clientes")
    qtd_clientes = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM tarefas WHERE status!='concluida'")
    qtd_tarefas = cur.fetchone()["total"]

    cur.execute("SELECT * FROM financeiro ORDER BY id DESC LIMIT 8")
    ultimos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        receitas=receitas,
        despesas=despesas,
        saldo=saldo,
        lucro_orcamentos=lucro_orcamentos,
        qtd_clientes=qtd_clientes,
        qtd_tarefas=qtd_tarefas,
        ultimos=ultimos,
    )


@app.route("/clientes", methods=["GET", "POST"])
@login_obrigatorio
def clientes():
    conn = conectar()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            """
            INSERT INTO clientes (nome, documento, telefone, endereco, email, observacao)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                request.form["nome"],
                request.form.get("documento"),
                request.form.get("telefone"),
                request.form.get("endereco"),
                request.form.get("email"),
                request.form.get("observacao"),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Cliente cadastrado com sucesso.")
        return redirect(url_for("clientes"))

    cur.execute("SELECT * FROM clientes ORDER BY id DESC")
    lista = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("clientes.html", clientes=lista)


@app.route("/financeiro", methods=["GET", "POST"])
@login_obrigatorio
def financeiro():
    conn = conectar()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            """
            INSERT INTO financeiro (tipo, descricao, categoria, valor, forma_pagamento, data_movimento, observacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                request.form["tipo"],
                request.form["descricao"],
                request.form.get("categoria"),
                parse_valor(request.form["valor"]),
                request.form.get("forma_pagamento"),
                request.form.get("data_movimento") or datetime.now().strftime("%Y-%m-%d"),
                request.form.get("observacao"),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Movimento financeiro registrado.")
        return redirect(url_for("financeiro"))

    cur.execute("SELECT * FROM financeiro ORDER BY id DESC")
    lista = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("financeiro.html", movimentos=lista)


@app.route("/tarefas", methods=["GET", "POST"])
@login_obrigatorio
def tarefas():
    conn = conectar()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute(
            """
            INSERT INTO tarefas (titulo, descricao, status, prioridade, vencimento)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                request.form["titulo"],
                request.form.get("descricao"),
                request.form.get("status", "pendente"),
                request.form.get("prioridade", "normal"),
                request.form.get("vencimento") or None,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Tarefa cadastrada.")
        return redirect(url_for("tarefas"))

    cur.execute("SELECT * FROM tarefas ORDER BY id DESC")
    lista = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("tarefas.html", tarefas=lista)


@app.route("/tarefas/<int:tarefa_id>/concluir")
@login_obrigatorio
def concluir_tarefa(tarefa_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("UPDATE tarefas SET status='concluida' WHERE id=%s", (tarefa_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Tarefa concluída.")
    return redirect(url_for("tarefas"))


@app.route("/orcamentos", methods=["GET", "POST"])
@login_obrigatorio
def orcamentos():
    conn = conectar()
    cur = conn.cursor()

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id") or None
        cliente_nome = request.form.get("cliente_nome", "").strip()

        if cliente_id:
            cur.execute("SELECT * FROM clientes WHERE id=%s", (cliente_id,))
            cliente = cur.fetchone()
            if cliente:
                cliente_nome = cliente["nome"]

        if not cliente_nome:
            flash("Informe um cliente cadastrado ou preencha o nome do cliente avulso.")
            return redirect(url_for("orcamentos"))

        materiais = parse_valor(request.form.get("valor_materiais"))
        mao_obra = parse_valor(request.form.get("valor_mao_obra"))
        despesas_extras = parse_valor(request.form.get("despesas_extras"))
        total = materiais + mao_obra
        lucro_estimado = total - materiais - despesas_extras

        cur.execute(
            """
            INSERT INTO orcamentos (
                cliente_id, cliente_nome, servico, quantidade, valor_materiais,
                valor_mao_obra, despesas_extras, total, lucro_estimado,
                status, forma_pagamento, observacao
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                cliente_id,
                cliente_nome,
                request.form["servico"],
                request.form.get("quantidade"),
                materiais,
                mao_obra,
                despesas_extras,
                total,
                lucro_estimado,
                request.form.get("status", "gerado"),
                request.form.get("forma_pagamento"),
                request.form.get("observacao"),
            ),
        )

        orcamento_id = cur.fetchone()["id"]

        cur.execute(
            """
            INSERT INTO financeiro (tipo, descricao, categoria, valor, forma_pagamento, data_movimento, observacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "receita",
                f"Orçamento #{orcamento_id} - {request.form['servico']}",
                "Orçamento",
                total,
                request.form.get("forma_pagamento"),
                datetime.now().strftime("%Y-%m-%d"),
                "Receita prevista gerada pelo orçamento",
            ),
        )

        if materiais > 0:
            cur.execute(
                """
                INSERT INTO financeiro (tipo, descricao, categoria, valor, forma_pagamento, data_movimento, observacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    "despesa",
                    f"Materiais orçamento #{orcamento_id}",
                    "Materiais",
                    materiais,
                    request.form.get("forma_pagamento"),
                    datetime.now().strftime("%Y-%m-%d"),
                    "Custo de materiais informado no orçamento",
                ),
            )

        if despesas_extras > 0:
            cur.execute(
                """
                INSERT INTO financeiro (tipo, descricao, categoria, valor, forma_pagamento, data_movimento, observacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    "despesa",
                    f"Despesas extras orçamento #{orcamento_id}",
                    "Despesas extras",
                    despesas_extras,
                    request.form.get("forma_pagamento"),
                    datetime.now().strftime("%Y-%m-%d"),
                    "Despesas adicionais informadas no orçamento",
                ),
            )

        conn.commit()
        cur.close()
        conn.close()
        flash("Orçamento criado e lançado no financeiro.")
        return redirect(url_for("orcamentos"))

    cur.execute("SELECT * FROM clientes ORDER BY nome")
    clientes = cur.fetchall()
    cur.execute("SELECT * FROM orcamentos ORDER BY id DESC")
    lista = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("orcamentos.html", orcamentos=lista, clientes=clientes)


@app.route("/orcamentos/<int:orcamento_id>/pdf")
@login_obrigatorio
def baixar_pdf(orcamento_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orcamentos WHERE id=%s", (orcamento_id,))
    orcamento = cur.fetchone()
    cur.close()
    conn.close()

    if not orcamento:
        flash("Orçamento não encontrado.")
        return redirect(url_for("orcamentos"))

    arquivo = gerar_pdf_orcamento(orcamento)
    return send_file(arquivo, as_attachment=True)


@app.route("/manifest.json")
def manifest():
    return send_file("static/manifest.json")


@app.route("/service-worker.js")
def sw():
    return send_file("static/service-worker.js")


if __name__ == "__main__":
    iniciar_banco()
    criar_admin_padrao()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
