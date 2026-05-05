from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .services import CharacterService
from .serializers import CharacterSerializer, CharacterCreateUpdateSerializer


@extend_schema(
    tags=['Characters'],
    summary='Список персонажей',
    description='Получение списка всех активных персонажей с пагинацией',
    parameters=[
        OpenApiParameter(name='page', type=int, location=OpenApiParameter.QUERY, description='Номер страницы', default=1),
        OpenApiParameter(name='limit', type=int, location=OpenApiParameter.QUERY, description='Количество записей на странице', default=10),
    ],
    responses={
        200: OpenApiResponse(
            description='Список персонажей',
            examples=[
                {
                    "data": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "name": "Valeros",
                            "type": "player",
                            "level": 5,
                            "class_name": "Fighter",
                            "ancestry": "Human",
                            "heritage": "Skilled",
                            "background": "Soldier",
                            "hp_max": 60,
                            "hp_current": 45,
                            "speed": 25,
                            "created_at": "2024-01-01T12:00:00Z",
                            "updated_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "meta": {"total": 42, "page": 1, "limit": 10, "totalPages": 5}
                }
            ]
        )
    }
)
class CharacterListCreateView(APIView):
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        limit = min(limit, 100)
        result = CharacterService.get_all_active(page, limit)
        serializer = CharacterSerializer(result['data'], many=True)
        return Response({
            'data': serializer.data,
            'meta': result['meta']
        })

    @extend_schema(
        summary='Создание персонажа',
        description='Создание нового игрового персонажа',
        request=CharacterCreateUpdateSerializer,
        responses={
            201: OpenApiResponse(
                description='Персонаж успешно создан',
                examples=[
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Valeros",
                        "type": "player",
                        "level": 1,
                        "class_name": "Fighter",
                        "ancestry": "Human",
                        "heritage": "Skilled",
                        "background": "Soldier",
                        "hp_max": 10,
                        "hp_current": 10,
                        "speed": 25,
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T12:00:00Z"
                    }
                ]
            ),
            400: OpenApiResponse(description='Ошибка валидации данных')
        }
    )
    def post(self, request):
        character = CharacterService.create(request.data)
        serializer = CharacterSerializer(character)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Characters'],
    summary='Получение персонажа',
    description='Получение информации о персонаже по UUID',
    parameters=[
        OpenApiParameter(name='pk', type=str, location=OpenApiParameter.PATH, description='UUID персонажа'),
    ],
    responses={
        200: OpenApiResponse(
            description='Данные персонажа',
            examples=[
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Valeros",
                    "type": "player",
                    "level": 5,
                    "class_name": "Fighter",
                    "ancestry": "Human",
                    "heritage": "Skilled",
                    "background": "Soldier",
                    "hp_max": 60,
                    "hp_current": 45,
                    "speed": 25,
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            ]
        ),
        404: OpenApiResponse(description='Персонаж не найден', examples=[{"error": "Персонаж не найден"}])
    }
)
class CharacterDetailView(APIView):
    def get_object(self, pk):
        character = CharacterService.get_by_id(pk)
        if not character:
            raise NotFound(detail="Персонаж не найден")
        return character

    def get(self, request, pk):
        character = self.get_object(pk)
        serializer = CharacterSerializer(character)
        return Response(serializer.data)

    @extend_schema(
        summary='Полное обновление персонажа',
        description='Полное обновление данных персонажа (PUT)',
        request=CharacterCreateUpdateSerializer,
        responses={
            200: OpenApiResponse(description='Персонаж обновлен'),
            404: OpenApiResponse(description='Персонаж не найден')
        }
    )
    def put(self, request, pk):
        character = CharacterService.update(pk, request.data, partial=False)
        serializer = CharacterSerializer(character)
        return Response(serializer.data)

    @extend_schema(
        summary='Частичное обновление персонажа',
        description='Частичное обновление данных персонажа (PATCH)',
        request=CharacterCreateUpdateSerializer,
        responses={
            200: OpenApiResponse(description='Персонаж обновлен'),
            404: OpenApiResponse(description='Персонаж не найден')
        }
    )
    def patch(self, request, pk):
        character = CharacterService.update(pk, request.data, partial=True)
        serializer = CharacterSerializer(character)
        return Response(serializer.data)

    @extend_schema(
        summary='Удаление персонажа',
        description='Мягкое удаление персонажа (soft delete)',
        responses={
            204: OpenApiResponse(description='Персонаж успешно удален'),
            404: OpenApiResponse(description='Персонаж не найден')
        }
    )
    def delete(self, request, pk):
        CharacterService.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)