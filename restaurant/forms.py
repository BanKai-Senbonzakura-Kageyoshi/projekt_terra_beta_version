from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

from .models import (
    BookingRequest,
    EventRequest,
    MenuCategory,
    MenuItem,
    Restaurant,
    RestaurantTable,
    DUSHANBE_LATITUDE_RANGE,
    DUSHANBE_LONGITUDE_RANGE,
)


class RestaurantMenuCategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.restaurant.name} — {obj.name}'


class SpamProtectedForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
    )
    consent = forms.BooleanField(
        required=True,
        label='Я согласен(на) с политикой обработки персональных данных.',
    )

    def clean_website(self):
        value = self.cleaned_data.get('website')
        if value:
            raise forms.ValidationError('Не удалось отправить форму.')
        return value

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = ''.join(character for character in phone if character.isdigit())
        if len(digits) < 7 or len(digits) > 15:
            raise forms.ValidationError('Введите корректный номер телефона.')
        return phone


class BookingRequestForm(SpamProtectedForm):
    restaurant = forms.ModelChoiceField(
        queryset=Restaurant.objects.filter(
            is_approved=True,
            owner__is_superuser=True,
            latitude__range=DUSHANBE_LATITUDE_RANGE,
            longitude__range=DUSHANBE_LONGITUDE_RANGE,
        ),
        label='Выберите ресторан',
        empty_label='Выберите ресторан',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )

    class Meta:
        model = BookingRequest
        fields = [
            'restaurant',
            'name',
            'phone',
            'booking_date',
            'booking_time',
            'guests',
            'comments',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name', 'class': 'form-input'}),
            'phone': forms.TelInput(attrs={
                'autocomplete': 'tel',
                'placeholder': '+992 ...',
                'class': 'form-input',
            }),
            'booking_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'data-date-field': '',
            }),
            'booking_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'guests': forms.NumberInput(attrs={
                'min': 1,
                'max': 12,
                'class': 'form-input',
            }),
            'comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }

    def clean_booking_date(self):
        booking_date = self.cleaned_data['booking_date']
        if booking_date < timezone.localdate():
            raise forms.ValidationError('Нельзя выбрать дату в прошлом.')
        return booking_date


class EventRequestForm(SpamProtectedForm):
    class Meta:
        model = EventRequest
        fields = ['name', 'phone', 'email', 'event_date', 'event_type', 'guests', 'comments']
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name', 'class': 'form-input'}),
            'phone': forms.TelInput(attrs={
                'autocomplete': 'tel',
                'placeholder': '+992 ...',
                'class': 'form-input',
            }),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-input'}),
            'event_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'data-date-field': '',
            }),
            'event_type': forms.TextInput(attrs={'class': 'form-input'}),
            'guests': forms.NumberInput(attrs={
                'min': 1,
                'max': 500,
                'class': 'form-input',
            }),
            'comments': forms.Textarea(attrs={'rows': 4, 'class': 'form-input'}),
        }

    def clean_event_date(self):
        event_date = self.cleaned_data['event_date']
        if event_date < timezone.localdate():
            raise forms.ValidationError('Нельзя выбрать дату в прошлом.')
        return event_date


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Электронная почта',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'autocomplete': 'email'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'


