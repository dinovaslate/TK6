from django.urls import path

from . import views

urlpatterns = [
    path("", views.redirect_to_login, name="root"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("home/", views.home_view, name="home"),
    path("catalog/", views.catalog_view, name="catalog"),
    path("venue/<int:pk>/", views.venue_detail_view, name="venue_detail"),
    path("venue/<int:pk>/book/", views.booking_view, name="booking"),
    path("venue/<int:pk>/add-review/", views.add_review, name="add_review"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/toggle/<int:venue_id>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("booking/<int:pk>/payment/", views.booking_payment_view, name="booking_payment"),
    path("booking/<int:pk>/success/", views.booking_success_view, name="booking_success"),
]
