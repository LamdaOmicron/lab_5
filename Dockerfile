FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .
# Открываем порт, который слушает приложение
EXPOSE 4200

# Точка входа: выполняем миграции и запускаем сервер
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:4200"]