import bcrypt

MAX_BCRYPT_BYTES = 72

def hash_password(password: str) -> str:
    pw = password.encode("utf-8")
    if len(pw) > MAX_BCRYPT_BYTES:
        raise ValueError("Password too long for bcrypt (max 72 bytes).")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw, salt).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    pw = password.encode("utf-8")
    if len(pw) > MAX_BCRYPT_BYTES:
        return False
    return bcrypt.checkpw(pw, password_hash.encode("utf-8"))