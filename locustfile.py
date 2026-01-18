import random
from faker import Faker 

fake = Faker("ru_RU")

from locust import HttpUser, task, SequentialTaskSet, TaskSet, constant_throughput

class UserTest(SequentialTaskSet):
    def on_start(self):
        login_response = self.client.post("/api/auth/login/", json={
                "email": "ivanov_joybox@mail.ru",
                "password": "Qwer1234!"
            }, headers = {
                'Content-Type': 'application/json',
            })
        
        if login_response.status_code == 200:
            self.auth_token = login_response.json()['token']
        
    @task
    def add_user(self):
        user_data = {
            "firstName": fake.first_name(),
            "lastName": fake.last_name(),
            "middleName": fake.middle_name() if random.choice([True, False]) else None,
            "email": fake.email(),
            "phone": fake.phone_number()[:11],  
            "birthDate": fake.date_of_birth(minimum_age=6, maximum_age=80).strftime('%Y-%m-%d'),
            "roleId": random.choice([1, 2, 4, 5]), 
            "password": "Qwer1234!!",
            "username": fake.user_name()
        }

        self.client.post("/api/admin/users/create/",
                        json=user_data,
                        headers={
                            'Authorization': f'Token {self.auth_token}',
                            'Content-Type': 'application/json'
                        })

    @task
    def delete_user(self):
        response = self.client.get("/api/admin/users/",
                                  headers={'Authorization': f'Token {self.auth_token}'})
        
        if response.status_code == 200:
            try:
                users = response.json()
                if len(users) > 1: 
                    user_ids = [u['userId'] for u in users if u['email'] != "ivanov_joybox@mail.ru"]
                    if user_ids:
                        user_id = random.choice(user_ids)
                        self.client.delete(f"/api/admin/users/{user_id}/",
                                          headers={'Authorization': f'Token {self.auth_token}'})
            except Exception as e:
                print(f"Ошибка удаления: {e}")
        self.interrupt()

class ProductTest(TaskSet):
    def on_start(self):
        login_response = self.client.post("/api/auth/login/", json={
                "email": "ivanov_joybox@mail.ru",
                "password": "Qwer1234!"
            }, headers = {
                'Content-Type': 'application/json',
            })
        
        if login_response.status_code == 200:
            self.auth_token = login_response.json()['token']

    @task(1)
    def delete_product(self):
        response = self.client.get("/api/admin/products/",
                                  headers={'Authorization': f'Token {self.auth_token}'})
        if response.status_code == 200:
            try:
                products = response.json()
                if len(products) > 5:  # Keep some products
                    product = random.choice(products)
                    product_id = product['productId']
                    self.client.delete(f"/api/admin/products/{product_id}/",
                                      headers={'Authorization': f'Token {self.auth_token}'})
            except Exception as e:
                print(f"Ошибка удаления: {e}")

    @task(1)
    def add_product(self):
        product_data = {
            "productName": f"{fake.word()} {fake.word()}",
            "productDescription": fake.text(max_nb_chars=200),
            "price": round(random.uniform(100, 5000), 2),
            "ageRating": random.choice([0, 6, 12, 16, 18]),
            "quantity": random.randint(1, 100),
            "weightKg": round(random.uniform(0.1, 10), 2),
            "dimensions": f"{random.randint(5, 50)}x{random.randint(5, 50)}x{random.randint(5, 50)}",
            "categoryId": random.randint(1, 1),  
            "brandId": random.randint(1, 2)
        }
        
        self.client.post("/api/admin/products/create/",
                        json=product_data,
                        headers={
                            'Authorization': f'Token {self.auth_token}',
                            'Content-Type': 'application/json'
                        })

    @task(5)
    def get_products(self):
        self.client.get("/api/catalog/products/") 

class WebsiteUser(HttpUser):

    wait_time = constant_throughput(2)

    tasks = [
        UserTest,
        ProductTest
    ]
