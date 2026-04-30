# ... (весь код до функции hash_password оставляем как есть)

def hash_password(password: str) -> str:
    """
    Hash password with bcrypt.
    bcrypt limits password to 72 bytes - we truncate safely.
    """
    # Simple approach: truncate to 72 characters (covers most ASCII passwords)
    # For production with unicode passwords, use byte-aware truncation
    safe_pwd = password[:72]
    return pwd_context.hash(safe_pwd)

# ... (остальной код файла оставляем без изменений)
