import requests
import json

# URL для тестирования
base_url = 'http://127.0.0.1:8000'

# Создаем сессию для сохранения cookies
session = requests.Session()

# Тест 1: Попытка получить корзину без аутентификации
print("Тест 1: Попытка получить корзину без аутентификации")
response = session.get(f'{base_url}/api/cart/')
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
print()

# Тест 2: Попытка добавить товар в корзину без аутентификации
print("Тест 2: Попытка добавить товар в корзину без аутентификации")
response = session.post(
    f'{base_url}/api/cart/',
    json={'product_id': 1, 'quantity': 1},
    headers={'Content-Type': 'application/json'}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
print()

# Тест 3: Попытка получить список городов (должно работать без аутентификации)
print("Тест 3: Попытка получить список городов")
response = session.get(f'{base_url}/api/cities/')
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}...")  # Показываем только первые 200 символов
print()

print("Тесты завершены!") 