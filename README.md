# ERP Empresarial com PostgreSQL + PWA

Sistema empresarial responsivo para desktop e celular.

## Recursos

- Login de administrador
- Banco PostgreSQL
- Dashboard financeiro
- Clientes
- Orçamentos com PDF
- Receitas e despesas
- Tarefas
- PWA: pode ser adicionado à tela inicial do celular
- Configuração pronta para Render
- Arquivo `render.yaml` para criar Web Service + PostgreSQL

## Usuário padrão

Configure no Render:

```text
ADMIN_USER=admin
ADMIN_PASSWORD=sua_senha_forte
```

Se rodar localmente com `.env.example`, o padrão é:

```text
Usuário: admin
Senha: admin123
```

Troque essa senha antes de usar de verdade.

## Rodar localmente com PostgreSQL

1. Instale PostgreSQL.
2. Crie um banco chamado `empresa`.
3. Copie `.env.example` para `.env`.
4. Ajuste a variável:

```text
DATABASE_URL=postgresql://usuario:senha@localhost:5432/empresa
```

5. Instale dependências:

```bash
pip install -r requirements.txt
```

6. Rode:

```bash
python app.py
```

7. Acesse:

```text
http://localhost:5000
```

## Deploy no Render

### Opção recomendada: Blueprint

1. Suba esta pasta para um repositório no GitHub.
2. Entre no Render.
3. Escolha **New > Blueprint**.
4. Selecione o repositório.
5. O Render vai ler o arquivo `render.yaml`.
6. Ele criará:
   - Web Service Python
   - Banco PostgreSQL
   - Variável DATABASE_URL
7. Altere `ADMIN_PASSWORD` para uma senha forte.

### Configuração manual

Crie um banco PostgreSQL no Render e copie a connection string.

Crie um Web Service com:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

Adicione as variáveis:

```text
DATABASE_URL=sua_connection_string_do_postgres
SECRET_KEY=uma_chave_segura
ADMIN_USER=admin
ADMIN_PASSWORD=sua_senha_forte
```

## Usar no celular como app

1. Abra o link do Render no Safari/Chrome.
2. No iPhone, toque em compartilhar.
3. Toque em **Adicionar à Tela de Início**.
4. No Android, toque no menu do Chrome e em **Adicionar à tela inicial**.

## Observação

Esta versão já está pronta para uso online, mas ainda é uma base inicial. Para uso comercial real, recomenda-se adicionar:
- backup automático;
- troca de senha pelo painel;
- níveis de usuário;
- relatórios em PDF;
- exportação Excel;
- logs de auditoria.
