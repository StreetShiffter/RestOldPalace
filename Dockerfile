FROM python:3.12-slim

# Устанавливаем системные зависимости для компиляции пакетов из документации
#каждой отдельной зависимости для установки через Debian/Ubuntu
#нужны для slim версии python, т.к. там нет таких библиотек для зависимостей проекта
#собирай и смотри что еще надо поставить

#RUN apt-get update && apt-get install -y --no-install-recommends \
#    gcc \
#    libc6-dev \
#    libpq-dev \
#    libjpeg-dev \
#    zlib1g-dev \
#    libpng-dev \
#    libfreetype6-dev \
#    #Удаляем кэш APT
#    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && pip install poetry #современный способ обновления библиотек

# Рабочая директория
WORKDIR /RestOldPalace

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Настраиваем Poetry и устанавливаем зависимости
# --no-root: не устанавливаем сам проект как пакет (опционально, но безопасно)
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root

# Копируем исходный код
COPY . .

# Создаём папку media (на случай, если том не смонтирован)
RUN mkdir -p /RestOldPalace/media

# Открываем порт (для документации, не обязателен)
EXPOSE 8000

# Запуск приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]