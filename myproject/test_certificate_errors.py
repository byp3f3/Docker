import requests
import json

# URL для тестирования
base_url = 'http://127.0.0.1:8000'

# Создаем сессию для сохранения cookies
session = requests.Session()

def test_certificate_errors():
    print("Тестирование обработки ошибок сертификатов в API checkout")
    print("=" * 60)
    
    # Тест 1: Несуществующий сертификат
    print("\nТест 1: Несуществующий сертификат")
    checkout_data = {
        'address': {
            'city': 1,
            'street': 'Тестовая улица',
            'building': '1',
            'apartment': '1',
            'postal_code': '123456'
        },
        'certificate_code': 'NONEXISTENT123'
    }
    
    response = session.post(
        f'{base_url}/api/checkout/',
        json=checkout_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        data = response.json()
        print(f"Error type: {data.get('error_type')}")
        print(f"Message: {data.get('message')}")
        if data.get('error_type') == 'certificate_not_found':
            print("✅ Правильная обработка несуществующего сертификата")
        else:
            print("❌ Неправильная обработка несуществующего сертификата")
    else:
        print("❌ Неожиданный статус ответа")
    
    # Тест 2: Использованный сертификат (нужно создать тестовый сертификат)
    print("\nТест 2: Использованный сертификат")
    checkout_data['certificate_code'] = 'USED123'
    
    response = session.post(
        f'{base_url}/api/checkout/',
        json=checkout_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        data = response.json()
        print(f"Error type: {data.get('error_type')}")
        print(f"Message: {data.get('message')}")
        if data.get('error_type') == 'certificate_used':
            print("✅ Правильная обработка использованного сертификата")
        else:
            print("❌ Неправильная обработка использованного сертификата")
    else:
        print("❌ Неожиданный статус ответа")
    
    # Тест 3: Просроченный сертификат
    print("\nТест 3: Просроченный сертификат")
    checkout_data['certificate_code'] = 'EXPIRED123'
    
    response = session.post(
        f'{base_url}/api/checkout/',
        json=checkout_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        data = response.json()
        print(f"Error type: {data.get('error_type')}")
        print(f"Message: {data.get('message')}")
        if data.get('error_type') == 'certificate_expired':
            print("✅ Правильная обработка просроченного сертификата")
        else:
            print("❌ Неправильная обработка просроченного сертификата")
    else:
        print("❌ Неожиданный статус ответа")
    
    # Тест 4: Короткий код сертификата (валидация на клиенте)
    print("\nТест 4: Короткий код сертификата")
    checkout_data['certificate_code'] = '12'  # Меньше 3 символов
    
    response = session.post(
        f'{base_url}/api/checkout/',
        json=checkout_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        data = response.json()
        print(f"Message: {data.get('message')}")
        print("✅ Правильная обработка короткого кода сертификата")
    else:
        print("❌ Неожиданный статус ответа")
    
    print("\n" + "=" * 60)
    print("Тестирование завершено!")

if __name__ == "__main__":
    test_certificate_errors() 