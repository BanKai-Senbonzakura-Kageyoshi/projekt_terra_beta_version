from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    View,
)

from .forms import (
    BookingRequestForm,
    BookingDecisionForm,
    EventRequestForm,
    MenuCategoryForm,
    MenuItemForm,
    RegisterForm,
    RestaurantForm,
    RestaurantTableForm,
)
from .models import (
    BookingRequest,
    GalleryImage,
    MenuCategory,
    MenuItem,
    Restaurant,
    RestaurantTable,
    SiteSettings,
    DUSHANBE_LATITUDE_RANGE,
    DUSHANBE_LONGITUDE_RANGE,
)


def save_language_in_session(request):
    """Запоминает выбранный язык и добавляет его к запросу."""
    language = request.GET.get('language')
    if language in ('ru', 'en'):
        request.session['language'] = language

    request.language = request.session.get('language', 'ru')


def get_shared_context(request):
    """Возвращает данные, которые нужны шаблонам сайта на каждой странице."""
    return {
        'site_settings': SiteSettings.objects.first(),
        'site_language': request.language,
        'booking_form': BookingRequestForm(),
    }


class SiteContextMixin:
    """Добавляет общий контекст и язык всем страницам сайта."""

    def dispatch(self, request, *args, **kwargs):
        save_language_in_session(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_shared_context(self.request))
        return context


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ограничивает владельческий и модераторский кабинеты superuser-аккаунтами."""

    login_url = 'restaurant:login'

    def test_func(self):
        return self.request.user.is_superuser


class HomePageView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurants = Restaurant.objects.filter(
            is_approved=True,
            latitude__range=DUSHANBE_LATITUDE_RANGE,
            longitude__range=DUSHANBE_LONGITUDE_RANGE,
        )
        context['restaurant_count'] = restaurants.count()
        context['dish_count'] = MenuItem.objects.filter(
            category__restaurant__in=restaurants,
        ).count()
        context['category_count'] = (
            MenuCategory.objects.filter(
                restaurant__in=restaurants,
                is_active=True,
            )
            .values('name')
            .distinct()
            .count()
        )
        context['featured_restaurants'] = restaurants[:3]
        context['gallery_images'] = GalleryImage.objects.filter(
            is_active=True,
        )[:4]
        return context


class RestaurantListView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/restaurants.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurants'] = Restaurant.objects.filter(
            is_approved=True,
            latitude__range=DUSHANBE_LATITUDE_RANGE,
            longitude__range=DUSHANBE_LONGITUDE_RANGE,
        )
        context['cuisines'] = (
            context['restaurants']
            .values_list('cuisine', flat=True)
            .distinct()
            .exclude(cuisine='')
            .order_by('cuisine')
        )
        context['restaurant_map_data'] = [
            {
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address,
                'cuisine': restaurant.cuisine,
                'url': reverse('restaurant:restaurant_detail', args=[restaurant.slug]),
                'latitude': float(restaurant.latitude),
                'longitude': float(restaurant.longitude),
            }
            for restaurant in context['restaurants']
        ]
        return context


class RestaurantDetailView(SiteContextMixin, DetailView):
    model = Restaurant
    template_name = 'restaurant/restaurant_detail.html'
    context_object_name = 'restaurant'

    def get_queryset(self):
        return Restaurant.objects.filter(is_approved=True).prefetch_related(
            'categories__items',
        )


class RegisterView(SiteContextMixin, FormView):
    form_class = RegisterForm
    template_name = 'restaurant/register.html'

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            'Аккаунт создан. Для доступа владельца попросите администратора выдать права суперпользователя.',
        )
        return redirect('restaurant:login')


class OwnerLoginView(SiteContextMixin, auth_views.LoginView):
    template_name = 'restaurant/login.html'

    def form_valid(self, form):
        if not form.get_user().is_superuser:
            form.add_error(
                None,
                'Доступ к кабинету ресторана есть только у аккаунтов владельцев, '
                'которые создал или подтвердил администратор.',
            )
            return self.form_invalid(form)
        return super().form_valid(form)


class OwnerDashboardView(SuperuserRequiredMixin, SiteContextMixin, ListView):
    model = Restaurant
    template_name = 'restaurant/dashboard.html'
    context_object_name = 'restaurants'

    def get_queryset(self):
        return Restaurant.objects.filter(owner=self.request.user)


class RestaurantCreateView(SuperuserRequiredMixin, SiteContextMixin, CreateView):
    form_class = RestaurantForm
    template_name = 'restaurant/restaurant_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.is_approved = False
        form.instance.moderation_note = ''
        messages.success(
            self.request,
            'Ресторан отправлен на модерацию. Он появится в каталоге после проверки.',
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('restaurant:dashboard')


class MenuManageView(SuperuserRequiredMixin, SiteContextMixin, TemplateView):
    template_name = 'restaurant/menu_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurants'] = Restaurant.objects.filter(owner=self.request.user)
        context['categories'] = (
            MenuCategory.objects.filter(restaurant__owner=self.request.user)
            .prefetch_related('items')
        )
        return context


class MenuCategoryCreateView(SuperuserRequiredMixin, SiteContextMixin, CreateView):
    form_class = MenuCategoryForm
    template_name = 'restaurant/category_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.restaurant = get_object_or_404(
            Restaurant,
            pk=kwargs['restaurant_id'],
            owner=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.restaurant = self.restaurant
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('restaurant:menu_manage')


class MenuItemCreateView(SuperuserRequiredMixin, SiteContextMixin, CreateView):
    form_class = MenuItemForm
    template_name = 'restaurant/menu_item_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            item = form.save(commit=False)
            category = form.cleaned_data['category']
            if category is None:
                category = MenuCategory.objects.create(
                    restaurant=form.cleaned_data['restaurant'],
                    name=form.cleaned_data['new_category'],
                )
            item.category = category
            item.save()
        messages.success(self.request, 'Блюдо добавлено в меню.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('restaurant:menu_manage')


class BookingManageView(SuperuserRequiredMixin, SiteContextMixin, ListView):
    model = BookingRequest
    template_name = 'restaurant/booking_manage.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return BookingRequest.objects.filter(
            restaurant__owner=self.request.user,
        ).select_related('restaurant', 'table')


class BookingDecisionView(SuperuserRequiredMixin, SiteContextMixin, FormView):
    form_class = BookingDecisionForm
    template_name = 'restaurant/booking_status_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(
            BookingRequest.objects.select_related('restaurant', 'table').filter(
                restaurant__owner=request.user,
            ),
            pk=kwargs['pk'],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['booking'] = self.booking
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking'] = self.booking
        form = context.get('form')
        if form is not None:
            context['table_count'] = form.fields['table'].queryset.count()
        return context

    def form_valid(self, form):
        with transaction.atomic():
            booking = get_object_or_404(
                BookingRequest.objects.select_for_update().filter(
                    restaurant__owner=self.request.user,
                ),
                pk=self.booking.pk,
            )
            status = form.cleaned_data['status']
            table = form.cleaned_data['table']
            if status == 'confirmed':
                if not form.get_available_tables().filter(pk=table.pk).exists():
                    form.add_error(
                        'table',
                        'Столик уже занят или больше не подходит для этой брони.',
                    )
                    return self.form_invalid(form)
                booking.table = table
            else:
                booking.table = None
            booking.status = status
            booking.owner_note = form.cleaned_data['owner_note']
            booking.save(update_fields=['table', 'status', 'owner_note'])
        messages.success(self.request, 'Решение по бронированию сохранено.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('restaurant:booking_manage')


class BookingReleaseTableView(SuperuserRequiredMixin, SiteContextMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(
            BookingRequest.objects.filter(
                restaurant__owner=request.user,
                status='confirmed',
                table__isnull=False,
            ),
            pk=pk,
        )
        booking.status = 'completed'
        booking.save(update_fields=['status'])
        messages.success(
            request,
            f'Столик {booking.table.name} снова доступен для бронирования.',
        )
        return redirect('restaurant:booking_manage')


class TableManageView(SuperuserRequiredMixin, SiteContextMixin, TemplateView):
    template_name = 'restaurant/table_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurants'] = Restaurant.objects.filter(owner=self.request.user)
        context['tables'] = RestaurantTable.objects.filter(
            restaurant__owner=self.request.user,
        ).select_related('restaurant')
        context['form'] = RestaurantTableForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        form = RestaurantTableForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Столик добавлен.')
            return redirect('restaurant:table_manage')
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class RestaurantTableToggleView(SuperuserRequiredMixin, SiteContextMixin, View):
    def post(self, request, pk):
        table = get_object_or_404(
            RestaurantTable,
            pk=pk,
            restaurant__owner=request.user,
        )
        table.is_active = not table.is_active
        table.save(update_fields=['is_active'])
        messages.success(request, 'Доступность столика обновлена.')
        return redirect('restaurant:table_manage')


class RestaurantModerationView(SuperuserRequiredMixin, SiteContextMixin, TemplateView):
    template_name = 'restaurant/moderation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = Restaurant.objects.filter(owner__isnull=False).select_related(
            'owner',
        )
        context['pending_restaurants'] = submissions.filter(
            is_approved=False,
            moderation_note='',
        )
        context['rejected_restaurants'] = submissions.exclude(moderation_note='')
        context['pending_count'] = context['pending_restaurants'].count()
        return context


class RestaurantModerationActionView(SuperuserRequiredMixin, SiteContextMixin, View):
    def post(self, request, pk):
        restaurant = get_object_or_404(
            Restaurant,
            pk=pk,
            owner__isnull=False,
            is_approved=False,
        )
        action = request.POST.get('action')
        note = request.POST.get('moderation_note', '').strip()
        if action == 'approve':
            restaurant.is_approved = True
            restaurant.moderation_note = ''
            message = 'Ресторан одобрен и опубликован.'
        elif action == 'reject' and note:
            restaurant.is_approved = False
            restaurant.moderation_note = note
            message = 'Ресторан отклонён. Комментарий сохранён.'
        else:
            messages.error(request, 'Для отклонения укажите причину.')
            return redirect('restaurant:moderation')
        restaurant.save(update_fields=['is_approved', 'moderation_note'])
        messages.success(request, message)
        return redirect('restaurant:moderation')


class AboutPageView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/about.html'


class MenuPageView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/menu.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurants'] = (
            Restaurant.objects.filter(
                is_approved=True,
                latitude__range=DUSHANBE_LATITUDE_RANGE,
                longitude__range=DUSHANBE_LONGITUDE_RANGE,
            )
            .prefetch_related('categories__items')
        )
        category_choices = (
            MenuCategory.objects.filter(
                restaurant__in=context['restaurants'],
                is_active=True,
            )
            .values_list('name', 'name_en')
            .distinct()
            .order_by('name')
        )
        context['menu_filter_categories'] = [
            {
                'value': name,
                'label': name_en if self.request.language == 'en' and name_en else name,
            }
            for name, name_en in category_choices
        ]
        return context


class EventsPageView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/events.html'


class GalleryPageView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/gallery.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gallery_images'] = GalleryImage.objects.filter(is_active=True)
        return context


class ContactPageView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        map_points = [
            {
                'kind': 'reference',
                'name': 'Alfemo — ориентир',
                'address': 'Улица Бухоро. Точка отмечена в OpenStreetMap.',
                'latitude': 38.5686582,
                'longitude': 68.7850622,
                'url': 'https://www.openstreetmap.org/node/5599650121',
            },
            {
                'kind': 'terra',
                'name': 'Terra — приблизительный адрес',
                'address': 'Район улицы Турсунзода, 24. Точное место уточните у ресторана.',
                'latitude': 38.5714485,
                'longitude': 68.7968311,
            },
        ]
        nearby_restaurants = Restaurant.objects.filter(
            is_approved=True,
            latitude__range=('38.55', '38.59'),
            longitude__range=('68.76', '68.81'),
        )
        for restaurant in nearby_restaurants:
            map_points.append(
                {
                    'kind': 'restaurant',
                    'id': restaurant.id,
                    'name': restaurant.name,
                    'address': restaurant.address,
                    'latitude': float(restaurant.latitude),
                    'longitude': float(restaurant.longitude),
                    'url': reverse(
                        'restaurant:restaurant_detail',
                        args=[restaurant.slug],
                    ),
                },
            )
        context['contact_map_data'] = map_points
        return context


class BookingCreateView(SiteContextMixin, CreateView):
    form_class = BookingRequestForm
    template_name = 'restaurant/booking.html'

    def form_valid(self, form):
        booking = form.save(commit=False)
        booking.language = self.request.language
        messages.success(self.request, 'Заявка сохранена.')
        return super().form_valid(form)

    def get_success_url(self):
        return f'{reverse("restaurant:thank_you")}?type=booking'


class EventRequestCreateView(SiteContextMixin, CreateView):
    form_class = EventRequestForm
    template_name = 'restaurant/events.html'

    def form_valid(self, form):
        event_request = form.save(commit=False)
        event_request.language = self.request.language
        messages.success(self.request, 'Заявка сохранена.')
        return super().form_valid(form)

    def get_success_url(self):
        return f'{reverse("restaurant:thank_you")}?type=event'


class ThankYouView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/thank_you.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_type'] = self.request.GET.get('type', 'booking')
        return context


class PrivacyPageView(SiteContextMixin, TemplateView):
    template_name = 'restaurant/privacy.html'
