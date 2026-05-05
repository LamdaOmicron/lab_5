# Create your models here.
import uuid
from django.db import models
from django.utils import timezone

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Character(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, db_index=True)
    type = models.CharField(max_length=50, default='character')  # тип персонажа (character, npc и т.д.)
    level = models.PositiveSmallIntegerField(default=1)
    class_name = models.CharField(max_length=50, blank=True)      # класс (например, "Oracle")
    ancestry = models.CharField(max_length=50, blank=True)        # ancestry (например, "Kitsune")
    heritage = models.CharField(max_length=100, blank=True)       # heritage (например, "Frozen Wind Kitsune")
    background = models.CharField(max_length=100, blank=True)     # background (например, "Undertaker")
    hp_max = models.PositiveSmallIntegerField(default=15)
    hp_current = models.PositiveSmallIntegerField(default=15)
    speed = models.PositiveSmallIntegerField(default=25)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = models.Manager()          # стандартный менеджер (включая удалённые)
    active = ActiveManager()            # менеджер для активных записей
    deleted_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'characters'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deleted_at']),  # для быстрого фильтра
            models.Index(fields=['name']),
        ]

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.deleted_at = None
        self.save()
