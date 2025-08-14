from dotenv import load_dotenv
import os

load_dotenv()

print("=== Testando variáveis de ambiente ===")
print(f"ORACLE_USER: {os.getenv('ORACLE_USER')}")
print(f"ORACLE_PASSWORD: {'*' * len(os.getenv('ORACLE_PASSWORD', '')) if os.getenv('ORACLE_PASSWORD') else 'NÃO DEFINIDA'}")
print(f"ORACLE_DSN: {os.getenv('ORACLE_DSN')}")
print(f"WALLET_LOCATION: {os.getenv('WALLET_LOCATION')}")