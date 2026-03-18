import secrets
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    import base64
    import os

def generate_fernet_key():
    if HAS_CRYPTO:
        return Fernet.generate_key().decode()
    else:
        # Fallback caso cryptography não esteja instalado
        return base64.urlsafe_b64encode(os.urandom(32)).decode()

def generate_secret_key():
    return secrets.token_hex(32)

if __name__ == "__main__":
    fernet = generate_fernet_key()
    secret = generate_secret_key()
    
    print("\n--- Copie estas chaves para o seu arquivo .env ---\n")
    print(f"AIRFLOW__CORE__FERNET_KEY={fernet}")
    print(f"AIRFLOW__WEBSERVER__SECRET_KEY={secret}")
    print("\n------------------------------------------------\n")
