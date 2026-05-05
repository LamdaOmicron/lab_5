from rest_framework import serializers
from django.core.validators import EmailValidator, MinLengthValidator
import re


class RegisterSerializer(serializers.Serializer):
    """DTO для регистрации пользователя."""
    email = serializers.EmailField(required=True, validators=[EmailValidator()])
    password = serializers.CharField(
        required=True,
        min_length=8,
        validators=[MinLengthValidator(8)],
        write_only=True
    )
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

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
    email = serializers.EmailField(required=True, validators=[EmailValidator()])
    password = serializers.CharField(required=True, write_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    """DTO для обновления токенов (используется только для валидации cookies)."""
    pass


class UserResponseSerializer(serializers.Serializer):
    """DTO для ответа с данными пользователя (без чувствительных данных)."""
    id = serializers.UUIDField()
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar_url = serializers.URLField()
    created_at = serializers.DateTimeField()


class ForgotPasswordSerializer(serializers.Serializer):
    """DTO для запроса сброса пароля."""
    email = serializers.EmailField(required=True, validators=[EmailValidator()])


class ResetPasswordSerializer(serializers.Serializer):
    """DTO для установки нового пароля."""
    token = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(
        required=True,
        min_length=8,
        validators=[MinLengthValidator(8)],
        write_only=True
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
