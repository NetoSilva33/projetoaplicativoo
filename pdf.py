\
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


def moeda(valor):
    return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf_orcamento(orcamento):
    pasta = Path("orcamentos_pdf")
    pasta.mkdir(exist_ok=True)

    nome = str(orcamento["cliente_nome"]).replace(" ", "_").replace("/", "_")
    arquivo = pasta / f"orcamento_{orcamento['id']}_{nome}.pdf"

    c = canvas.Canvas(str(arquivo), pagesize=A4)
    largura, altura = A4
    y = altura - 2 * cm

    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, y, "ORÇAMENTO COMERCIAL")
    y -= 0.9 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, "Sistema Empresarial - Orçamentos e Gestão")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Data: {datetime.now().strftime('%d/%m/%Y')}")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Dados do Cliente")
    y -= 0.7 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Cliente: {orcamento['cliente_nome']}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Serviço: {orcamento['servico']}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Quantidade: {orcamento.get('quantidade') or ''}")
    y -= 0.8 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Valores")
    y -= 0.7 * cm

    c.setFont("Helvetica", 10)
    linhas = [
        ("Materiais", orcamento["valor_materiais"]),
        ("Mão de obra", orcamento["valor_mao_obra"]),
        ("Despesas extras", orcamento["despesas_extras"]),
        ("Total", orcamento["total"]),
        ("Lucro estimado", orcamento["lucro_estimado"]),
    ]

    for titulo, valor in linhas:
        c.drawString(2 * cm, y, f"{titulo}: {moeda(valor)}")
        y -= 0.5 * cm

    y -= 0.4 * cm
    c.drawString(2 * cm, y, f"Forma de pagamento: {orcamento.get('forma_pagamento') or ''}")
    y -= 1 * cm

    c.setFont("Helvetica", 9)
    obs = orcamento.get("observacao") or "Orçamento sujeito à análise técnica e disponibilidade de materiais."
    c.drawString(2 * cm, y, f"Observação: {str(obs)[:120]}")
    y -= 2 * cm

    c.line(2 * cm, y, 8 * cm, y)
    c.line(11 * cm, y, 18 * cm, y)
    y -= 0.5 * cm
    c.drawString(2.5 * cm, y, "Assinatura do Cliente")
    c.drawString(12 * cm, y, "Assinatura do Fornecedor")

    c.save()
    return str(arquivo)