class RestaurantForm(forms.ModelForm):
    slug = forms.SlugField(
        required=False,
        label='Короткий адрес страницы (необязательно)',
        help_text='Можно оставить пустым — он создастся из названия.',
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )

    class Meta:
        model = Restaurant
        fields = [
            'name',
            'slug',
            'cuisine',
            'description',
            'address',
            'phone',
            'opening_hours',
            'latitude',
            'longitude',
            'image',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'slug': forms.TextInput(attrs={'class': 'form-input'}),
            'cuisine': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'address': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TelInput(attrs={'class': 'form-input'}),
            'opening_hours': forms.TextInput(attrs={'class': 'form-input'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
                'data-image-preview': '',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cuisine'].required = False
        self.fields['image'].required = True

    def clean_latitude(self):
        latitude = self.cleaned_data['latitude']
        minimum, maximum = map(Decimal, DUSHANBE_LATITUDE_RANGE)
        if not minimum <= latitude <= maximum:
            raise forms.ValidationError('Выберите место внутри Душанбе на карте.')
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data['longitude']
        minimum, maximum = map(Decimal, DUSHANBE_LONGITUDE_RANGE)
        if not minimum <= longitude <= maximum:
            raise forms.ValidationError('Выберите место внутри Душанбе на карте.')
        return longitude

    def clean_slug(self):
        slug = self.cleaned_data.get('slug') or slugify(
            self.cleaned_data.get('name', ''),
            allow_unicode=True,
        )
        if not slug:
            raise forms.ValidationError('Добавьте короткий адрес страницы.')
        existing_restaurants = Restaurant.objects.filter(slug=slug)
        if self.instance.pk:
            existing_restaurants = existing_restaurants.exclude(pk=self.instance.pk)
        if existing_restaurants.exists():
            raise forms.ValidationError('Такой адрес уже занят. Укажите другой.')
        return slug


class MenuItemForm(forms.ModelForm):
    restaurant = forms.ModelChoiceField(
        queryset=Restaurant.objects.none(),
        label='Ресторан',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    category = RestaurantMenuCategoryChoiceField(
        queryset=MenuCategory.objects.none(),
        required=False,
        label='Существующая категория',
        empty_label='Выберите категорию или создайте новую ниже',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    new_category = forms.CharField(
        required=False,
        max_length=100,
        label='Новая категория',
        help_text='Заполните только если такой категории ещё нет.',
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )

    class Meta:
        model = MenuItem
        fields = [
            'name',
            'name_en',
            'description',
            'description_en',
            'image',
            'price',
            'allergens',
            'is_vegetarian',
            'is_available',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'name_en': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'description_en': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
                'data-image-preview': '',
            }),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'allergens': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = True
        if user is not None:
            restaurants = Restaurant.objects.filter(owner=user)
            self.fields['restaurant'].queryset = restaurants
            if not self.is_bound and restaurants.count() == 1:
                self.initial['restaurant'] = restaurants.get().pk
            self.fields['category'].queryset = MenuCategory.objects.filter(
                restaurant__owner=user,
            )
        self.order_fields([
            'restaurant',
            'category',
            'new_category',
            'name',
            'name_en',
            'description',
            'description_en',
            'image',
            'price',
            'allergens',
            'is_vegetarian',
            'is_available',
        ])

    def clean(self):
        cleaned_data = super().clean()
        restaurant = cleaned_data.get('restaurant')
        category = cleaned_data.get('category')
        new_category = cleaned_data.get('new_category', '').strip()
        if category and restaurant and category.restaurant_id != restaurant.pk:
            self.add_error('category', 'Выберите категорию этого ресторана.')
        if category and new_category:
            self.add_error(
                'new_category',
                'Выберите существующую категорию или укажите новую, но не обе.',
            )
        elif not category and not new_category:
            self.add_error(
                'new_category',
                'Выберите категорию или укажите название новой категории.',
            )
        cleaned_data['new_category'] = new_category
        return cleaned_data


class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ['name', 'name_en', 'order']
        widgets = {
            'name': forms.TextInput({
                'class': 'form-input',
                'list': 'menu-category-suggestions',
            }),
            'name_en': forms.TextInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class BookingDecisionForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ('confirmed', 'Подтвердить бронь'),
            ('rejected', 'Отклонить заявку'),
            ('closed', 'Закрыть бронь'),
        ],
        label='Решение',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    table = forms.ModelChoiceField(
        queryset=RestaurantTable.objects.none(),
        required=False,
        label='Столик',
        empty_label='Выберите свободный столик',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    owner_note = forms.CharField(
        required=False,
        label='Комментарий клиенту',
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
    )

    def __init__(self, *args, booking, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking
        self.fields['table'].queryset = self.get_available_tables()

    def get_available_tables(self):
        booking = self.booking
        tables = RestaurantTable.objects.filter(
            restaurant=booking.restaurant,
            is_active=True,
            capacity__gte=booking.guests,
        )
        overlapping_bookings = BookingRequest.objects.filter(
            restaurant=booking.restaurant,
            status='confirmed',
            table__in=tables,
            booking_date=booking.booking_date,
        ).exclude(pk=booking.pk).select_related('table')
        busy_table_ids = overlapping_bookings.values_list('table_id', flat=True)
        return tables.exclude(pk__in=busy_table_ids)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        table = cleaned_data.get('table')
        if status == 'confirmed' and table is None:
            self.add_error('table', 'Для подтверждения выберите свободный столик.')
        if status != 'confirmed' and table is not None:
            cleaned_data['table'] = None
        return cleaned_data


class RestaurantTableForm(forms.ModelForm):
    class Meta:
        model = RestaurantTable
        fields = ['restaurant', 'name', 'capacity']
        widgets = {
            'restaurant': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 20,
            }),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['restaurant'].queryset = Restaurant.objects.filter(owner=user)
