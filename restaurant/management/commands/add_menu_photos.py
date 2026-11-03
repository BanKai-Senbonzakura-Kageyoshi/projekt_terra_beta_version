from django.core.management.base import BaseCommand

from restaurant.models import MenuItem


PHOTO_IDS = {
    'samosa': 'photo-1601050690597-df0568f70950',
    'salad': 'photo-1512621776951-a57141f2eefd',
    'soup': 'photo-1547592180-85f173990554',
    'noodles': 'photo-1555949258-eb67b1ef0ceb',
    'rice': 'photo-1512058564366-18510be2db19',
    'dumplings': 'photo-1563245372-f21724e3856d',
    'grill': 'photo-1555939594-58d7cb561ad1',
    'vegetables': 'photo-1540420773420-3366772f4999',
    'dessert': 'photo-1578985545062-69928b1d9587',
    'tea': 'photo-1544787219-7f47ccb76574',
    'breakfast': 'photo-1525351484163-7529414344d8',
    'pasta': 'photo-1473093295043-cdd812d0e601',
    'pizza': 'photo-1513104890138-7c749659a591',
    'side': 'photo-1573080496219-bb080dd4f877',
    'bread': 'photo-1509440159596-0249088772ff',
    'coffee': 'photo-1495474472287-4d71bcdd2085',
    'lemonade': 'photo-1544145945-f90425340c7e',
    'juice': 'photo-1600271886742-f049cd451bba',
    'default': 'photo-1504674900247-0877df9cc836',
}

ITEM_PHOTOS = {
    'Самбуса с зеленью': 'samosa',
    'Салат из свежих овощей': 'salad',
    'Шурбо с говядиной': 'soup',
    'Лагман по-домашнему': 'noodles',
    'Плов с говядиной': 'rice',
    'Манты с тыквой': 'dumplings',
    'Куриный шашлык': 'grill',
    'Овощи на углях': 'vegetables',
    'Чак-чак с мёдом': 'dessert',
    'Зелёный чай': 'tea',
    'Каша с фруктами': 'breakfast',
    'Омлет с овощами': 'breakfast',
    'Салат с курицей': 'salad',
    'Салат с сыром': 'salad',
    'Паста с курицей': 'pasta',
    'Паста с томатным соусом': 'noodles',
    'Пицца с сыром': 'pizza',
    'Пицца с овощами': 'pizza',
    'Картофель по-домашнему': 'side',
    'Рис с овощами': 'rice',
    'Лепёшка из тандыра': 'bread',
    'Пирог с яблоком': 'dessert',
    'Кофе латте': 'coffee',
    'Американо': 'coffee',
    'Домашний лимонад': 'lemonade',
    'Свежевыжатый сок': 'juice',
}

CATEGORY_PHOTOS = {
    'закуск': 'samosa',
    'салат': 'salad',
    'суп': 'soup',
    'лагман': 'noodles',
    'горяч': 'rice',
    'гриль': 'grill',
    'десерт': 'dessert',
    'напит': 'tea',
}


def photo_url(photo_name):
    photo_id = PHOTO_IDS[photo_name]
    return f'https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=720&q=80'


def choose_photo(item):
    photo_name = ITEM_PHOTOS.get(item.name)
    if photo_name is None:
        category_name = item.category.name.lower()
        photo_name = next(
            (
                photo
                for category_part, photo in CATEGORY_PHOTOS.items()
                if category_part in category_name
            ),
            'default',
        )
    return photo_url(photo_name)


class Command(BaseCommand):
    help = 'Добавляет иллюстративные фотографии блюдам меню, у которых их ещё нет.'

    def handle(self, *args, **options):
        updated_count = 0
        for item in MenuItem.objects.select_related('category').filter(image_url=''):
            item.image_url = choose_photo(item)
            item.save(update_fields=['image_url'])
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Добавлены фотографии для {updated_count} блюд без фотографий.',
            ),
        )
        self.stdout.write(
            self.style.WARNING(
                'Это иллюстративные стоковые фотографии; рестораны их не подтверждали.',
            ),
        )
