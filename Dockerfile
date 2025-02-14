# Используем официальный образ Python 3.12
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg
# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем исходный код
COPY . .

# Указываем команду для запуска
CMD ["python", "main.py"]

