from cryptography.fernet import Fernet
from config.settings import settings


def get_fernet() -> Fernet:
    return Fernet(settings.token_encryption_key.encode())


def encrypt_token(plain_token: str) -> str:
    '''
    Call this BEFORE saving token to MySQL.
    plain_token  = raw GitHub access token
    returns      = encrypted string safe to store in DB
    '''
    f = get_fernet()
    encrypted = f.encrypt(plain_token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    '''
    Call this BEFORE using token to call GitHub API.
    encrypted_token = value stored in MySQL
    returns         = original GitHub access token
    '''
    f = get_fernet()
    decrypted = f.decrypt(encrypted_token.encode())
    return decrypted.decode()
