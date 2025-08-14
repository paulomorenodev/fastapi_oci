import os
import psycopg2
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel, EmailStr
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import create_engine, text
from datetime import datetime
import json

# Carregar variáveis de ambiente
load_dotenv()

# --- Configurações do Banco PostgreSQL ---

def get_database_url():
    """
    Constrói a URL do banco de dados a partir das variáveis de ambiente.
    """
    # Tentar usar DATABASE_URL primeiro (mais simples)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Senão, construir a partir das variáveis individuais
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    
    if not all([host, database, user, password]):
        raise ValueError("Configurações de banco de dados incompletas!")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def get_database_engine():
    """
    Cria a engine de conexão com o PostgreSQL do Render.
    """
    database_url = get_database_url()
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verificar conexões antes de usar
        pool_recycle=300,    # Reciclar conexões a cada 5 minutos
    )
    return engine

def create_db_and_tables():
    """
    Cria a tabela de usuários se não existir.
    """
    engine = get_database_engine()
    
    try:
        with engine.connect() as connection:
            # Criar tabela de usuários com suporte a JSON
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    user_data JSONB DEFAULT '{}',
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
            
            connection.execute(text(create_table_sql))
            
            # Criar índices para performance
            indices_sql = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
                "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_data_gin ON users USING GIN(user_data)"
            ]
            
            for index_sql in indices_sql:
                connection.execute(text(index_sql))
            
            connection.commit()
            print("✅ Tabela 'users' e índices criados/verificados com sucesso!")
                
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    """
    print("🚀 Iniciando a aplicação e configurando o PostgreSQL (Render)...")
    try:
        create_db_and_tables()
        print("✅ Banco de dados configurado com sucesso!")
    except Exception as e:
        print(f"❌ Erro na configuração do banco: {e}")
        raise
    
    yield
    print("🛑 Finalizando a aplicação.")

# --- Modelos de Dados com Pydantic ---

class UserWebhook(BaseModel):
    """
    Modelo para validação dos dados recebidos no webhook.
    """
    username: str
    email: EmailStr

class UserUpdate(BaseModel):
    """
    Modelo para atualização de dados do usuário.
    """
    username: str = None
    email: EmailStr = None
    status: str = None

# --- Configuração da Aplicação FastAPI ---

app = FastAPI(
    title="Api com Render PostgreSQL",
    description="API para cadastrar usuarios e armazenar dados no PostgreSQL (Render)",
    version="1.0.0",
    lifespan=lifespan
)

# --- Endpoints da API ---

@app.get("/")
def read_root():
    return {
        "message": "API Paulo Moreno PostgreSQL (Render)",
           }

@app.post("/new-user", status_code=status.HTTP_201_CREATED)
def receive_user_webhook(user_data: UserWebhook):
    """
    Cadastrar um novo usuário e salvar no PostgreSQL.
    """
    engine = get_database_engine()
    
    try:
        with engine.connect() as connection:
            # Preparar dados JSON adicionais
            additional_data = {
                "created_via": "webhook",
                "source": "api",
                "timestamp": datetime.now().isoformat(),
                "ip_address": "unknown"  # Você pode capturar o IP real se necessário
            }
            
            # Inserir dados do usuário
            insert_sql = """
                INSERT INTO users (username, email, user_data) 
                VALUES (:username, :email, :user_data)
                RETURNING id, created_at
            """
            
            result = connection.execute(
                text(insert_sql),
                {
                    "username": user_data.username,
                    "email": user_data.email,
                    "user_data": json.dumps(additional_data)
                }
            )
            
            row = result.fetchone()
            user_id = row[0]
            created_at = row[1]
            
            connection.commit()
            
    except sqlalchemy.exc.IntegrityError as e:
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"O e-mail '{user_data.email}' já está cadastrado."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro de integridade: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )

    return {
        "message": "Usuário recebido e salvo com sucesso no Render!",
        "user_id": user_id,
        "created_at": created_at.isoformat() if created_at else None,
        "data_saved": {
            "username": user_data.username,
            "email": user_data.email
        }
    }

# ...existing code...

@app.get("/users")
def list_users(limit: int = 10, offset: int = 0, status_filter: str = None):
    """
    Endpoint para listar usuários com paginação e filtros.
    """
    engine = get_database_engine()
    
    try:
        with engine.connect() as connection:
            # Construir query com filtros opcionais
            where_clause = ""
            params = {"limit": limit, "offset": offset}
            
            if status_filter:
                where_clause = "WHERE status = :status_filter"
                params["status_filter"] = status_filter
            
            # Query com paginação
            query_sql = f"""
                SELECT 
                    id, username, email, user_data, status,
                    created_at, updated_at
                FROM users
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            result = connection.execute(text(query_sql), params)
            
            users = []
            for row in result:
                # Correção: verificar se user_data já é dict ou precisa ser convertido
                user_data = row[3] if isinstance(row[3], dict) else (json.loads(row[3]) if row[3] else {})
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "additional_data": user_data,
                    "status": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "updated_at": row[6].isoformat() if row[6] else None
                })
            
            # Contar total de usuários
            count_sql = f"SELECT COUNT(*) FROM users {where_clause}"
            count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
            count_result = connection.execute(text(count_sql), count_params)
            total = count_result.fetchone()[0]
            
            return {
                "users": users,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total,
                    "pages": (total + limit - 1) // limit  # Calcular total de páginas
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar usuários: {str(e)}"
        )

