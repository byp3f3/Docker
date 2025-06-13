from django.db import models

class User(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Администратор'),
        ('Manager', 'Менеджер'),
        ('Customer', 'Покупатель'),
    ]

    username = models.CharField(max_length=50, unique=True, verbose_name='Имя пользователя')
    password = models.CharField(max_length=255, verbose_name='Пароль')
    email = models.EmailField(unique=True, verbose_name='Email')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name='Роль')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    phone = models.CharField(max_length=11, null=True, blank=True, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class ProductCategory(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Категория товара'
        verbose_name_plural = 'Категории товаров'

    def __str__(self):
        return self.name
    
class Supplier(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    contact_person = models.CharField(max_length=100, null=True, blank=True, verbose_name='Контактное лицо')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(null=True, blank=True, verbose_name='Email')
    address = models.TextField(null=True, blank=True, verbose_name='Адрес')

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, verbose_name='Категория')
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    stock_quantity = models.IntegerField(default=0, verbose_name='Количество на складе')
    suppliers = models.ManyToManyField(Supplier, verbose_name='Поставщики')
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='Фотография')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

class PlantType(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Тип растения'
        verbose_name_plural = 'Типы растений'

    def __str__(self):
        return self.name

class PlantAttribute(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Характеристика растения'
        verbose_name_plural = 'Характеристики растений'

    def __str__(self):
        return self.name

class Plant(models.Model):
    plant_type = models.ForeignKey(PlantType, on_delete=models.CASCADE, verbose_name='Тип растения')
    product = models.OneToOneField(Product, on_delete=models.CASCADE, verbose_name='Товар')
    scientific_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='Научное название')
    attributes = models.ManyToManyField(PlantAttribute, verbose_name='Характеристики')

    class Meta:
        verbose_name = 'Растение'
        verbose_name_plural = 'Растения'

    def __str__(self):
        return self.scientific_name or self.product.name

class Certificate(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name='Код')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='Срок действия')
    is_used = models.BooleanField(default=False, verbose_name='Использован')
    used_by = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Использован покупателем')
    used_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата использования')

    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'

    def __str__(self):
        return self.code

class City(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self):
        return self.name

class DeliveryAddress(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    building = models.CharField(max_length=20, verbose_name='Дом')
    apartment = models.CharField(max_length=20, null=True, blank=True, verbose_name='Квартира')
    postal_code = models.CharField(max_length=20, null=True, blank=True, verbose_name='Почтовый индекс')

    class Meta:
        verbose_name = 'Адрес доставки'
        verbose_name_plural = 'Адреса доставки'

    def __str__(self):
        return f"{self.street}, {self.building}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Ожидает обработки'),
        ('Processing', 'В обработке'),
        ('Shipped', 'Отправлен'),
        ('Delivered', 'Доставлен'),
        ('Cancelled', 'Отменен'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Покупатель')
    address = models.ForeignKey(DeliveryAddress, on_delete=models.CASCADE, verbose_name='Адрес доставки')
    order_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Статус')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая сумма')
    certificate = models.ForeignKey(Certificate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Сертификат')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Сумма скидки')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.IntegerField(verbose_name='Количество')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за единицу')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Покупатель')
    rating = models.IntegerField(verbose_name='Оценка')
    comment = models.TextField(null=True, blank=True, verbose_name='Комментарий')
    review_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата отзыва')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f"Отзыв от {self.customer} на {self.product}"


