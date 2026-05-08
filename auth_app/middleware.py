from rest_framework.exceptions import AuthenticationFailed
from auth_app.jwt_utils import verify_access_token
from auth_app.services import AuthService


class JWTAuthenticationMiddleware:
    """
    Middleware для аутентификации через JWT токен в cookies.
    Добавляет объект пользователя в request если токен валиден.
    Также проверяет наличие JTI токена в Redis для возможности отзыва.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Пытаемся получить пользователя из токена
        access_token = request.COOKIES.get('access_token')
        
        if access_token:
            payload = verify_access_token(access_token)
            
            if payload:
                user_id = payload.get('user_id')
                jti = payload.get('jti')
                
                # Проверяем наличие JTI в Redis (не отозван ли токен)
                if jti and user_id:
                    is_token_valid = AuthService.verify_access_token_in_cache(user_id=user_id, jti=jti)
                    if not is_token_valid:
                        # Токен отозван или не найден в Redis
                        request.user = None
                        request.authenticated = False
                        response = self.get_response(request)
                        return response
                
                user = AuthService.get_user_by_id(user_id)
                
                if user:
                    request.user = user
                    request.authenticated = True
                else:
                    request.user = None
                    request.authenticated = False
            else:
                request.user = None
                request.authenticated = False
        else:
            request.user = None
            request.authenticated = False
        
        response = self.get_response(request)
        return response