@app.get("/users/{user_id}")
def get_user_by_id(user_id: int):
    """
    Buscar usuário específico por ID.
    """
    engine = get_database_engine()
    
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT 
                        id, username, email, user_data, status,
                        created_at, updated_at
                    FROM users 
                    WHERE id = :user_id
                """),
                {"user_id": user_id}
            )
            
            row = result.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuário com ID {user_id} não encontrado."
                )
            
            # Correção: verificar se user_data já é dict ou precisa ser convertido
            user_data = row[3] if isinstance(row[3], dict) else (json.loads(row[3]) if row[3] else {})
            # return {
            #     "id": row[0],
            #     "username": row[1],
            #     "email": row[2],
            #     "additional_data": user_data,
            #     "status": row[4],
            #     "created_at": row[5].isoformat() if row[5] else None,
            #     "updated_at": row[6].isoformat() if row[6] else None
            # }
            return {
                "id": row[0],
                "username": row[1]

            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar usuário: {str(e)}"
        )

# ...existing code...

@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserUpdate):
    """
    Atualizar dados do usuário.
    """
    engine = get_database_engine()
    
    try:
        with engine.connect() as connection:
            # Verificar se usuário existe
            check_sql = "SELECT COUNT(*) FROM users WHERE id = :user_id"
            result = connection.execute(text(check_sql), {"user_id": user_id})
            if result.fetchone()[0] == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuário com ID {user_id} não encontrado."
                )
            
            # Preparar campos para atualização
            update_fields = []
            params = {"user_id": user_id}
            
            if user_data.username is not None:
                update_fields.append("username = :username")
                params["username"] = user_data.username
            
            if user_data.email is not None:
                update_fields.append("email = :email")
                params["email"] = user_data.email
            
            if user_data.status is not None:
                update_fields.append("status = :status")
                params["status"] = user_data.status
            
            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nenhum campo fornecido para atualização."
                )
            
            # Adicionar timestamp de atualização
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            # Executar atualização
            update_sql = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = :user_id
                RETURNING id, username, email, status, updated_at
            """
            
            result = connection.execute(text(update_sql), params)
            row = result.fetchone()
            connection.commit()
            
            return {
                "message": f"Usuário ID {user_id} atualizado com sucesso!",
                "user": {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "status": row[3],
                    "updated_at": row[4].isoformat() if row[4] else None
                }
            }
            
    except HTTPException:
        raise
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já está em uso por outro usuário."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """
    Deletar usuário por ID (soft delete - marca como inativo).
    """
    engine = get_database_engine()
    
    try:
        with engine.connect() as connection:
            # Soft delete - apenas marcar como inativo
            update_sql = """
                UPDATE users 
                SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id AND status != 'deleted'
                RETURNING id, username, email
            """
            
            result = connection.execute(text(update_sql), {"user_id": user_id})
            row = result.fetchone()
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuário com ID {user_id} não encontrado ou já deletado."
                )
            
            connection.commit()
            
            return {
                "message": f"Usuário '{row[1]}' marcado como deletado!",
                "deleted_user": {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2]
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar usuário: {str(e)}"
        )

@app.get("/health")
def health_check():
    """
    Endpoint para verificar saúde da aplicação e conexão com DB.
    """
    try:
        engine = get_database_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1, version()"))
            row = result.fetchone()
            db_status = "connected"
            db_version = row[1] if row else "unknown"
    except Exception as e:
        db_status = f"error: {str(e)}"
        db_version = "unknown"
    
    return {
        "status": "healthy",
        "database": {
            "status": db_status,
            "version": db_version,
            "provider": "Render PostgreSQL"
        },
        "timestamp": datetime.now().isoformat()
    }