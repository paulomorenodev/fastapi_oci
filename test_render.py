import os
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text

load_dotenv()

def test_render_connection():
    """Testar conexão com Render PostgreSQL"""
    
    print("=== Testando conexão com Render PostgreSQL ===")
    
    # Tentar DATABASE_URL primeiro
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print(f"DATABASE_URL: {database_url[:50]}...{database_url[-20:]}")
        
        try:
            # Teste com psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version(), current_database(), current_user;")
            result = cursor.fetchone()
            
            print(f"✅ Conexão bem-sucedida!")
            print(f"   Versão: {result[0][:50]}...")
            print(f"   Database: {result[1]}")
            print(f"   Usuário: {result[2]}")
            
            cursor.close()
            conn.close()
            
            # Teste com SQLAlchemy
            engine = create_engine(database_url)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 'Hello from Render!' as message"))
                message = result.fetchone()[0]
                print(f"✅ SQLAlchemy: {message}")
                
            return True
            
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            return False
    else:
        print("❌ DATABASE_URL não definida!")
        return False

if __name__ == "__main__":
    success = test_render_connection()
    if success:
        print("\n🎉 Tudo funcionando! Pode executar a aplicação.")
    else:
        print("\n❌ Verifique as configurações do .env")