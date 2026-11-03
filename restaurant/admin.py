from django.contrib import admin

from .models import (
    BookingRequest,
    EventRequest,
    GalleryImage,
    MenuCategory,
    MenuItem,
    Restaurant,
    RestaurantTable,
    SiteSettings,
)


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'name_en', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    inlines = [MenuItemInline]


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'cuisine', 'is_approved']
    list_filter = ['is_approved', 'cuisine']
    search_fields = ['name', 'address', 'owner__username']
    list_editable = ['is_approved']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'order']
    list_filter = ['category', 'is_available', 'is_vegetarian']
    search_fields = ['name', 'name_en', 'description']
    list_editable = ['is_available', 'order']


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'capacity', 'is_active']
    list_filter = ['restaurant', 'is_active']
    search_fields = ['name', 'restaurant__name']
    list_editable = ['is_active']


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'alt_text', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['address', 'phone', 'restaurant_hours']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'restaurant',
        'phone',
        'booking_date',
        'booking_time',
        'guests',
        'status',
    ]
    list_filter = ['status', 'booking_date']
    search_fields = ['name', 'phone']
    list_editable = ['status']
    readonly_fields = ['created_at']


@admin.register(EventRequest)
class EventRequestAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'restaurant',
        'phone',
        'event_date',
        'event_type',
        'guests',
        'created_at',
    ]
    list_filter = ['event_date', 'event_type']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at']
