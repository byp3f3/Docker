#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Тестируем API городов
print("=== Тестирование API городов ===")

# URL для API городов
api_url = "http://127.0.0.1:8000/api/cities/"

try:
    print(f"Отправляем GET запрос на: {api_url}")
    response = requests.get(api_url)
    
    print(f"Статус ответа: {response.status_code}")
    print(f"Заголовки ответа: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Данные ответа: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if isinstance(data, list):
            print(f"Количество городов в ответе: {len(data)}")
            for city in data:
                print(f"  - ID: {city.get('id')}, Name: {city.get('name')}")
        else:
            print("ОШИБКА: Ответ не является списком!")
            print(f"Тип ответа: {type(data)}")
    else:
        print(f"ОШИБКА: HTTP {response.status_code}")
        print(f"Текст ответа: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("ОШИБКА: Не удается подключиться к серверу. Убедитесь, что Django сервер запущен.")
except Exception as e:
    print(f"ОШИБКА: {e}")

print("\n=== Проверка через Django ORM ===")
from flowerroom.models import City
cities = City.objects.all()
print(f"Города в БД: {cities.count()}")
for city in cities:
    print(f"  - ID: {city.id}, Name: {city.name}") 