import bcrypt


def hash_password(password: str) -> tuple[str, str]:
    """
    Хеширование пароля с использованием уникальной соли.
    
    Args:
        password: Пароль в открытом виде.
        
    Returns:
        Кортеж (хеш_пароля, соль).
    """
    # Генерируем случайную соль
    salt = bcrypt.gensalt(rounds=12)
    # Хэшируем пароль с солью
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8'), salt.decode('utf-8')


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Проверка пароля путем сравнения хешей.
    
    Args:
        password: Пароль в открытом виде для проверки.
        password_hash: Сохраненный хеш пароля.
        salt: Соль, использованная при хешировании.
        
    Returns:
        True если пароль верный, False иначе.
    """
    password_bytes = password.encode('utf-8')
    stored_hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, stored_hash_bytes)


def hash_token(token: str) -> str:
    """
    Хеширование токена для безопасного хранения в БД.
    Используется bcrypt с自动生成ной солью.
    
    Args:
        token: Токен в открытом виде.
        
    Returns:
        Хеш токена.
    """
    token_bytes = token.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(token_bytes, salt)
    return hashed.decode('utf-8')


def verify_token(token: str, token_hash: str) -> bool:
    """
    Проверка токена путем сравнения хешей.
    
    Args:
        token: Токен в открытом виде для проверки.
        token_hash: Сохраненный хеш токена.
        
    Returns:
        True если токен верный, False иначе.
    """
    token_bytes = token.encode('utf-8')
    stored_hash_bytes = token_hash.encode('utf-8')
    return bcrypt.checkpw(token_bytes, stored_hash_bytes)
