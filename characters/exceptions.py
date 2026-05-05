import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

logger = logging.getLogger(__name__)


class ConflictError(Exception):
    """Исключение для конфликта данных (например, попытка создать дубликат)."""
    pass


def custom_exception_handler(exc, context):
    """
    Глобальный обработчик исключений для API.
    Не возвращает технические детали ошибок клиенту.
    """
    # Сначала вызываем стандартный обработчик DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Логируем ошибку для разработчиков
        logger.error(f"API Exception: {exc}", exc_info=True)
        
        # Скрываем технические детали
        if isinstance(exc, AuthenticationFailed):
            return Response(
                {'error': 'Неавторизованный доступ'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif isinstance(exc, PermissionDenied):
            return Response(
                {'error': 'Доступ запрещен'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif response.status_code == 400:
            # Валидационные ошибки
            return Response(
                {'error': 'Ошибка валидации данных', 'details': response.data},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif response.status_code == 404:
            return Response(
                {'error': 'Ресурс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif response.status_code >= 500:
            # Скрываем детали внутренних ошибок сервера
            return Response(
                {'error': 'Внутренняя ошибка сервера'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return response

    # Обрабатываем кастомные исключения
    if isinstance(exc, ConflictError):
        logger.warning(f"Conflict Error: {exc}")
        return Response(
            {"error": str(exc)},
            status=status.HTTP_409_CONFLICT
        )

    if isinstance(exc, DjangoValidationError):
        logger.warning(f"Validation Error: {exc}")
        return Response(
            {"error": exc.messages[0] if exc.messages else "Ошибка валидации"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if isinstance(exc, IntegrityError):
        logger.warning(f"Integrity Error: {exc}")
        return Response(
            {"error": "Конфликт данных: запись уже существует"},
            status=status.HTTP_409_CONFLICT
        )

    # Логирование необработанных исключений
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return Response(
        {"error": "Внутренняя ошибка сервера"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )