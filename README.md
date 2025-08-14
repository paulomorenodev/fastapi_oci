# FastAPI com PostgreSQL no Render

API desenvolvida com FastAPI para gerenciar usuários com armazenamento em PostgreSQL hospedado no Render.

## ✨ Funcionalidades

- 🔗 **Webhook** para receber dados de novos usuários
- ✅ **Validação robusta** de dados com Pydantic
- 🗄️ **PostgreSQL** com suporte a JSONB no Render
- 📧 **Prevenção de emails duplicados**
- 📄 **Paginação** em listagens
- 🔍 **Filtros** por status
- 🗑️ **Soft delete** (marcação como deletado)
- 🏥 **Health check** para monitoramento
- 📚 **CRUD completo** (Create, Read, Update, Delete)

## 🛠️ Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **PostgreSQL** - Banco de dados relacional
- **Render** - Plataforma de hospedagem
- **Pydantic** - Validação de dados
- **SQLAlchemy** - ORM para Python

## 🚀 Como executar

### 1. Instale as dependências:
```bash
pip install fastapi uvicorn[standard] pydantic[email] psycopg2-binary sqlalchemy python-dotenv
```

### 2. Configure as variáveis de ambiente:
Crie um arquivo `.env` na raiz do projeto:
```bash
# Configuração do PostgreSQL - Render
DATABASE_URL=postgresql://usuario:senha@host:5432/database

# OU configure separadamente:
POSTGRES_HOST=dpg-abc123-a.oregon-postgres.render.com
POSTGRES_PORT=5432
POSTGRES_DB=fastapi_db
POSTGRES_USER=fastapi_user
POSTGRES_PASSWORD=sua_senha_aqui

# Configurações da API
DEBUG=True
API_PORT=8000
API_HOST=0.0.0.0
```

### 3. Execute a aplicação:
```bash
uvicorn api_render:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Acesse a documentação:
- 📖 **Documentação interativa**: http://localhost:8000/docs
- 📋 **Documentação alternativa**: http://localhost:8000/redoc

## 🔗 Endpoints da API

### Informações gerais
- `GET /` - Informações da API e lista de endpoints
- `GET /health` - Status da aplicação e conexão com banco

### Gestão de usuários
- `POST /new-user` - Criar novo usuário via webhook
- `GET /users` - Listar usuários com paginação e filtros
- `GET /users/{user_id}` - Buscar usuário específico por ID
- `PUT /users/{user_id}` - Atualizar dados do usuário
- `DELETE /users/{user_id}` - Marcar usuário como deletado (soft delete)

### Parâmetros de consulta
```bash
# Listar usuários com paginação
GET /users?limit=10&offset=0

# Filtrar por status
GET /users?status_filter=active

# Combinar filtros
GET /users?limit=5&offset=10&status_filter=deleted
```

## 📊 Estrutura do Banco de Dados

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    user_data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 🎯 Exemplos de Uso

### Criar um novo usuário:
```bash
curl -X POST "http://localhost:8000/new-user" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "joao_silva",
    "email": "joao@email.com"
  }'
```

### Listar usuários:
```bash
curl "http://localhost:8000/users?limit=5&offset=0"
```

### Buscar usuário específico:
```bash
curl "http://localhost:8000/users/1"
```

### Atualizar usuário:
```bash
curl -X PUT "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "joao_santos",
    "status": "inactive"
  }'
```

### Verificar saúde da API:
```bash
curl "http://localhost:8000/health"
```

## 🏗️ Configuração do Render

### 1. Criar banco PostgreSQL:
1. Acesse [render.com](https://render.com)
2. Clique em **"New +"** > **"PostgreSQL"**
3. Configure:
   - **Name**: `fastapi-webhook-db`
   - **Database**: `fastapi_db`
   - **User**: `fastapi_user`
   - **Region**: `Oregon (US West)`
   - **Plan**: **Free**

### 2. Obter credenciais:
- Acesse o dashboard do banco criado
- Copie a **External Database URL**
- Use no arquivo `.env`

## 🔒 Recursos de Segurança

- ✅ Validação de entrada com Pydantic
- ✅ Prevenção de SQL injection com SQLAlchemy
- ✅ Conexões SSL automáticas (Render)
- ✅ Tratamento de erros padronizado
- ✅ Soft delete para preservar dados

## 📈 Monitoramento

### Health Check
O endpoint `/health` retorna:
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "version": "PostgreSQL 15.x",
    "provider": "Render PostgreSQL"
  },
  "timestamp": "2025-08-14T15:30:00Z"
}
```

## 🧪 Testes

Para testar a conexão com o banco:
```bash
python test_render.py
```

## 📝 Estrutura do Projeto

```
fastapi_oci/
├── api_render.py          # Aplicação principal
├── test_render.py         # Teste de conexão
├── .env                   # Variáveis de ambiente
├── .gitignore            # Arquivos ignorados pelo Git
├── README.md             # Este arquivo
└── requirements.txt      # Dependências (opcional)
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

Se você encontrar algum problema ou tiver dúvidas:

1. Verifique a [documentação](http://localhost:8000/docs)
2. Teste a conexão com `python test_render.py`
3. Verifique os logs da aplicação
4. Consulte a [documentação do Render](https://render.com/docs)

---

**Desenvolvido com ❤️ usando FastAPI e PostgreSQL**