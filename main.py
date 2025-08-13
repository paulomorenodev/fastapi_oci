import sqlite3
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel, EmailStr
from contextlib import asynccontextmanager

DATABASE_URL = "users.db"

# --- Gerenciamento do Banco de Dados ---

def create_db_and_tables():
    """
    Cria o arquivo do banco de dados e a tabela de usuários se não existirem.
    """
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    # A cláusula "UNIQUE" impede que o mesmo email seja cadastrado duas vezes.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    É executado na inicialização e finalização da API.
    """
    # Código a ser executado antes da aplicação iniciar
    print("Iniciando a aplicação e configurando o banco de dados...")
    create_db_and_tables()
    yield
    # Código a ser executado após a aplicação finalizar (não usado aqui, mas o local é este)
    print("Finalizando a aplicação.")


# --- Modelos de Dados com Pydantic ---

class UserWebhook(BaseModel):
    """
    Modelo para validação dos dados recebidos no webhook.
    EmailStr garante que o campo 'email' tenha um formato de e-mail válido.
    """
    username: str
    email: EmailStr


# --- Configuração da Aplicação FastAPI ---

app = FastAPI(lifespan=lifespan)


# --- Endpoints da API ---

@app.get("/")
def read_root():
    return {"message": "API de Webhook com SQLite"}

@app.post("/webhook/new-user", status_code=status.HTTP_201_CREATED)
def receive_user_webhook(user_data: UserWebhook):
    """
    Webhook para receber dados de um novo usuário e salvar no banco de dados.
    """
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Insere os dados do usuário na tabela
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (user_data.username, user_data.email)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Este erro ocorre se a constraint "UNIQUE" para o email for violada
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O e-mail '{user_data.email}' já está cadastrado."
        )
    
    # Pega o ID do usuário recém-criado
    user_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Usuário recebido e salvo com sucesso!",
        "user_id": user_id,
        "data_saved": user_data
    }