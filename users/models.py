import uuid
from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    """Менеджер для получения только активных (не удаленных) пользователей."""
    
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class User(models.Model):
    """
    Модель пользователя для хранения учетных данных.
    Поддерживает как локальную аутентификацию (email/пароль),
    так и OAuth (Yandex, VK).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Контактные данные
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    # Хеш пароля и соль (для локальной аутентификации)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    salt = models.CharField(max_length=255, null=True, blank=True)
    
    # OAuth идентификаторы
    yandex_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    vk_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    # Дополнительная информация
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Менеджеры
    objects = models.Manager()  # стандартный менеджер (включая удалённые)
    active = ActiveManager()    # менеджер для активных записей
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deleted_at']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]
    
    def __str__(self):
        if self.email:
            return f"User {self.email}"
        elif self.phone:
            return f"User {self.phone}"
        return f"User {self.id}"
    
    def soft_delete(self):
        """Мягкое удаление пользователя."""
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Восстановление пользователя после мягкого удаления."""
        self.deleted_at = None
        self.save()


class RefreshToken(models.Model):
    """
    Модель для хранения Refresh токенов.
    Токены хранятся в хешированном виде для безопасности.
    Позволяет управлять сессиями и отзывать доступ.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Связь с пользователем
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='refresh_tokens')
    
    # Хеш токена (не храним токен в открытом виде)
    token_hash = models.CharField(max_length=255, db_index=True)
    
    # Срок действия
    expires_at = models.DateTimeField()
    
    # Флаг отзыва токена
    revoked = models.BooleanField(default=False)
    
    # Дополнительная информация
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'refresh_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['revoked']),
        ]
    
    def __str__(self):
        return f"RefreshToken for {self.user} (expires: {self.expires_at})"
    
    def is_valid(self):
        """Проверка действительности токена."""
        if self.revoked:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    def revoke(self):
        """Отзыв токена."""
        self.revoked = True
        self.save()


class AccessToken(models.Model):
    """
    Модель для хранения Access токенов.
    Токены хранятся в хешированном виде для безопасности.
    Позволяет управлять сессиями и отзывать доступ.
    Access токены имеют короткое время жизни (15 минут).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Связь с пользователем
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='access_tokens')
    
    # Хеш токена (не храним токен в открытом виде)
    token_hash = models.CharField(max_length=255, db_index=True)
    
    # Срок действия
    expires_at = models.DateTimeField()
    
    # Флаг отзыва токена
    revoked = models.BooleanField(default=False)
    
    # Дополнительная информация
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'access_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['revoked']),
        ]
    
    def __str__(self):
        return f"AccessToken for {self.user} (expires: {self.expires_at})"
    
    def is_valid(self):
        """Проверка действительности токена."""
        if self.revoked:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    def revoke(self):
        """Отзыв токена."""
        self.revoked = True
        self.save()
