from rest_framework import serializers
from django.core.validators import EmailValidator, MinLengthValidator
import re



class RegisterSerializer(serializers.Serializer):
    """DTO для регистрации пользователя."""
    email = serializers.EmailField(
        required=True, 
        validators=[EmailValidator()],
        help_text="Электронная почта пользователя"
    )
    password = serializers.CharField(
        required=True,
        min_length=8,
        validators=[MinLengthValidator(8)],
        write_only=True,
        help_text="Пароль (минимум 8 символов, должен содержать буквы и цифры)"
    )
    first_name = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True,
        help_text="Имя пользователя"
    )
    last_name = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True,
        help_text="Фамилия пользователя"
    )

    def validate_password(self, value):
        """Валидация сложности пароля."""
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать минимум 8 символов.")
        
        # Проверка наличия букв и цифр
        has_letter = bool(re.search(r'[A-Za-zА-Яа-я]', value))
        has_digit = bool(re.search(r'\d', value))
        
        if not has_letter or not has_digit:
            raise serializers.ValidationError("Пароль должен содержать буквы и цифры.")
        
        return value



class LoginSerializer(serializers.Serializer):
    """DTO для входа пользователя."""
    email = serializers.EmailField(
        required=True, 
        validators=[EmailValidator()],
        help_text="Электронная почта пользователя"
    )
    password = serializers.CharField(
        required=True, 
        write_only=True,
        help_text="Пароль пользователя"
    )


class RefreshTokenSerializer(serializers.Serializer):
    """DTO для обновления токенов (используется только для валидации cookies)."""
    pass



class UserResponseSerializer(serializers.Serializer):
    """DTO для ответа с данными пользователя (без чувствительных данных)."""
    id = serializers.UUIDField(help_text="Уникальный идентификатор пользователя")
    email = serializers.EmailField(allow_null=True, help_text="Электронная почта")
    phone = serializers.CharField(allow_null=True, help_text="Номер телефона")
    first_name = serializers.CharField(help_text="Имя")
    last_name = serializers.CharField(help_text="Фамилия")
    avatar_url = serializers.URLField(help_text="URL аватара")
    created_at = serializers.DateTimeField(help_text="Дата создания аккаунта")


class ForgotPasswordSerializer(serializers.Serializer):
    """DTO для запроса сброса пароля."""
    email = serializers.EmailField(
        required=True, 
        validators=[EmailValidator()],
        help_text="Электронная почта для сброса пароля"
    )



class ResetPasswordSerializer(serializers.Serializer):
    """DTO для установки нового пароля."""
    token = serializers.CharField(
        required=True, 
        write_only=True,
        help_text="Токен сброса пароля"
    )
    password = serializers.CharField(
        required=True,
        min_length=8,
        validators=[MinLengthValidator(8)],
        write_only=True,
        help_text="Новый пароль (минимум 8 символов, должен содержать буквы и цифры)"
    )

    def validate_password(self, value):
        """Валидация сложности пароля."""
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать минимум 8 символов.")
        
        has_letter = bool(re.search(r'[A-Za-zА-Яа-я]', value))
        has_digit = bool(re.search(r'\d', value))
        
        if not has_letter or not has_digit:
            raise serializers.ValidationError("Пароль должен содержать буквы и цифры.")
        
        return value
