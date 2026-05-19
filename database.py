\
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from urllib.parse import urlparse


def get_database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não configurado. Configure o PostgreSQL no .env ou no servidor.")
    # Render às vezes usa postgres://; psycopg2 aceita, mas mantemos compatibilidade.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def conectar():
    conn = psycopg2.connect(get_database_url(), cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def iniciar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        usuario VARCHAR(120) UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        documento TEXT,
        telefone TEXT,
        endereco TEXT,
        email TEXT,
        observacao TEXT,
        criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tarefas (
        id SERIAL PRIMARY KEY,
        titulo TEXT NOT NULL,
        descricao TEXT,
        status TEXT DEFAULT 'pendente',
        prioridade TEXT DEFAULT 'normal',
        vencimento DATE,
        criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS financeiro (
        id SERIAL PRIMARY KEY,
        tipo TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
        descricao TEXT NOT NULL,
        categoria TEXT,
        valor NUMERIC(12,2) NOT NULL,
        forma_pagamento TEXT,
        data_movimento DATE NOT NULL DEFAULT CURRENT_DATE,
        observacao TEXT,
        criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orcamentos (
        id SERIAL PRIMARY KEY,
        cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
        cliente_nome TEXT NOT NULL,
        servico TEXT NOT NULL,
        quantidade TEXT,
        valor_materiais NUMERIC(12,2) DEFAULT 0,
        valor_mao_obra NUMERIC(12,2) DEFAULT 0,
        despesas_extras NUMERIC(12,2) DEFAULT 0,
        total NUMERIC(12,2) DEFAULT 0,
        lucro_estimado NUMERIC(12,2) DEFAULT 0,
        status TEXT DEFAULT 'gerado',
        forma_pagamento TEXT,
        observacao TEXT,
        criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """)

    conn.commit()
    cur.close()
    conn.close()
