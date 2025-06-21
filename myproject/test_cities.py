#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from flowerroom.models import City
from api_shop.serializers import CitySerializer

# Проверяем города в БД
print("=== Проверка городов в БД ===")
cities = City.objects.all()
print(f"Количество городов: {cities.count()}")
for city in cities:
    print(f"ID: {city.id}, Name: {city.name}")

# Проверяем сериализацию
print("\n=== Проверка сериализации ===")
if cities.exists():
    serializer = CitySerializer(cities, many=True)
    print("Сериализованные данные:")
    print(serializer.data)
else:
    print("Городов нет в БД!")

# Создаем тестовые города если их нет
if not cities.exists():
    print("\n=== Создание тестовых городов ===")
    test_cities = [
        "Москва",
        "Санкт-Петербург", 
        "Новосибирск",
        "Екатеринбург",
        "Казань"
    ]
    
    for city_name in test_cities:
        city, created = City.objects.get_or_create(name=city_name)
        if created:
            print(f"Создан город: {city_name}")
        else:
            print(f"Город уже существует: {city_name}")
    
    # Проверяем снова
    print("\n=== Проверка после создания ===")
    cities = City.objects.all()
    print(f"Количество городов: {cities.count()}")
    for city in cities:
        print(f"ID: {city.id}, Name: {city.name}") 