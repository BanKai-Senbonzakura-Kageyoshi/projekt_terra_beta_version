from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import (
    BookingRequest,
    EventRequest,
    MenuCategory,
    MenuItem,
    Restaurant,
    RestaurantTable,
)


def make_test_image(name='test.jpg'):
    image = Image.new('RGB', (2, 2), color='orange')
    image_file = BytesIO()
    image.save(image_file, format='JPEG')
    return SimpleUploadedFile(name, image_file.getvalue(), content_type='image/jpeg')


class RestaurantPageTests(TestCase):
    def test_main_pages_open(self):
        page_names = [
            'home',
            'about',
            'menu',
            'events',
            'event_request',
            'gallery',
            'contacts',
            'booking',
            'thank_you',
            'privacy',
            'register',
            'login',
        ]

        for page_name in page_names:
            with self.subTest(page=page_name):
                response = self.client.get(reverse(f'restaurant:{page_name}'))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.content.lstrip().startswith(b'<!doctype html>'))
                self.assertContains(response, '<html lang=', html=False)

    def test_homepage_is_a_guide_separate_from_the_restaurant_catalog(self):
        response = self.client.get(reverse('restaurant:home'))

        self.assertContains(response, 'Найдите своё место.')
        self.assertContains(response, 'заведений в Душанбе')
        self.assertNotContains(response, 'restaurant-map-data')

    def test_restaurant_catalog_shows_approved_restaurants(self):
        owner = User.objects.create_user(username='catalog-owner', password='TestPass-8542')
        Restaurant.objects.create(
            owner=owner,
            name='Лимон и Луна',
            slug='limon-test',
            cuisine='Кафе',
            description='Тестовое описание',
            address='Душанбе',
            latitude='38.559800',
            longitude='68.787000',
            is_approved=True,
        )

        response = self.client.get(reverse('restaurant:restaurants'))

        self.assertContains(response, 'Лимон и Луна')
        self.assertContains(response, 'restaurant-map-data')

    def test_restaurant_outside_dushanbe_does_not_show_in_city_catalog(self):
        owner = User.objects.create_user(username='outside-owner', password='TestPass-8542')
        Restaurant.objects.create(
            owner=owner,
            name='Ресторан вне Душанбе',
            slug='outside-dushanbe-test',
            cuisine='Кафе',
            description='Тест',
            address='Другой город',
            latitude='12.202217',
            longitude='123.432142',
            is_approved=True,
        )

        response = self.client.get(reverse('restaurant:restaurants'))

        self.assertNotContains(response, 'Ресторан вне Душанбе')
        self.assertEqual(response.context['restaurants'].count(), 0)

    def test_dushanbe_loader_adds_thirteen_places_without_fake_menus(self):
        call_command('load_dushanbe_restaurants')
        call_command('load_dushanbe_restaurants')

        self.assertEqual(Restaurant.objects.filter(is_approved=True).count(), 13)
        self.assertEqual(MenuCategory.objects.count(), 0)
        self.assertEqual(MenuItem.objects.count(), 0)

    def test_sample_menu_loader_adds_thirteen_categories_and_photos_per_restaurant(self):
        call_command('load_dushanbe_restaurants')
        call_command('add_sample_menus')
        call_command('add_sample_menus')

        restaurants = Restaurant.objects.filter(is_approved=True)
        self.assertEqual(restaurants.count(), 13)
        self.assertEqual(MenuItem.objects.count(), 338)
        self.assertEqual(MenuCategory.objects.count(), 169)
        self.assertTrue(all(restaurant.menu_is_sample for restaurant in restaurants))
        call_command('add_menu_photos')
        call_command('add_menu_photos')
        self.assertEqual(MenuItem.objects.filter(image_url='').count(), 0)
        self.assertEqual(MenuItem.objects.filter(image_url__startswith='https://images.unsplash.com/').count(), 338)
        for restaurant in restaurants:
            self.assertEqual(
                MenuItem.objects.filter(category__restaurant=restaurant).count(),
                26,
            )
            self.assertEqual(
                restaurant.categories.aggregate(count=Count('items'))['count'],
                26,
            )

    def test_contact_page_shows_alfemo_and_approximate_terra_map_points(self):
        response = self.client.get(reverse('restaurant:contacts'))

        self.assertContains(response, 'contact-map-data')
        map_points = response.context['contact_map_data']
        self.assertEqual(map_points[0]['name'], 'Alfemo — ориентир')
        self.assertEqual(map_points[1]['name'], 'Terra — приблизительный адрес')

    def test_selected_language_is_remembered_on_the_next_page(self):
        self.client.get(reverse('restaurant:about'), {'language': 'en'})

        response = self.client.get(reverse('restaurant:menu'))

        self.assertEqual(response.context['site_language'], 'en')

    def test_restaurant_page_shows_its_own_dishes(self):
        owner = User.objects.create_user(username='menu-owner', password='TestPass-8542')
        restaurant = Restaurant.objects.create(
            owner=owner,
            name='Кафе Сад',
            slug='kafe-sad',
            cuisine='Домашняя кухня',
            description='Тест',
            address='Душанбе',
            latitude='38.559800',
            longitude='68.787000',
            is_approved=True,
        )
        category = MenuCategory.objects.create(restaurant=restaurant, name='Завтраки')
        MenuItem.objects.create(
            category=category,
            name='Овсяная каша',
            price='45.00',
            image_url='https://example.com/oatmeal.jpg',
        )

        response = self.client.get(
            reverse('restaurant:restaurant_detail', args=[restaurant.slug]),
        )

        self.assertContains(response, 'Завтраки')
        self.assertContains(response, 'Овсяная каша')
        self.assertContains(response, 'https://example.com/oatmeal.jpg')
        self.assertContains(response, 'Фотографии блюд — иллюстративные стоковые снимки')
        self.assertContains(response, '45')

    def test_all_menus_page_shows_each_restaurant_and_its_dish_photo(self):
        owner = User.objects.create_user(username='all-menu-owner', password='TestPass-8542')
        restaurant = Restaurant.objects.create(
            owner=owner,
            name='Кафе Сад',
            slug='kafe-sad-all-menus',
            cuisine='Домашняя кухня',
            description='Тест',
            address='Душанбе',
            latitude='38.559800',
            longitude='68.787000',
            is_approved=True,
        )
        category = MenuCategory.objects.create(restaurant=restaurant, name='Завтраки')
        MenuItem.objects.create(
            category=category,
            name='Овсяная каша',
            price='45.00',
            image_url='https://example.com/oatmeal.jpg',
        )

        response = self.client.get(reverse('restaurant:menu'))

        self.assertContains(response, 'Меню ресторанов')
        self.assertContains(response, 'Кафе Сад')
        self.assertContains(response, 'Овсяная каша')
        self.assertContains(response, 'https://example.com/oatmeal.jpg')

    def test_menu_page_has_filters_and_a_photo_for_each_dish(self):
        restaurant = Restaurant.objects.create(
            name='Кафе Меню',
            slug='kafe-menu',
            cuisine='Домашняя кухня',
            description='Тест',
            address='Душанбе',
            latitude='38.559800',
            longitude='68.787000',
            is_approved=True,
        )
        category = MenuCategory.objects.create(
            restaurant=restaurant,
            name='Завтраки',
        )
        MenuItem.objects.create(
            category=category,
            name='Овсяная каша',
            price='45.00',
            image_url='https://example.com/oatmeal.jpg',
            is_vegetarian=True,
        )

        response = self.client.get(reverse('restaurant:menu'))

        self.assertContains(response, 'data-menu-category-filter')
        self.assertContains(response, 'data-menu-price-filter')
        self.assertContains(response, 'data-menu-vegetarian-filter')
        self.assertContains(response, 'https://example.com/oatmeal.jpg')


