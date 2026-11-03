from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User


DUSHANBE_LATITUDE_RANGE = ('38.46', '38.71')
DUSHANBE_LONGITUDE_RANGE = ('68.68', '68.89')


class Restaurant(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='restaurants',
        verbose_name='Владелец аккаунта',
        null=True,
        blank=True,
    )
    name = models.CharField('Название', max_length=150)
    slug = models.SlugField('Адрес страницы', unique=True)
    cuisine = models.CharField('Кухня или тип заведения', max_length=100, blank=True)
    description = models.TextField('Описание')
    address = models.CharField('Адрес', max_length=250)
    phone = models.CharField('Телефон', max_length=40, blank=True)
    opening_hours = models.CharField('Часы работы', max_length=100, blank=True)
    menu_is_sample = models.BooleanField(
        'В меню есть примеры, не подтверждённые рестораном',
        default=False,
    )
    latitude = models.DecimalField('Широта карты', max_digits=9, decimal_places=6)
    longitude = models.DecimalField('Долгота карты', max_digits=9, decimal_places=6)
    image = models.ImageField(
        'Фотография ресторана',
        upload_to='restaurants/',
        blank=True,
    )
    image_url = models.URLField('Ссылка на фотографию', blank=True)
    is_approved = models.BooleanField('Показывать на сайте', default=True)
    moderation_note = models.TextField('Комментарий модератора', blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class RestaurantTable(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='tables',
        verbose_name='Ресторан',
    )
    name = models.CharField('Название столика', max_length=80)
    capacity = models.PositiveSmallIntegerField(
        'Количество мест',
        validators=[MinValueValidator(1), MaxValueValidator(20)],
    )
    is_active = models.BooleanField('Доступен для бронирования', default=True)

    class Meta:
        ordering = ['restaurant__name', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'name'],
                name='unique_table_name_per_restaurant',
            ),
        ]
        verbose_name = 'столик'
        verbose_name_plural = 'столики'

    def __str__(self):
        return f'{self.restaurant.name} — {self.name} ({self.capacity} мест)'


class MenuCategory(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name='Ресторан',
        null=True,
        blank=True,
    )
    name = models.CharField('Название категории (RU)', max_length=100)
    name_en = models.CharField('Название категории (EN)', max_length=100, blank=True)
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Показывать на сайте', default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'категория меню'
        verbose_name_plural = 'категории меню'

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Категория',
    )
    name = models.CharField('Название (RU)', max_length=150)
    name_en = models.CharField('Название (EN)', max_length=150, blank=True)
    description = models.TextField('Состав и описание (RU)', blank=True)
    description_en = models.TextField('Состав и описание (EN)', blank=True)
    image = models.ImageField(
        'Фотография блюда',
        upload_to='menu_items/',
        blank=True,
    )
    image_url = models.URLField(
        'Фотография блюда',
        blank=True,
        help_text='Ссылка на фотографию блюда.',
    )
    price = models.DecimalField('Цена в сомони', max_digits=8, decimal_places=2)
    allergens = models.CharField('Аллергены', max_length=200, blank=True)
    is_vegetarian = models.BooleanField('Вегетарианское', default=False)
    is_available = models.BooleanField('Есть в наличии', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['category__order', 'order', 'name']
        verbose_name = 'блюдо'
        verbose_name_plural = 'блюда меню'

    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    title = models.CharField('Подпись (RU)', max_length=150, blank=True)
    title_en = models.CharField('Подпись (EN)', max_length=150, blank=True)
    image_url = models.URLField('Ссылка на оптимизированное изображение')
    alt_text = models.CharField('Описание изображения для доступности', max_length=200)
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Показывать на сайте', default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'фотография галереи'
        verbose_name_plural = 'фотографии галереи'

    def __str__(self):
        return self.title or self.alt_text


class SiteSettings(models.Model):
    address = models.CharField(
        'Адрес',
        max_length=250,
        default='Meros Residence, ул. Мирзо Турсунзода, 24, Душанбе',
    )
    phone = models.CharField('Телефон ресторана', max_length=40, blank=True)
    instagram_url = models.URLField('Instagram', blank=True)
    instagram_name = models.CharField(
        'Имя в Instagram',
        max_length=80,
        default='@terra.dushanbe',
    )
    breakfast_hours = models.CharField(
        'Завтраки',
        max_length=100,
        default='08:00–14:00',
    )
    restaurant_hours = models.CharField(
        'Часы работы ресторана',
        max_length=100,
        blank=True,
        help_text='Оставьте пустым, пока режим не подтверждён.',
    )
    map_url = models.URLField('Ссылка для построения маршрута', blank=True)

    class Meta:
        verbose_name = 'настройки сайта'
        verbose_name_plural = 'настройки сайта'

    def __str__(self):
        return 'Контакты и часы работы Terra'


class BookingRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В обработке'),
        ('confirmed', 'Подтверждена менеджером'),
        ('rejected', 'Отклонена рестораном'),
        ('completed', 'Гости ушли · столик свободен'),
        ('closed', 'Закрыта'),
    ]

    name = models.CharField('Имя', max_length=100)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Ресторан',
        null=True,
        blank=True,
    )
    phone = models.CharField('Телефон', max_length=40)
    booking_date = models.DateField('Дата')
    booking_time = models.TimeField('Время')
    guests = models.PositiveSmallIntegerField(
        'Количество гостей',
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    table = models.ForeignKey(
        RestaurantTable,
        on_delete=models.SET_NULL,
        related_name='bookings',
        verbose_name='Столик',
        null=True,
        blank=True,
    )
    comments = models.TextField('Комментарий', blank=True)
    owner_note = models.TextField('Ответ ресторана', blank=True)
    language = models.CharField('Язык сайта', max_length=2, default='ru')
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'заявка на бронирование'
        verbose_name_plural = 'заявки на бронирование'

    def __str__(self):
        return f'{self.name} — {self.booking_date} {self.booking_time}'


class EventRequest(models.Model):
    name = models.CharField('Имя', max_length=100)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='event_requests',
        verbose_name='Ресторан',
        null=True,
        blank=True,
    )
    phone = models.CharField('Телефон', max_length=40)
    email = models.EmailField('Email', blank=True)
    event_date = models.DateField('Предполагаемая дата')
    event_type = models.CharField('Формат события', max_length=100)
    guests = models.PositiveSmallIntegerField(
        'Ориентировочное число гостей',
        validators=[MinValueValidator(1), MaxValueValidator(500)],
    )
    comments = models.TextField('Комментарий', blank=True)
    language = models.CharField('Язык сайта', max_length=2, default='ru')
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'заявка на частное событие'
        verbose_name_plural = 'заявки на частные события'

    def __str__(self):
        return f'{self.name} — {self.event_type}'
