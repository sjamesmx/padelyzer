from passlib.context import CryptContext
import sys

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

if len(sys.argv) != 2:
    print("Uso: python crear_hash.py <contraseña>")
    sys.exit(1)

plain_password = sys.argv[1]
new_hash = pwd_context.hash(plain_password)
print(f"Hash generado para '{plain_password}':\n{new_hash}") 