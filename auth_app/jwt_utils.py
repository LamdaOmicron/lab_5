import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from django.conf import settings


def generate_access_token(user_id: str, email: Optional[str] = None) -> tuple[str, str]:
    """
    Генерация Access токена с коротким временем жизни (15 минут).
    
    Args:
        user_id: UUID пользователя.
        email: Email пользователя (опционально).
        
    Returns:
        Кортеж (jwt_token, jti) где jti - уникальный идентификатор токена.
    """
    # Генерируем уникальный JTI (JWT ID)
    jti = str(uuid.uuid4())
    
    expiration_time = datetime.now(timezone.utc) + timedelta(
        minutes=int(settings.JWT_ACCESS_EXPIRATION.replace('m', ''))
        if hasattr(settings, 'JWT_ACCESS_EXPIRATION') and 'm' in settings.JWT_ACCESS_EXPIRATION
        else 15
    )
    
    payload = {
        'user_id': user_id,
        'email': email,
        'type': 'access',
        'jti': jti,
        'exp': expiration_time,
        'iat': datetime.now(timezone.utc),
    }
    
    secret = getattr(settings, 'JWT_ACCESS_SECRET', 'default_access_secret')
    token = jwt.encode(payload, secret, algorithm='HS256')
    
    return token, jti


def generate_refresh_token(user_id: str, email: Optional[str] = None) -> str:
    """
    Генерация Refresh токена с длительным временем жизни (7 дней).
    
    Args:
        user_id: UUID пользователя.
        email: Email пользователя (опционально).
        
    Returns:
        JWT токен в виде строки.
    """
    expiration_time = datetime.now(timezone.utc) + timedelta(
        days=int(settings.JWT_REFRESH_EXPIRATION.replace('d', ''))
        if hasattr(settings, 'JWT_REFRESH_EXPIRATION') and 'd' in settings.JWT_REFRESH_EXPIRATION
        else 7
    )
    
    payload = {
        'user_id': user_id,
        'email': email,
        'type': 'refresh',
        'exp': expiration_time,
        'iat': datetime.now(timezone.utc),
    }
    
    secret = getattr(settings, 'JWT_REFRESH_SECRET', 'default_refresh_secret')
    return jwt.encode(payload, secret, algorithm='HS256')


def verify_access_token(token: str) -> Optional[dict]:
    """
    Проверка и декодирование Access токена.
    
    Args:
        token: JWT токен для проверки.
        
    Returns:
        Payload токена если токен валиден, None иначе.
    """
    try:
        secret = getattr(settings, 'JWT_ACCESS_SECRET', 'default_access_secret')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        # Проверяем что это access токен
        if payload.get('type') != 'access':
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Проверка и декодирование Refresh токена.
    
    Args:
        token: JWT токен для проверки.
        
    Returns:
        Payload токена если токен валиден, None иначе.
    """
    try:
        secret = getattr(settings, 'JWT_REFRESH_SECRET', 'default_refresh_secret')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        # Проверяем что это refresh токен
        if payload.get('type') != 'refresh':
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_expiration_datetime(expiration_str: str) -> datetime:
    """
    Преобразование строки времени жизни токена в datetime.
    
    Args:
        expiration_str: Строка вида '15m' или '7d'.
        
    Returns:
        Datetime объекта истечения срока.
    """
    now = datetime.now(timezone.utc)
    
    if 'm' in expiration_str:
        minutes = int(expiration_str.replace('m', ''))
        return now + timedelta(minutes=minutes)
    elif 'd' in expiration_str:
        days = int(expiration_str.replace('d', ''))
        return now + timedelta(days=days)
    else:
        # По умолчанию 15 минут
        return now + timedelta(minutes=15)


def get_access_token_ttl_seconds() -> int:
    """
    Получение времени жизни Access токена в секундах.
    
    Returns:
        Время жизни в секундах.
    """
    expiration_str = getattr(settings, 'JWT_ACCESS_EXPIRATION', '15m')
    if 'm' in expiration_str:
        minutes = int(expiration_str.replace('m', ''))
        return minutes * 60
    elif 'h' in expiration_str:
        hours = int(expiration_str.replace('h', ''))
        return hours * 3600
    else:
        return 900  # 15 минут по умолчанию
