from django.contrib import admin

from .models import AddOn, Booking, Category, Review, Venue, WishlistItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "category", "price_per_hour")
    list_filter = ("city", "category")
    search_fields = ("name", "city")


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ("name", "venue", "price")
    search_fields = ("name", "venue__name")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "venue", "created_at")
    list_filter = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("venue", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("venue__name", "user__username")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "venue", "user", "date", "status", "grand_total")
    list_filter = ("status", "date")
    search_fields = ("venue__name", "user__username")
    autocomplete_fields = ("venue", "user", "addons")
