from rest_framework.exceptions import AuthenticationFailed
from auth.jwt_utils import verify_access_token
from auth.services import AuthService


class JWTAuthenticationMiddleware:
    """
    Middleware для аутентификации через JWT токен в cookies.
    Добавляет объект пользователя в request если токен валиден.
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
