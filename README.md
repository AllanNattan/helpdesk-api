# HelpDesk API

[![CI](https://github.com/AllanNattan/helpdesk-api/actions/workflows/ci.yml/badge.svg)](https://github.com/AllanNattan/helpdesk-api/actions/workflows/ci.yml)

API REST para gerenciamento corporativo de chamados de suporte técnico, com autenticação, controle de acesso, histórico de alterações e comentários.

## Tecnologias

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Pydantic
- Pytest
- Ruff
- JWT
- Argon2
- Docker
- Docker Compose
- Git e GitHub
- GitHub Actions

## Funcionalidades

- Autenticação com tokens JWT.
- Armazenamento seguro de senhas com Argon2.
- Controle de acesso com base no perfil do usuário.
- Criação e consulta de chamados de suporte.
- Listagem paginada de chamados.
- Filtros por status e prioridade.
- Atualização de chamados com validação das transições de status.
- Atribuição e remoção de responsáveis.
- Controle de acesso aos chamados de acordo com o solicitante.
- Registro do histórico de alterações dos chamados.
- Armazenamento dos valores anteriores e novos de cada alteração.
- Criação e consulta de comentários nos chamados.
- Ordenação cronológica do histórico e dos comentários.
- Validação dos dados de entrada.
- Migrações versionadas do banco de dados.
- Testes automatizados com Pytest.
- Verificação de qualidade do código com Ruff.
- Execução conteinerizada com Docker e PostgreSQL.
- Integração contínua com GitHub Actions.

## Requisitos

Para executar o projeto localmente:

- Python 3.12.
- Git.
- PostgreSQL.

Para executar com Docker:

- Docker Engine.
- Docker Compose v2.

## Instalação

Clone o repositório:

```bash
git clone https://github.com/AllanNattan/helpdesk-api.git
cd helpdesk-api
```

Crie o ambiente virtual:

```bash
python3 -m venv .venv
```

Ative o ambiente virtual no Linux:

```bash
source .venv/bin/activate
```

Instale as dependências do projeto:

```bash
python -m pip install -e ".[dev]"
```

## Configuração

Crie o arquivo `.env` a partir do modelo disponibilizado no projeto:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure as variáveis necessárias para executar a aplicação.

### Banco de dados

Configure a senha do usuário do PostgreSQL por meio da variável `DATABASE_PASSWORD`.

A URL de conexão é montada pela configuração da aplicação, utilizando as variáveis definidas no arquivo `.env`.

### Chave JWT

Configure `JWT_SECRET_KEY` com uma chave aleatória de pelo menos 32 caracteres.

Para gerar uma chave, execute:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie o resultado para a variável `JWT_SECRET_KEY` no arquivo `.env`.

**Segurança:** nunca publique o arquivo `.env`, senhas, tokens ou outras credenciais no GitHub.

## Executar com Docker

O Docker Compose inicia a API e um servidor PostgreSQL em contêineres separados. O banco utilizado nesse ambiente é independente de uma instalação local do PostgreSQL.

### 1. Configurar as variáveis de ambiente

Se ainda não existir um arquivo `.env`, crie-o a partir do modelo:

```bash
cp .env.example .env
```

Edite o arquivo e configure, no mínimo:

- `DATABASE_PASSWORD`: senha do usuário do PostgreSQL.
- `JWT_SECRET_KEY`: chave aleatória de pelo menos 32 caracteres.

Substitua os valores de exemplo antes de iniciar os serviços.

O Compose usa essas variáveis para configurar o PostgreSQL. Dentro do contêiner da API, `DATABASE_HOST` e `DATABASE_PORT` são configurados para acessar o banco pela rede interna do Compose.

Não é necessário alterar o endereço do banco local no arquivo `.env` para utilizar o Docker Compose.

### 2. Construir a imagem e iniciar os serviços

Na raiz do projeto, execute:

```bash
docker compose up -d --build
```

Se sua instalação exigir privilégios administrativos, use `sudo docker compose` no lugar de `docker compose`.

O Compose inicia o PostgreSQL e aguarda o banco ficar saudável antes de iniciar a API.

A aplicação executa `alembic upgrade head` antes de iniciar o Uvicorn. Assim, as migrações pendentes são aplicadas na inicialização do contêiner da API.

### 3. Verificar os serviços

Consulte o estado dos contêineres:

```bash
docker compose ps
```

Consulte os logs da aplicação:

```bash
docker compose logs --tail=80 api
```

Verifique a saúde da API:

```bash
curl -i http://127.0.0.1:8000/health
```

A resposta esperada é HTTP `200 OK`, com o seguinte conteúdo:

```json
{
  "status": "ok"
}
```

Para consultar a revisão do banco aplicada no contêiner:

```bash
docker compose exec api python -m alembic current
```

### 4. Acessar a API

A API fica disponível localmente em:

http://127.0.0.1:8000

Documentação interativa:

http://127.0.0.1:8000/docs

Especificação OpenAPI:

http://127.0.0.1:8000/openapi.json

A porta é publicada no endereço `127.0.0.1`, evitando a exposição direta da API a outras máquinas da rede.

### 5. Consultar logs em tempo real

Para acompanhar os logs da API:

```bash
docker compose logs -f api
```

Pressione `Ctrl+C` para encerrar o acompanhamento dos logs. Isso não encerra os contêineres.

### 6. Encerrar os serviços

Para parar e remover os contêineres e a rede criada pelo Compose:

```bash
docker compose down
```

O volume `postgres_data` é preservado, mantendo os dados do PostgreSQL para a próxima inicialização.

**Atenção:** o comando abaixo remove também os volumes do projeto, incluindo os dados persistidos do PostgreSQL:

```bash
docker compose down -v
```

Não execute esse comando quando precisar preservar os dados do banco.

## Configuração do PostgreSQL local

Esta seção é necessária apenas para executar a aplicação sem Docker.

O projeto utiliza, por padrão, o banco `helpdesk_db` e o usuário `helpdesk_app`.

No Linux, caso o usuário e o banco ainda não existam, abra o terminal administrativo do PostgreSQL:

```bash
sudo -u postgres psql
```

Dentro do terminal interativo do PostgreSQL, execute:

```sql
CREATE USER helpdesk_app WITH PASSWORD 'SUA_SENHA';
CREATE DATABASE helpdesk_db OWNER helpdesk_app;
\q
```

Substitua `SUA_SENHA` por uma senha escolhida por você.

Configure a mesma senha em `DATABASE_PASSWORD`, no arquivo `.env`.

Se o usuário e o banco já existirem, não execute novamente os comandos de criação.

## Migrações do banco de dados

O projeto utiliza Alembic para versionar as alterações da estrutura do banco.

### Execução local

Depois de configurar o PostgreSQL local e as variáveis de ambiente, aplique as migrações:

```bash
python -m alembic upgrade head
```

Para consultar a revisão aplicada:

```bash
python -m alembic current
```

### Execução com Docker

As migrações pendentes são aplicadas automaticamente quando a API inicia. Para consultar a revisão dentro do contêiner:

```bash
docker compose exec api python -m alembic current
```

As migrações ficam no diretório `migrations/versions/`.

## Executar a API localmente

Com o ambiente virtual ativado e o banco de dados local configurado, inicie o servidor:

```bash
python -m uvicorn app.main:app --reload
```

A API estará disponível em:

http://127.0.0.1:8000

### Documentação interativa

O FastAPI disponibiliza a documentação interativa dos endpoints em:

http://127.0.0.1:8000/docs

A documentação permite consultar as rotas, visualizar os schemas, enviar requisições e testar os endpoints autenticados.

Para encerrar o servidor, pressione `Ctrl+C` no terminal em que ele está rodando.

## Endpoints

Todas as rotas de autenticação e gerenciamento de chamados devem ser utilizadas de acordo com os requisitos de autenticação e autorização definidos pela aplicação.

### Autenticação

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/auth/register` | Cadastra um usuário |
| `POST` | `/auth/login` | Autentica um usuário |
| `GET` | `/auth/me` | Consulta o usuário autenticado |

### Chamados

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/tickets` | Lista os chamados acessíveis ao usuário |
| `POST` | `/tickets` | Cria um chamado |
| `GET` | `/tickets/{ticket_id}` | Consulta um chamado específico |
| `PATCH` | `/tickets/{ticket_id}` | Atualiza os campos permitidos de um chamado |
| `GET` | `/tickets/{ticket_id}/history` | Consulta o histórico de alterações |

### Comentários

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/tickets/{ticket_id}/comments` | Lista os comentários de um chamado |
| `POST` | `/tickets/{ticket_id}/comments` | Adiciona um comentário a um chamado |

### Filtros e paginação

O endpoint `GET /tickets` aceita os seguintes parâmetros:

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `skip` | Inteiro | `0` | Quantidade de registros ignorados |
| `limit` | Inteiro | `20` | Quantidade máxima de registros retornados, entre 1 e 100 |
| `status` | Texto | Sem filtro | Filtra pelo status do chamado |
| `priority` | Texto | Sem filtro | Filtra pela prioridade do chamado |

Os status aceitos são:

- `open`
- `in_progress`
- `waiting`
- `resolved`
- `closed`

As prioridades aceitas são:

- `low`
- `medium`
- `high`
- `urgent`

Exemplo de consulta com filtros e paginação:

```http
GET /tickets?status=in_progress&priority=high&skip=0&limit=10
```

A listagem é ordenada dos chamados mais recentes para os mais antigos. O acesso aos resultados respeita as restrições aplicáveis ao usuário autenticado.

## Comentários nos chamados

Os comentários permitem registrar informações adicionais sobre o atendimento sem alterar diretamente os campos do chamado.

Para criar um comentário, envie uma requisição autenticada:

```http
POST /tickets/1/comments
Content-Type: application/json
```

Corpo da requisição:

```json
{
  "content": "O problema continua ocorrendo após reiniciar o sistema."
}
```

O campo `content` deve conter entre 1 e 5.000 caracteres após a remoção dos espaços externos. Conteúdo vazio e campos adicionais não são aceitos.

Para consultar os comentários de um chamado:

```http
GET /tickets/1/comments
```

Os comentários são retornados em ordem cronológica.

Solicitantes podem consultar e comentar nos próprios chamados. Agentes e administradores podem atuar nos chamados conforme as regras de acesso implementadas pela API.

## Histórico de alterações

O endpoint de histórico permite consultar as alterações registradas durante o atendimento.

Exemplo:

```http
GET /tickets/1/history
```

Cada registro de histórico contém informações como:

- Identificador do registro.
- Identificador do chamado.
- Identificador do usuário responsável pela alteração, quando disponível.
- Nome do campo alterado.
- Valor anterior.
- Novo valor.
- Data e hora do registro.

O histórico permite acompanhar as mudanças realizadas nos chamados e identificar a evolução do atendimento.

## Autenticação

A API utiliza tokens JWT para autenticar as requisições protegidas.

Após obter um token válido pelos endpoints de autenticação, envie-o no cabeçalho `Authorization` das requisições:

```http
Authorization: Bearer SEU_TOKEN
```

O token deve permanecer privado e não deve ser compartilhado ou enviado ao repositório.

## Testes automatizados

Os testes utilizam Pytest e o cliente de testes do FastAPI.

Para executar toda a suíte de testes:

```bash
python -m pytest
```

A suíte verifica, entre outros aspectos:

- Autenticação e segurança.
- Funcionamento dos endpoints.
- Validação dos dados de entrada.
- Criação e atualização de chamados.
- Filtros e paginação.
- Validação das transições de status.
- Registro do histórico de alterações.
- Criação e consulta de comentários.
- Restrições de acesso a chamados de outros solicitantes.
- Restrições e relacionamentos dos modelos.

## Qualidade do código

Para verificar o código com Ruff:

```bash
python -m ruff check .
```

Para formatar os arquivos Python:

```bash
python -m ruff format .
```

Execute as verificações antes de publicar novas alterações.

## Integração contínua

O projeto utiliza GitHub Actions para executar automaticamente as verificações configuradas no repositório quando há atualizações e pull requests para a branch principal.

O status das verificações pode ser consultado na seção de ações do repositório:

https://github.com/AllanNattan/helpdesk-api/actions

## Estrutura do projeto

```text
helpdesk-api/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── dependencies.py
│   │   └── tickets.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   ├── ticket.py
│   │   ├── ticket_comment.py
│   │   ├── ticket_history.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── ticket.py
│   │   ├── ticket_comment.py
│   │   └── ticket_history.py
│   └── main.py
├── migrations/
│   ├── env.py
│   └── versions/
├── scripts/
├── tests/
├── .dockerignore
├── .env.example
├── alembic.ini
├── compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Status do projeto

Projeto em desenvolvimento, com autenticação, controle de acesso, gerenciamento de chamados, filtros, paginação, histórico de alterações, comentários, migrações de banco de dados, testes automatizados, Docker e integração contínua.