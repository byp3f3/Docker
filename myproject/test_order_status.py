import requests
from bs4 import BeautifulSoup

# URL для тестирования
base_url = 'http://127.0.0.1:8000'

# Создаем сессию для сохранения cookies
session = requests.Session()

# Тест 1: Получение страницы входа
print("Тест 1: Получение страницы входа")
response = session.get(f'{base_url}/login/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    
    if csrf_token:
        csrf_value = csrf_token.get('value')
        print("CSRF токен найден")
        
        # Тест 2: Попытка входа
        print("\nТест 2: Попытка входа")
        login_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'csrfmiddlewaretoken': csrf_value
        }
        
        response = session.post(f'{base_url}/login/', data=login_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Проверяем, есть ли ошибки входа
            soup = BeautifulSoup(response.text, 'html.parser')
            error_messages = soup.find_all(class_='alert-danger')
            if error_messages:
                print("Ошибка входа (ожидаемо для тестового пользователя)")
            else:
                print("Вход выполнен успешно")
                
                # Тест 3: Получение страницы "Мои заказы"
                print("\nТест 3: Получение страницы 'Мои заказы'")
                response = session.get(f'{base_url}/my-orders/')
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("Страница 'Мои заказы' загружена")
                    
                    # Проверяем отображение статусов
                    soup = BeautifulSoup(response.text, 'html.parser')
                    status_badges = soup.find_all(class_='badge')
                    if status_badges:
                        print(f"Найдено статусов: {len(status_badges)}")
                        for badge in status_badges:
                            print(f"  - {badge.text.strip()}")
                    else:
                        print("Статусы не найдены")
                    
                    # Проверяем наличие кнопок отмены
                    cancel_buttons = soup.find_all('a', href=lambda x: x and 'cancel' in x)
                    if cancel_buttons:
                        print(f"Найдено кнопок отмены: {len(cancel_buttons)}")
                    else:
                        print("Кнопки отмены не найдены")
                else:
                    print("Ошибка загрузки страницы 'Мои заказы'")
        else:
            print("Ошибка при попытке входа")
    else:
        print("CSRF токен не найден")
else:
    print("Ошибка загрузки страницы входа")

print("\nТесты завершены!") 