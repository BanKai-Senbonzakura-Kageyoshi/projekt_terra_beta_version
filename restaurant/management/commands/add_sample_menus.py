from django.core.management.base import BaseCommand

from .add_menu_photos import ITEM_PHOTOS, photo_url
from restaurant.models import (
    DUSHANBE_LATITUDE_RANGE,
    DUSHANBE_LONGITUDE_RANGE,
    MenuCategory,
    MenuItem,
    Restaurant,
)


SAMPLE_MENU = [
    {
        'category': 'Закуски',
        'items': [
            ('Самбуса с зеленью', 'Тонкое тесто, зелень и лук', '18.00'),
            ('Салат из свежих овощей', 'Томаты, огурцы, зелень и лёгкая заправка', '32.00'),
        ],
    },
    {
        'category': 'Супы',
        'items': [
            ('Шурбо с говядиной', 'Наваристый суп с овощами и зеленью', '58.00'),
            ('Лагман по-домашнему', 'Лапша, овощи и мясо в ароматном бульоне', '64.00'),
        ],
    },
    {
        'category': 'Горячие блюда',
        'items': [
            ('Плов с говядиной', 'Рис, морковь, специи и говядина', '78.00'),
            ('Манты с тыквой', 'Тесто на пару, тыква и лук', '52.00'),
        ],
    },
    {
        'category': 'Гриль',
        'items': [
            ('Куриный шашлык', 'Курица на углях с луком и зеленью', '72.00'),
            ('Овощи на углях', 'Сезонные овощи, приготовленные на гриле', '48.00'),
        ],
    },
    {
        'category': 'Десерты и напитки',
        'items': [
            ('Чак-чак с мёдом', 'Хрустящее тесто и натуральный мёд', '28.00'),
            ('Зелёный чай', 'Заварной чайник зелёного чая', '12.00'),
        ],
    },
    {
        'category': 'Завтраки',
        'items': [
            ('Каша с фруктами', 'Каша с сезонными фруктами', '38.00'),
            ('Омлет с овощами', 'Яйца, томаты, зелень и свежие овощи', '42.00'),
        ],
    },
    {
        'category': 'Салаты',
        'items': [
            ('Салат с курицей', 'Курица, свежие овощи и лёгкая заправка', '48.00'),
            ('Салат с сыром', 'Овощи, сыр и свежая зелень', '44.00'),
        ],
    },
    {
        'category': 'Паста',
        'items': [
            ('Паста с курицей', 'Паста, курица и сливочный соус', '68.00'),
            ('Паста с томатным соусом', 'Паста, томаты и ароматные травы', '58.00'),
        ],
    },
    {
        'category': 'Пицца',
        'items': [
            ('Пицца с сыром', 'Тесто, сыр и томатный соус', '75.00'),
            ('Пицца с овощами', 'Тесто, сезонные овощи и сыр', '70.00'),
        ],
    },
    {
        'category': 'Гарниры',
        'items': [
            ('Картофель по-домашнему', 'Запечённый картофель с зеленью', '30.00'),
            ('Рис с овощами', 'Рис, морковь и свежие овощи', '35.00'),
        ],
    },
    {
        'category': 'Выпечка',
        'items': [
            ('Лепёшка из тандыра', 'Свежая лепёшка из тандыра', '12.00'),
            ('Пирог с яблоком', 'Домашний пирог с яблоком и корицей', '22.00'),
        ],
    },
    {
        'category': 'Кофе',
        'items': [
            ('Кофе латте', 'Кофе эспрессо с молоком', '24.00'),
            ('Американо', 'Классический чёрный кофе', '18.00'),
        ],
    },
    {
        'category': 'Холодные напитки',
        'items': [
            ('Домашний лимонад', 'Лимон, вода и свежая мята', '25.00'),
            ('Свежевыжатый сок', 'Сок из сезонных фруктов', '28.00'),
        ],
    },
]


class Command(BaseCommand):
    help = 'Добавляет каждому ресторану Душанбе 13 категорий и 26 примерных блюд.'

    def handle(self, *args, **options):
        restaurants = Restaurant.objects.filter(
            is_approved=True,
            latitude__range=DUSHANBE_LATITUDE_RANGE,
            longitude__range=DUSHANBE_LONGITUDE_RANGE,
        )
        restaurant_count = 0

        for restaurant in restaurants:
            restaurant.menu_is_sample = True
            restaurant.save(update_fields=['menu_is_sample'])

            for category_order, menu_group in enumerate(SAMPLE_MENU, start=1):
                category, _ = MenuCategory.objects.get_or_create(
                    restaurant=restaurant,
                    name=menu_group['category'],
                    defaults={'order': category_order},
                )

                for item_order, (name, description, price) in enumerate(
                    menu_group['items'],
                    start=1,
                ):
                    item, _ = MenuItem.objects.get_or_create(
                        category=category,
                        name=name,
                        defaults={
                            'description': description,
                            'price': price,
                            'image_url': photo_url(ITEM_PHOTOS[name]),
                            'order': item_order,
                        },
                    )
                    if not item.image_url:
                        item.image_url = photo_url(ITEM_PHOTOS[name])
                        item.save(update_fields=['image_url'])

            restaurant_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Добавлено 13 категорий меню для {restaurant_count} ресторанов.',
            ),
        )
        self.stdout.write(
            self.style.WARNING(
                'Меню, цены и фотографии — примеры, не подтверждённые ресторанами.',
            ),
        )
