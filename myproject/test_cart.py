import requests
from bs4 import BeautifulSoup

# URL для тестирования
base_url = 'http://127.0.0.1:8000'

# Создаем сессию для сохранения cookies
session = requests.Session()

# Тест 1: Получаем главную страницу
print("Тест 1: Получение главной страницы")
response = session.get(f'{base_url}/')
print(f"Status: {response.status_code}")
print()

# Тест 2: Получаем страницу каталога
print("Тест 2: Получение страницы каталога")
response = session.get(f'{base_url}/catalog/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    # Ищем ссылки на товары
    product_links = soup.find_all('a', href=True)
    product_urls = [link['href'] for link in product_links if '/product/' in link['href']]
    
    if product_urls:
        print(f"Найдено товаров: {len(product_urls)}")
        first_product_url = product_urls[0]
        print(f"Первый товар: {first_product_url}")
        
        # Тест 3: Получаем страницу товара
        print("\nТест 3: Получение страницы товара")
        response = session.get(f'{base_url}{first_product_url}')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Ищем форму добавления в корзину
            add_to_cart_form = soup.find('form', {'id': 'add-to-cart-form'})
            if add_to_cart_form:
                print("Форма добавления в корзину найдена")
                # Ищем product_id
                product_id_input = add_to_cart_form.find('input', {'name': 'product_id'})
                if product_id_input:
                    product_id = product_id_input.get('value')
                    print(f"Product ID: {product_id}")
                    
                    # Тест 4: Попытка добавить товар в корзину (должна быть ошибка без аутентификации)
                    print("\nТест 4: Попытка добавить товар в корзину")
                    response = session.post(
                        f'{base_url}/add-to-cart/',
                        data={'product_id': product_id, 'quantity': 1}
                    )
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
                else:
                    print("Product ID не найден в форме")
            else:
                print("Форма добавления в корзину не найдена")
    else:
        print("Товары не найдены")
else:
    print("Не удалось получить каталог")

print("\nТесты завершены!") 