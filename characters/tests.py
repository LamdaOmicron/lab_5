# Create your tests here.
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
import uuid
from .models import Character
from django.test import TestCase
class CharacterAPITestCase(APITestCase):
    
    def setUp(self):
        # Создаём тестового персонажа
        self.character_data = {
            'name': 'Тестовый персонаж',
            'type': 'character',
            'level': 3,
            'class_name': 'Oracle',
            'ancestry': 'Kitsune',
            'heritage': 'Frozen Wind Kitsune',
            'background': 'Undertaker',
            'hp_max': 20,
            'hp_current': 20,
            'speed': 25
        }
        self.character = Character.objects.create(**self.character_data)
        self.list_url = reverse('character-list')
        self.detail_url = reverse('character-detail', kwargs={'id': self.character.id})

    def test_get_characters_list(self):
        """GET /api/characters/ — получение списка с пагинацией"""
        response = self.client.get(self.list_url, {'page': 1, 'limit': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('meta', response.data)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['meta']['total'], 1)
        self.assertEqual(response.data['meta']['page'], 1)
        self.assertEqual(response.data['meta']['limit'], 10)
        self.assertEqual(response.data['meta']['totalPages'], 1)

    def test_get_character_detail(self):
        """GET /api/characters/{id}/ — получение одного персонажа"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.character_data['name'])
        self.assertEqual(response.data['level'], self.character_data['level'])

    def test_get_nonexistent_character(self):
        """GET /api/characters/{invalid_id}/ — 404 Not Found"""
        invalid_id = uuid.uuid4()
        url = reverse('character-detail', kwargs={'id': invalid_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_character(self):
        """POST /api/characters/ — создание нового персонажа"""
        new_data = {
            'name': 'Новый персонаж',
            'type': 'character',
            'level': 1,
            'class_name': 'Bard',
            'ancestry': 'Human',
            'heritage': '',
            'background': 'Acolyte',
            'hp_max': 10,
            'hp_current': 10,
            'speed': 30
        }
        response = self.client.post(self.list_url, new_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], new_data['name'])
        self.assertEqual(Character.objects.count(), 2)

    def test_create_character_duplicate_name(self):
        """POST /api/characters/ — дублирование имени -> 409 Conflict"""
        duplicate_data = self.character_data.copy()
        duplicate_data['name'] = self.character_data['name']  # то же имя
        response = self.client.post(self.list_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)

    def test_create_character_invalid_level(self):
        """POST /api/characters/ — неверный уровень -> 400 Bad Request"""
        invalid_data = self.character_data.copy()
        invalid_data['level'] = 0
        response = self.client.post(self.list_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_character(self):
        """PUT /api/characters/{id}/ — полное обновление"""
        updated_data = self.character_data.copy()
        updated_data['name'] = 'Обновлённое имя'
        updated_data['level'] = 5
        response = self.client.put(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.character.refresh_from_db()
        self.assertEqual(self.character.name, 'Обновлённое имя')
        self.assertEqual(self.character.level, 5)

    def test_partial_update_character(self):
        """PATCH /api/characters/{id}/ — частичное обновление"""
        patch_data = {'hp_current': 15}
        response = self.client.patch(self.detail_url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.character.refresh_from_db()
        self.assertEqual(self.character.hp_current, 15)

    def test_soft_delete_character(self):
        """DELETE /api/characters/{id}/ — мягкое удаление"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Обновляем объект из БД
        self.character.refresh_from_db()
        self.assertIsNotNone(self.character.deleted_at)

    def test_get_deleted_character(self):
        """GET /api/characters/{id}/ после удаления -> 404 Not Found"""
        self.character.soft_delete()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pagination_limit(self):
        """Проверка, что limit работает и ограничен максимумом"""
        # Создадим 30 персонажей
        for i in range(30):
            Character.objects.create(
                name=f'Персонаж {i}',
                type='character',
                level=1,
                class_name='Warrior',
                hp_max=10, hp_current=10, speed=20
            )
        # Запрос с limit=50 (больше max_page_size=100, но по умолчанию 100)
        # В нашем CustomPageNumberPagination max_page_size=100, поэтому должно быть 30 записей
        response = self.client.get(self.list_url, {'limit': 50})
        self.assertEqual(len(response.data['data']), 31)  # всего 31 (1 старый + 30 новых)
        self.assertEqual(response.data['meta']['limit'], 50)
        # Проверка, что limit не превышает max_page_size (100)
        response = self.client.get(self.list_url, {'limit': 150})
        self.assertEqual(response.data['meta']['limit'], 100)  # должно ограничиться