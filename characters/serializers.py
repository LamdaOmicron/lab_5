from rest_framework import serializers
from .models import Character



class CharacterSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения персонажа."""
    class Meta:
        model = Character
        fields = ['id', 'name', 'type', 'level', 'class_name', 'ancestry', 
                  'heritage', 'background', 'hp_max', 'hp_current', 'speed',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CharacterCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления персонажа."""
    class Meta:
        model = Character
        fields = ['name', 'type', 'level', 'class_name', 'ancestry', 
                  'heritage', 'background', 'hp_max', 'hp_current', 'speed']

    def validate_level(self, value):
        if value < 1 or value > 20:
            raise serializers.ValidationError("Уровень должен быть от 1 до 20")
        return value