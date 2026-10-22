# HelpDesk API

[![CI](https://github.com/AllanNattan/helpdesk-api/actions/workflows/ci.yml/badge.svg)](https://github.com/AllanNattan/helpdesk-api/actions/workflows/ci.yml)

API REST para gerenciamento corporativo de chamados de suporte técnico, com autenticação, controle de acesso e histórico de alterações.

## Tecnologias

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy e Alembic
- Pytest e Ruff
- JWT e Argon2

## Requisitos

- Python 3.12
- Git
- PostgreSQL

## Funcionalidades

- Autenticação com tokens JWT.
- Armazenamento seguro de senhas com Argon2.
- Controle de acesso por perfil de usuário.
- Criação e consulta de chamados.
- Atualização do status dos chamados.
- Histórico de alterações dos chamados.

## Instalação

Clone o repositório:

```bash
git clone https://github.com/AllanNattan/helpdesk-api.git
cd helpdesk-api
```

Crie e ative o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install -e ".[dev]"
```

## Configuração

Crie o arquivo `.env` a partir do modelo:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:

- `DATABASE_PASSWORD`: senha do usuário do PostgreSQL.
- `JWT_SECRET_KEY`: chave aleatória com pelo menos 32 caracteres.

Para gerar uma chave JWT aleatória, você pode executar no terminal Bash:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie o resultado para `JWT_SECRET_KEY` no arquivo `.env`.

Não publique o arquivo `.env` no GitHub.

## Banco de dados

A API utiliza PostgreSQL. O banco de dados esperado é `helpdesk_db` e o usuário é `helpdesk_app`, conforme a configuração padrão do projeto.

Se o usuário e o banco ainda não existirem, abra o terminal Bash do Linux e execute:

```bash
sudo -u postgres psql
```

Esse comando abre o terminal interativo do PostgreSQL. Você saberá que entrou nele quando aparecer um prompt parecido com `postgres=#`.

Dentro desse prompt, execute:

```sql
CREATE USER helpdesk_app WITH PASSWORD 'SUA_SENHA';
CREATE DATABASE helpdesk_db OWNER helpdesk_app;
\q
```

Substitua `SUA_SENHA` por uma senha escolhida por você e configure a mesma senha em `DATABASE_PASSWORD` no arquivo `.env`.

Se o usuário e o banco já existirem, não execute novamente os comandos de criação.

Depois de configurar o banco e o arquivo `.env`, aplique as migrações:

```bash
python -m alembic upgrade head
```

## Executar a API

Inicie o servidor de desenvolvimento:

```bash
python -m uvicorn app.main:app --reload
```

Acesse a documentação interativa no navegador:

http://127.0.0.1:8000/docs

Para encerrar o servidor, pressione `Ctrl+C` no terminal em que ele está rodando.

## Testes

Execute os testes automatizados:

```bash
python -m pytest
```

## Qualidade do código

Para aplicar correções automáticas de estilo:

```bash
python -m ruff check --fix .
```

Depois, verifique o código:

```bash
python -m ruff check .
```

## Integração contínua

O GitHub Actions executa automaticamente as verificações de qualidade e os testes configurados no projeto quando há atualizações no repositório e pull requests para a branch principal.

## Status

Projeto em desenvolvimento, com autenticação, gerenciamento de chamados, histórico de alterações, migrações de banco de dados e testes automatizados.