class BookingRequestTests(TestCase):
    def setUp(self):
        owner = User.objects.create_superuser(
            username='booking-owner',
            email='booking-owner@example.com',
            password='TestPass-8542',
        )
        self.restaurant = Restaurant.objects.create(
            owner=owner,
            name='Тестовый ресторан',
            slug='test-booking-restaurant',
            cuisine='Тестовая кухня',
            description='Тест',
            address='Душанбе',
            latitude='38.559800',
            longitude='68.787000',
            is_approved=True,
        )

    def test_valid_booking_is_saved_as_a_request(self):
        response = self.client.post(
            reverse('restaurant:booking'),
            {
                'restaurant': self.restaurant.pk,
                'name': 'Амина',
                'phone': '+992 900 123 456',
                'booking_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'booking_time': '19:30',
                'guests': 3,
                'comments': '',
                'consent': 'on',
                'website': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(BookingRequest.objects.count(), 1)
        self.assertEqual(BookingRequest.objects.first().guests, 3)
        self.assertEqual(BookingRequest.objects.first().restaurant, self.restaurant)

    def test_booking_with_more_than_twelve_guests_is_not_saved(self):
        response = self.client.post(
            reverse('restaurant:booking'),
            {
                'restaurant': self.restaurant.pk,
                'name': 'Амина',
                'phone': '+992 900 123 456',
                'booking_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'booking_time': '19:30',
                'guests': 13,
                'comments': '',
                'consent': 'on',
                'website': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BookingRequest.objects.count(), 0)

    def test_booking_choices_only_include_managed_restaurants(self):
        unowned_restaurant = Restaurant.objects.create(
            name='Ресторан без владельца',
            slug='unowned-booking-place',
            description='Пока без владельца бронирований',
            address='Душанбе',
            latitude='38.559800',
            longitude='68.787000',
            is_approved=True,
        )

        response = self.client.get(reverse('restaurant:booking'))

        choices = list(response.context['form'].fields['restaurant'].queryset)
        self.assertIn(self.restaurant, choices)
        self.assertNotIn(unowned_restaurant, choices)

    def test_booking_in_the_past_is_not_saved(self):
        response = self.client.post(
            reverse('restaurant:booking'),
            {
                'restaurant': self.restaurant.pk,
                'name': 'Амина',
                'phone': '+992 900 123 456',
                'booking_date': (timezone.localdate() - timedelta(days=1)).isoformat(),
                'booking_time': '19:30',
                'guests': 3,
                'comments': '',
                'consent': 'on',
                'website': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BookingRequest.objects.count(), 0)

    def test_event_request_is_saved(self):
        response = self.client.post(
            reverse('restaurant:event_request'),
            {
                'name': 'Амина',
                'phone': '+992 900 123 456',
                'email': '',
                'event_date': (timezone.localdate() + timedelta(days=10)).isoformat(),
                'event_type': 'Семейный ужин',
                'guests': 15,
                'comments': '',
                'consent': 'on',
                'website': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(EventRequest.objects.count(), 1)


class OwnerAccountTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username='owner',
            email='owner@example.com',
            password='TestPass-8542',
        )
        self.other_owner = User.objects.create_superuser(
            username='other-owner',
            email='other-owner@example.com',
            password='TestPass-8542',
        )
        self.restaurant = Restaurant.objects.create(
            owner=self.owner,
            name='Мой ресторан',
            slug='my-owner-restaurant',
            cuisine='Домашняя кухня',
            description='Тестовое описание',
            address='Душанбе',
            latitude='38.559800',
            longitude='68.787000',
            is_approved=True,
        )
        self.other_restaurant = Restaurant.objects.create(
            owner=self.other_owner,
            name='Чужой ресторан',
            slug='other-owner-restaurant',
            cuisine='Другая кухня',
            description='Чужое тестовое описание',
            address='Душанбе',
            latitude='38.560000',
            longitude='68.788000',
            is_approved=True,
        )
        self.category = MenuCategory.objects.create(
            restaurant=self.restaurant,
            name='Основные блюда',
        )
        self.other_category = MenuCategory.objects.create(
            restaurant=self.other_restaurant,
            name='Чужая категория',
        )
        self.client.force_login(self.owner)

    def test_owner_dashboard_only_shows_their_restaurants(self):
        response = self.client.get(reverse('restaurant:dashboard'))

        self.assertContains(response, 'Мой ресторан')
        self.assertEqual(list(response.context['restaurants']), [self.restaurant])

    def test_owner_restaurant_form_uses_map_picker_and_uploaded_photo(self):
        response = self.client.get(reverse('restaurant:restaurant_add'))

        self.assertContains(response, 'data-location-picker')
        self.assertContains(response, 'name="latitude"', html=False)
        self.assertContains(response, 'name="longitude"', html=False)
        self.assertContains(response, 'name="image"', html=False)
        self.assertContains(response, 'type="file"', html=False)
        self.assertNotContains(response, 'name="image_url"', html=False)

    def test_owner_can_add_a_restaurant_that_waits_for_approval(self):
        response = self.client.post(
            reverse('restaurant:restaurant_add'),
            {
                'name': 'Новый семейный стол',
                'slug': 'novy-semeyny-stol',
                'cuisine': 'Домашняя кухня',
                'description': 'Новый ресторан',
                'address': 'Душанбе',
                'phone': '',
                'opening_hours': '',
                'latitude': '38.559800',
                'longitude': '68.787000',
                'image': make_test_image('restaurant.jpg'),
            },
        )

        self.assertEqual(response.status_code, 302)
        restaurant = Restaurant.objects.get(slug='novy-semeyny-stol')
        self.addCleanup(restaurant.image.delete, save=False)
        self.assertEqual(restaurant.owner, self.owner)
        self.assertFalse(restaurant.is_approved)
        self.assertTrue(restaurant.image.name.startswith('restaurants/'))
        self.assertTrue(restaurant.image.storage.exists(restaurant.image.name))
        self.assertTrue(restaurant.image.url.startswith('/media/restaurants/'))

    def test_owner_can_add_a_dish_to_their_category(self):
        response = self.client.post(
            reverse('restaurant:menu_item_add'),
            {
                'restaurant': self.restaurant.pk,
                'category': self.category.pk,
                'new_category': '',
                'name': 'Суп дня',
                'name_en': '',
                'description': 'Овощной суп',
                'description_en': '',
                'image': make_test_image('soup.jpg'),
                'price': '35.00',
                'allergens': '',
                'is_vegetarian': 'on',
                'is_available': 'on',
            },
        )

        self.assertEqual(response.status_code, 302)
        item = MenuItem.objects.get(category=self.category, name='Суп дня')
        self.addCleanup(item.image.delete, save=False)
        self.assertTrue(item.image.name.startswith('menu_items/'))

    def test_owner_dish_form_uploads_photo_instead_of_a_photo_url(self):
        response = self.client.get(reverse('restaurant:menu_item_add'))

        self.assertContains(response, 'name="restaurant"', html=False)
        self.assertContains(response, 'name="new_category"', html=False)
        self.assertContains(response, 'name="image"', html=False)
        self.assertContains(response, 'type="file"', html=False)
        self.assertNotContains(response, 'name="image_url"', html=False)

    def test_owner_cannot_add_a_dish_to_another_owners_category(self):
        response = self.client.post(
            reverse('restaurant:menu_item_add'),
            {
                'restaurant': self.restaurant.pk,
                'category': self.other_category.pk,
                'new_category': '',
                'name': 'Чужое блюдо',
                'name_en': '',
                'description': '',
                'description_en': '',
                'image': make_test_image('soup.jpg'),
                'price': '35.00',
                'allergens': '',
                'is_vegetarian': '',
                'is_available': 'on',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(MenuItem.objects.filter(name='Чужое блюдо').exists())

    def test_owner_can_add_a_dish_and_new_category_in_one_form(self):
        response = self.client.post(
            reverse('restaurant:menu_item_add'),
            {
                'restaurant': self.restaurant.pk,
                'category': '',
                'new_category': 'Домашние десерты',
                'name': 'Пирог с яблоком',
                'name_en': '',
                'description': 'Яблоки и тесто',
                'description_en': '',
                'image': make_test_image('pie.jpg'),
                'price': '25.00',
                'allergens': '',
                'is_vegetarian': 'on',
                'is_available': 'on',
            },
        )

        self.assertEqual(response.status_code, 302)
        item = MenuItem.objects.get(name='Пирог с яблоком')
        self.addCleanup(item.image.delete, save=False)
        self.assertEqual(item.category.name, 'Домашние десерты')
        self.assertEqual(item.category.restaurant, self.restaurant)

    def test_owner_cannot_add_a_restaurant_without_map_location(self):
        response = self.client.post(
            reverse('restaurant:restaurant_add'),
            {
                'name': 'Без адреса',
                'slug': 'bez-adresa',
                'cuisine': '',
                'description': 'Тест',
                'address': 'Душанбе',
                'phone': '',
                'opening_hours': '',
                'latitude': '',
                'longitude': '',
                'image': make_test_image('restaurant.jpg'),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Restaurant.objects.filter(slug='bez-adresa').exists())


    def test_registration_creates_a_regular_account_without_owner_privileges(self):
        self.client.logout()

        response = self.client.post(
            reverse('restaurant:register'),
            {
                'username': 'new-owner',
                'email': 'new-owner@example.com',
                'password1': 'Safe-password-8345!',
                'password2': 'Safe-password-8345!',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='new-owner').exists())
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(User.objects.get(username='new-owner').is_superuser)

    def test_regular_account_cannot_open_owner_dashboard(self):
        self.client.logout()
        regular_user = User.objects.create_user(
            username='regular-user',
            password='TestPass-8542',
        )
        self.client.force_login(regular_user)

        response = self.client.get(reverse('restaurant:dashboard'))

        self.assertEqual(response.status_code, 403)

    def test_owner_cannot_open_another_owners_booking(self):
        booking = BookingRequest.objects.create(
            restaurant=self.other_restaurant,
            name='Гость',
            phone='+992 900 000 000',
            booking_date=timezone.localdate() + timedelta(days=1),
            booking_time='19:00',
            guests=2,
        )

        response = self.client.get(
            reverse('restaurant:booking_status', args=[booking.pk]),
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_add_and_disable_their_own_table(self):
        response = self.client.post(
            reverse('restaurant:table_manage'),
            {
                'restaurant': self.restaurant.pk,
                'name': 'Стол 1',
                'capacity': 4,
            },
        )
        self.assertEqual(response.status_code, 302)
        table = RestaurantTable.objects.get(restaurant=self.restaurant)
        self.assertEqual(table.capacity, 4)

        response = self.client.post(
            reverse('restaurant:table_toggle', args=[table.pk]),
        )

        self.assertEqual(response.status_code, 302)
        table.refresh_from_db()
        self.assertFalse(table.is_active)

    def test_owner_cannot_manage_another_restaurants_table(self):
        table = RestaurantTable.objects.create(
            restaurant=self.other_restaurant,
            name='Чужой стол',
            capacity=4,
        )

        response = self.client.post(
            reverse('restaurant:table_toggle', args=[table.pk]),
        )

        self.assertEqual(response.status_code, 404)
        table.refresh_from_db()
        self.assertTrue(table.is_active)

    def test_owner_can_confirm_booking_at_a_free_suitable_table(self):
        table = RestaurantTable.objects.create(
            restaurant=self.restaurant,
            name='У окна',
            capacity=4,
        )
        booking = BookingRequest.objects.create(
            restaurant=self.restaurant,
            name='Гость',
            phone='+992 900 000 000',
            booking_date=timezone.localdate() + timedelta(days=1),
            booking_time='19:00',
            guests=3,
        )

        response = self.client.post(
            reverse('restaurant:booking_status', args=[booking.pk]),
            {'status': 'confirmed', 'table': table.pk, 'owner_note': 'Ждём вас'},
        )

        self.assertRedirects(response, reverse('restaurant:booking_manage'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(booking.table, table)
        self.assertEqual(booking.owner_note, 'Ждём вас')

    def test_confirmed_booking_blocks_table_for_overlapping_time(self):
        table = RestaurantTable.objects.create(
            restaurant=self.restaurant,
            name='У окна',
            capacity=4,
        )
        booking_date = timezone.localdate() + timedelta(days=1)
        BookingRequest.objects.create(
            restaurant=self.restaurant,
            table=table,
            name='Первый гость',
            phone='+992 900 000 000',
            booking_date=booking_date,
            booking_time='19:00',
            guests=3,
            status='confirmed',
        )
        second_booking = BookingRequest.objects.create(
            restaurant=self.restaurant,
            name='Второй гость',
            phone='+992 900 000 001',
            booking_date=booking_date,
            booking_time='20:00',
            guests=2,
        )

        response = self.client.get(
            reverse('restaurant:booking_status', args=[second_booking.pk]),
        )

        self.assertFalse(
            response.context['form'].fields['table'].queryset.filter(
                pk=table.pk,
            ).exists(),
        )

    def test_confirmed_booking_blocks_table_until_owner_marks_guests_departed(self):
        table = RestaurantTable.objects.create(
            restaurant=self.restaurant,
            name='Стол у окна',
            capacity=4,
        )
        booking_date = timezone.localdate() + timedelta(days=1)
        booking = BookingRequest.objects.create(
            restaurant=self.restaurant,
            table=table,
            name='Гости',
            phone='+992 900 000 000',
            booking_date=booking_date,
            booking_time='19:00',
            guests=2,
            status='confirmed',
        )
        later_booking = BookingRequest.objects.create(
            restaurant=self.restaurant,
            name='Следующие гости',
            phone='+992 900 000 001',
            booking_date=booking_date,
            booking_time='23:00',
            guests=2,
        )

        response = self.client.get(
            reverse('restaurant:booking_status', args=[later_booking.pk]),
        )
        self.assertFalse(
            response.context['form'].fields['table'].queryset.filter(
                pk=table.pk,
            ).exists(),
        )

        response = self.client.post(
            reverse('restaurant:booking_release_table', args=[booking.pk]),
        )
        self.assertRedirects(response, reverse('restaurant:booking_manage'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'completed')
        self.assertEqual(booking.table, table)

        response = self.client.get(
            reverse('restaurant:booking_status', args=[later_booking.pk]),
        )
        self.assertTrue(
            response.context['form'].fields['table'].queryset.filter(
                pk=table.pk,
            ).exists(),
        )

    def test_owner_cannot_confirm_without_assigning_table(self):
        booking = BookingRequest.objects.create(
            restaurant=self.restaurant,
            name='Гость',
            phone='+992 900 000 000',
            booking_date=timezone.localdate() + timedelta(days=1),
            booking_time='19:00',
            guests=2,
        )

        response = self.client.post(
            reverse('restaurant:booking_status', args=[booking.pk]),
            {'status': 'confirmed', 'table': '', 'owner_note': ''},
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'new')
        self.assertIsNone(booking.table)


class ModerationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='moderator',
            email='moderator@example.com',
            password='TestPass-8542',
        )
        self.owner = User.objects.create_user(
            username='pending-owner',
            password='TestPass-8542',
        )
        self.restaurant = Restaurant.objects.create(
            owner=self.owner,
            name='Новый ресторан',
            slug='moderation-new-restaurant',
            description='Проверить публикацию',
            address='Душанбе',
            latitude='38.559800',
            longitude='68.787000',
            is_approved=False,
        )

    def test_superuser_can_review_and_approve_a_restaurant(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('restaurant:moderation'))

        self.assertContains(response, self.restaurant.name)
        response = self.client.post(
            reverse('restaurant:moderation_action', args=[self.restaurant.pk]),
            {'action': 'approve'},
        )
        self.assertRedirects(response, reverse('restaurant:moderation'))
        self.restaurant.refresh_from_db()
        self.assertTrue(self.restaurant.is_approved)

    def test_superuser_rejection_requires_and_saves_a_reason(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('restaurant:moderation_action', args=[self.restaurant.pk]),
            {'action': 'reject', 'moderation_note': ''},
        )
        self.assertRedirects(response, reverse('restaurant:moderation'))
        self.restaurant.refresh_from_db()
        self.assertFalse(self.restaurant.is_approved)
        self.assertEqual(self.restaurant.moderation_note, '')

        self.client.post(
            reverse('restaurant:moderation_action', args=[self.restaurant.pk]),
            {'action': 'reject', 'moderation_note': 'Добавьте номер телефона.'},
        )
        self.restaurant.refresh_from_db()
        self.assertEqual(
            self.restaurant.moderation_note,
            'Добавьте номер телефона.',
        )

    def test_regular_account_cannot_open_moderation(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('restaurant:moderation'))

        self.assertEqual(response.status_code, 403)
