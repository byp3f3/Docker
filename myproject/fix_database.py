#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from flowerroom.models import DeliveryAddress, City
from django.db import connection, models

print("=== Диагностика базы данных ===")

# Проверяем существующие адреса
print("\n1. Существующие адреса доставки:")
addresses = DeliveryAddress.objects.all().order_by('id')
print(f"Количество адресов: {addresses.count()}")
for addr in addresses:
    print(f"  ID: {addr.id}, Город: {addr.city.name}, Улица: {addr.street}, Дом: {addr.building}")

# Проверяем максимальный ID
if addresses.exists():
    max_id = addresses.aggregate(max_id=models.Max('id'))['max_id']
    print(f"\n2. Максимальный ID в таблице адресов: {max_id}")
else:
    print("\n2. Таблица адресов пуста")
    max_id = 0

# Проверяем последовательность ID (для PostgreSQL)
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT last_value FROM flowerroom_deliveryaddress_id_seq")
        last_value = cursor.fetchone()[0]
        print(f"\n3. Текущее значение последовательности: {last_value}")
        
        if last_value <= max_id:
            print("   ⚠️  Последовательность отстает от максимального ID!")
            print("   Исправляем последовательность...")
            
            cursor.execute(f"SELECT setval('flowerroom_deliveryaddress_id_seq', {max_id + 1})")
            new_value = cursor.fetchone()[0]
            print(f"   ✅ Последовательность исправлена. Новое значение: {new_value}")
        else:
            print("   ✅ Последовательность в порядке")
            
except Exception as e:
    print(f"\n3. Ошибка проверки последовательности: {e}")
    print("   Возможно, используется SQLite или другая БД")

# Тестируем создание нового адреса
print("\n4. Тестируем создание нового адреса...")
try:
    # Получаем первый город для теста
    city = City.objects.first()
    if city:
        test_address = DeliveryAddress.objects.create(
            city=city,
            street="Тестовая улица",
            building="1",
            apartment="1",
            postal_code="123456"
        )
        print(f"   ✅ Тестовый адрес создан с ID: {test_address.id}")
        
        # Удаляем тестовый адрес
        test_address.delete()
        print("   ✅ Тестовый адрес удален")
    else:
        print("   ❌ Нет городов в базе данных")
        
except Exception as e:
    print(f"   ❌ Ошибка создания тестового адреса: {e}")

print("\n=== Диагностика завершена ===") 