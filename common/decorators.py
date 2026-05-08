from functools import wraps
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied


def require_auth(view_func):
    """
    Декоратор для проверки аутентификации пользователя.
    Требует наличия валидного JWT токена в cookies.
    
    Usage:
        @require_auth
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'authenticated') or not request.authenticated:
            raise AuthenticationFailed('Требуется авторизация')
        if not hasattr(request, 'user') or not request.user:
            raise AuthenticationFailed('Пользователь не найден')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_owner_or_403(model_class, lookup_field='id', lookup_url_kwarg=None):
    """
    Декоратор для проверки владения ресурсом.
    Проверяет, что текущий пользователь является владельцем объекта.
    
    Args:
        model_class: Модель Django для поиска объекта
        lookup_field: Поле модели для поиска (по умолчанию 'id')
        lookup_url_kwarg: Имя параметра URL (по умолчанию совпадает с lookup_field)
    
    Usage:
        @require_auth
        @require_owner_or_403(Character, lookup_field='id')
        def update_character(request, id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'authenticated') or not request.authenticated:
                raise AuthenticationFailed('Требуется авторизация')
            if not hasattr(request, 'user') or not request.user:
                raise AuthenticationFailed('Пользователь не найден')
            
            # Получаем ID объекта из URL
            obj_id = kwargs.get(lookup_url_kwarg or lookup_field)
            
            if obj_id:
                try:
                    obj = model_class.objects.get(**{lookup_field: obj_id})
                    # Проверяем владение (предполагается, что у модели есть поле owner/user)
                    if hasattr(obj, 'owner') and obj.owner != request.user:
                        raise PermissionDenied('Нет прав для выполнения этой операции')
                    if hasattr(obj, 'user') and obj.user != request.user:
                        raise PermissionDenied('Нет прав для выполнения этой операции')
                except model_class.DoesNotExist:
                    pass  # Обработается как 404
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
