# FastAPI Webhook com SQLite

API webhook desenvolvida com FastAPI para receber e armazenar dados de usuários em um banco SQLite.

## Funcionalidades

- Endpoint webhook para receber dados de novos usuários
- Validação de dados com Pydantic
- Armazenamento em banco SQLite
- Prevenção de emails duplicados

## Como executar

1. Instale as dependências:
```bash
pip install fastapi uvicorn[standard] pydantic[email]
```

2. Execute a aplicação:
```bash
uvicorn main:app --reload
```

3. Acesse a documentação em: http://localhost:8000/docs

## Endpoints

- `GET /` - Mensagem de boas-vindas
- `POST /webhook/new-user` - Recebe dados de novos usuários