#!/bin/bash

echo "Проверка конфигурации git..."

# Получаем текущие значения
user_name=$(git config --global user.name)
user_email=$(git config --global user.email)

need_name=false
need_email=false

# Проверка user.name
if [ -z "$user_name" ]; then
    echo "⚠️ user.name не задан. Устанавливаю значение по умолчанию: LamdaOmicron"
    git config --global user.name "LamdaOmicron"
    user_name="LamdaOmicron"
    need_name=true
else
    echo "✅ user.name = $user_name"
fi

# Проверка user.email
if [ -z "$user_email" ]; then
    echo "⚠️ user.email не задан. Устанавливаю значение по умолчанию: genaz0983@gmail.com"
    git config --global user.email "genaz0983@gmail.com"
    user_email="genaz0983@gmail.com"
    need_email=true
else
    echo "✅ user.email = $user_email"
fi

echo ""
if [ "$need_name" = true ] || [ "$need_email" = true ]; then
    echo "✓ Настройки git обновлены:"
    echo "   user.name  = $user_name"
    echo "   user.email = $user_email"
else
    echo "✓ Все параметры git уже настроены корректно."
fi

# Опция клонирования репозитория lab_2
echo ""
read -p "Хотите клонировать репозиторий lab_2? (y/n): " clone_choice
if [[ "$clone_choice" =~ ^[Yy]$ ]]; then
    echo ""
    # Запрос URL репозитория
    read -p "Введите URL репозитория lab_2 (например, https://github.com/user/lab_2.git): " repo_url
    if [ -z "$repo_url" ]; then
        echo "❌ URL не указан. Клонирование отменено."
    else
        # Запрос директории для клонирования (по умолчанию текущая)
        read -p "Введите директорию для клонирования (оставьте пустым для текущей): " target_dir
        if [ -z "$target_dir" ]; then
            target_dir="."
        fi

        # Проверка существования git
        if ! command -v git &> /dev/null; then
            echo "❌ Git не установлен. Невозможно выполнить клонирование."
        else
            echo "Клонирование репозитория $repo_url в $target_dir ..."
            if git clone "$repo_url" "$target_dir"; then
                echo "✅ Репозиторий успешно клонирован."
            else
                echo "❌ Ошибка при клонировании репозитория."
            fi
        fi
    fi
fi

echo ""
read -p "Нажмите Enter для выхода..."