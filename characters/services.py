from django.utils import timezone
from .models import Character
from .serializers import CharacterCreateUpdateSerializer
from .exceptions import ConflictError

class CharacterService:
    @staticmethod
    def get_all_active(page=1, limit=10):
        start = (page - 1) * limit
        end = start + limit
        queryset = Character.active.all()
        total = queryset.count()
        items = queryset[start:end]
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return {
            'data': items,
            'meta': {
                'total': total,
                'page': page,
                'limit': limit,
                'totalPages': total_pages,
            }
        }

    @staticmethod
    def get_by_id(character_id):
        try:
            return Character.active.get(id=character_id)
        except Character.DoesNotExist:
            return None

    @staticmethod
    def create(data):
        # Сначала валидируем данные через сериализатор
        serializer = CharacterCreateUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # Затем проверяем уникальность имени
        name = data.get('name')
        if name and Character.active.filter(name=name).exists():
            raise ConflictError("Персонаж с таким именем уже существует")
        return serializer.save()

    @staticmethod
    def update(character_id, data, partial=False):
        character = Character.active.get(id=character_id)
        # Сначала валидируем данные через сериализатор
        serializer = CharacterCreateUpdateSerializer(character, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # Проверяем уникальность имени, если оно меняется
        new_name = data.get('name')
        if new_name and new_name != character.name:
            if Character.active.filter(name=new_name).exclude(id=character_id).exists():
                raise ConflictError("Персонаж с таким именем уже существует")
        return serializer.save()

    @staticmethod
    def delete(character_id):
        character = Character.active.get(id=character_id)
        character.soft_delete()
        return True