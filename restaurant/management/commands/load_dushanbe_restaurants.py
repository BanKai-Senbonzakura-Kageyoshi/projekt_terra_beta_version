from django.core.management.base import BaseCommand

from restaurant.models import Restaurant


RESTAURANTS = [
    {
        'name': 'Sorbon',
        'slug': 'sorbon-dushanbe',
        'address': 'Душанбе, улица Айни',
        'latitude': '38.563171',
        'longitude': '68.791101',
    },
    {
        'name': 'Farovon',
        'slug': 'farovon-dushanbe',
        'address': 'Душанбе, улица Карамов',
        'latitude': '38.594229',
        'longitude': '68.753954',
    },
    {
        'name': 'Лесная сказка',
        'slug': 'lesnaya-skazka-dushanbe',
        'address': 'Душанбе, Таджикистан',
        'latitude': '38.583863',
        'longitude': '68.741903',
    },
    {
        'name': 'Арбат',
        'slug': 'arbat-dushanbe',
        'address': 'Душанбе, Таджикистан',
        'latitude': '38.584700',
        'longitude': '68.749652',
    },
    {
        'name': 'Райхон',
        'slug': 'rayhon-dushanbe',
        'address': 'Душанбе, Таджикистан',
        'latitude': '38.592650',
        'longitude': '68.744456',
    },
    {
        'name': 'Маржона',
        'slug': 'marjona-dushanbe',
        'address': 'Душанбе, Таджикистан',
        'latitude': '38.609121',
        'longitude': '68.789539',
        'cuisine': 'Региональная кухня',
    },
    {
        'name': 'Oli Somon',
        'slug': 'oli-somon-dushanbe',
        'address': 'Душанбе, Таджикистан',
        'latitude': '38.567689',
        'longitude': '68.751729',
        'cuisine': 'Азиатская кухня',
    },
    {
        'name': 'Ошхонаи Сино',
        'slug': 'oshkhonai-sino-dushanbe',
        'address': 'Душанбе, Таджикистан',
        'latitude': '38.588118',
        'longitude': '68.755816',
        'cuisine': 'Региональная кухня',
    },
    {
        'name': 'Парасту',
        'slug': 'parastu-dushanbe',
        'address': 'Душанбе, Таджикистан',
        'latitude': '38.586641',
        'longitude': '68.729955',
    },
    {
        'name': 'Navruzgoh',
        'slug': 'navruzgoh-dushanbe',
        'address': 'Душанбе, проспект Хофизи Шерози',
        'latitude': '38.568695',
        'longitude': '68.773037',
    },
    {
        'name': 'Тарабхонаи «КАНД»',
        'slug': 'kand-dushanbe',
        'address': 'Душанбе, улица Баховиддинова, 101-й микрорайон',
        'latitude': '38.577715',
        'longitude': '68.734758',
        'cuisine': 'Национальная кухня',
    },
    {
        'name': 'Тарабхонаи «Шоми-101»',
        'slug': 'shomi-101-dushanbe',
        'address': 'Душанбе, улица Баховиддинова, 101-й микрорайон',
        'latitude': '38.577181',
        'longitude': '68.736342',
        'cuisine': 'Национальная кухня',
    },
    {
        'name': 'Қурутобхона',
        'slug': 'qurutobkhona-dushanbe',
        'address': 'Душанбе, улица Бободжона Гафурова, 101-й микрорайон',
        'latitude': '38.581012',
        'longitude': '68.740401',
        'cuisine': 'Национальная кухня',
    },
]


class Command(BaseCommand):
    help = 'Добавляет тринадцать заведений Душанбе из данных OpenStreetMap.'

    def handle(self, *args, **options):
        Restaurant.objects.filter(
            owner__isnull=True,
            slug__in=['safarali-dushanbe', 'shomi-zebo-dushanbe'],
        ).delete()

        for item in RESTAURANTS:
            Restaurant.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    **item,
                    'cuisine': item.get('cuisine', ''),
                    'description': (
                        'Открытые сведения о названии и местоположении получены '
                        'из OpenStreetMap. Точное меню, часы работы и телефон '
                        'пока не добавлены.'
                    ),
                    'owner': None,
                    'is_approved': True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS('В каталог добавлено 13 заведений Душанбе.'),
        )
