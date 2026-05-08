from django.utils import timezone
import logging
from rest_framework.exceptions import PermissionDenied
from .models import Character
from .serializers import CharacterCreateUpdateSerializer
from .exceptions import ConflictError
from common.cache.cache_service import cache_service

logger = logging.getLogger(__name__)


class CharacterService:
    # Префиксы ключей кеша
    CACHE_PREFIX_LIST = 'items:list'
    CACHE_PREFIX_DETAIL = 'items:detail'
    
    @staticmethod
    def _get_list_cache_key(page: int, limit: int) -> str:
        """Генерация ключа кеша для списка персонажей."""
        return f"{CharacterService.CACHE_PREFIX_LIST}:page:{page}:limit:{limit}"
    
    @staticmethod
    def _get_detail_cache_key(character_id: str) -> str:
        """Генерация ключа кеша для конкретного персонажа."""
        return f"{CharacterService.CACHE_PREFIX_DETAIL}:{character_id}"
    
    @staticmethod
    def _invalidate_list_cache():
        """Инвалидация всех ключей кеша списков."""
        cache_service.delete_by_pattern(f"{CharacterService.CACHE_PREFIX_LIST}:*")
        logger.debug("Invalidated character list cache")
    
    @staticmethod
    def get_all_active(page=1, limit=10):
        # Формируем ключ кеша
        cache_key = CharacterService._get_list_cache_key(page, limit)
        
        # Проверяем кеш
        cached_data = cache_service.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache HIT for key: {cache_key}")
            return cached_data
        
        logger.debug(f"Cache MISS for key: {cache_key}")
        
        # Запрос к БД
        start = (page - 1) * limit
        end = start + limit
        queryset = Character.active.all()
        total = queryset.count()
        items = queryset[start:end]
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        
        result = {
            'data': list(items),
            'meta': {
                'total': total,
                'page': page,
                'limit': limit,
                'totalPages': total_pages,
            }
        }
        
        # Сохраняем в кеш
        cache_service.set(cache_key, result)
        
        return result

    @staticmethod
    def get_by_id(character_id):
        # Проверяем кеш
        cache_key = CharacterService._get_detail_cache_key(character_id)
        cached_data = cache_service.get(cache_key)
        
        if cached_data is not None:
            logger.debug(f"Cache HIT for detail key: {cache_key}")
            # Возвращаем объект модели из сериализованных данных
            try:
                return Character.objects.get(id=cached_data['id'])
            except (Character.DoesNotExist, KeyError):
                # Если объект не найден, удаляем из кеша и продолжаем
                cache_service.delete(cache_key)
        
        logger.debug(f"Cache MISS for detail key: {cache_key}")
        
        # Запрос к БД
        try:
            character = Character.active.get(id=character_id)
            # Сохраняем в кеш (сериализуем данные)
            cache_data = {
                'id': str(character.id),
                'name': character.name,
                'type': character.type,
                'level': character.level,
                'class_name': character.class_name,
                'ancestry': character.ancestry,
                'heritage': character.heritage,
                'background': character.background,
                'hp_max': character.hp_max,
                'hp_current': character.hp_current,
                'speed': character.speed,
                'created_at': character.created_at.isoformat() if character.created_at else None,
                'updated_at': character.updated_at.isoformat() if character.updated_at else None,
            }
            cache_service.set(cache_key, cache_data)
            return character
        except Character.DoesNotExist:
            return None

    @staticmethod
    def create(data, user=None):
        # Сначала валидируем данные через сериализатор
        serializer = CharacterCreateUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # Затем проверяем уникальность имени
        name = data.get('name')
        if name and Character.active.filter(name=name).exists():
            raise ConflictError("Персонаж с таким именем уже существует")
        
        character = serializer.save(owner=user)
        
        # Инвалидация кеша списков
        CharacterService._invalidate_list_cache()
        
        return character

    @staticmethod
    def update(character_id, data, partial=False, user=None):
        character = Character.active.get(id=character_id)
        
        # Проверяем владение если передан пользователь
        if user and character.owner and character.owner != user:
            raise PermissionDenied("Нет прав для редактирования этого персонажа")
        
        # Сначала валидируем данные через сериализатор
        serializer = CharacterCreateUpdateSerializer(character, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # Проверяем уникальность имени, если оно меняется
        new_name = data.get('name')
        if new_name and new_name != character.name:
            if Character.active.filter(name=new_name).exclude(id=character_id).exists():
                raise ConflictError("Персонаж с таким именем уже существует")
        
        character = serializer.save()
        
        # Инвалидация кеша списков и конкретного элемента
        CharacterService._invalidate_list_cache()
        cache_service.delete(CharacterService._get_detail_cache_key(character_id))
        
        return character

    @staticmethod
    def delete(character_id, user=None):
        character = Character.active.get(id=character_id)
        
        # Проверяем владение если передан пользователь
        if user and character.owner and character.owner != user:
            raise PermissionDenied("Нет прав для удаления этого персонажа")
        
        character.soft_delete()
        
        # Инвалидация кеша списков и конкретного элемента
        CharacterService._invalidate_list_cache()
        cache_service.delete(CharacterService._get_detail_cache_key(character_id))
        
        return True