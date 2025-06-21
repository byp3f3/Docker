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
        
        # Тест 2: Попытка входа (нужно будет создать тестового пользователя)
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
                
                # Тест 3: Получение страницы профиля
                print("\nТест 3: Получение страницы профиля")
                response = session.get(f'{base_url}/profile/')
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("Страница профиля загружена")
                    
                    # Тест 4: Получение страницы редактирования профиля
                    print("\nТест 4: Получение страницы редактирования профиля")
                    response = session.get(f'{base_url}/profile/edit/')
                    print(f"Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("Страница редактирования профиля загружена")
                        
                        # Проверяем наличие формы
                        soup = BeautifulSoup(response.text, 'html.parser')
                        form = soup.find('form')
                        if form:
                            print("Форма редактирования найдена")
                            
                            # Проверяем наличие полей
                            fields = ['first_name', 'last_name', 'email', 'phone']
                            for field in fields:
                                field_input = soup.find('input', {'name': field})
                                if field_input:
                                    print(f"Поле {field} найдено")
                                else:
                                    print(f"Поле {field} НЕ найдено")
                        else:
                            print("Форма редактирования НЕ найдена")
                    else:
                        print("Ошибка загрузки страницы редактирования профиля")
                else:
                    print("Ошибка загрузки страницы профиля")
        else:
            print("Ошибка при попытке входа")
    else:
        print("CSRF токен не найден")
else:
    print("Ошибка загрузки страницы входа")

print("\nТесты завершены!") 