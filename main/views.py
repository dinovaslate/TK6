from __future__ import annotations

from typing import Iterable

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db.models import Count, Prefetch

from .forms import BookingForm, LoginForm, PaymentForm, RegisterForm, ReviewForm
from .models import Booking, Review, Venue, WishlistItem


def _apply_filters(queryset: Iterable[Venue], request: HttpRequest):
    city = request.GET.get("city")
    category = request.GET.get("category")
    max_price = request.GET.get("max_price")
    if city:
        queryset = queryset.filter(city__iexact=city)
    if category:
        queryset = queryset.filter(category__name__iexact=category)
    if max_price:
        try:
            queryset = queryset.filter(price_per_hour__lte=float(max_price))
        except ValueError:
            pass
    return queryset


def redirect_to_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")
    return redirect("login")


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        login(request, user)
        messages.success(request, f"Welcome back, {user.username}!")
        return redirect("home")

    return render(request, "main/auth/login.html", {"form": form})


def register_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Registration successful. Please log in.")
        return redirect("login")

    return render(request, "main/auth/register.html", {"form": form})


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    messages.info(request, "You have been logged out.")
    logout(request)
    return redirect("login")


@login_required
def home_view(request: HttpRequest) -> HttpResponse:
    venues = Venue.objects.select_related("category").annotate(booking_count=Count("bookings"))
    filtered_venues = _apply_filters(venues, request)

    popular_venues = (
        filtered_venues.order_by("-booking_count", "name")[:3]
        if request.GET
        else venues.order_by("-booking_count", "name")[:3]
    )

    context = {
        "popular_venues": popular_venues,
        "filters": {
            "city": request.GET.get("city", ""),
            "category": request.GET.get("category", ""),
            "max_price": request.GET.get("max_price", ""),
        },
        "available_cities": Venue.objects.values_list("city", flat=True).distinct().order_by("city"),
        "available_categories": Venue.objects.values_list("category__name", flat=True).distinct().order_by("category__name"),
    }
    return render(request, "main/home.html", context)


@login_required
def catalog_view(request: HttpRequest) -> HttpResponse:
    venues = (
        Venue.objects.select_related("category")
        .prefetch_related("addons")
        .annotate(booking_count=Count("bookings"))
    )
    venues = _apply_filters(venues, request)
    context = {
        "venues": venues,
        "filters": {
            "city": request.GET.get("city", ""),
            "category": request.GET.get("category", ""),
            "max_price": request.GET.get("max_price", ""),
        },
        "available_cities": Venue.objects.values_list("city", flat=True).distinct().order_by("city"),
        "available_categories": Venue.objects.values_list("category__name", flat=True).distinct().order_by("category__name"),
    }
    return render(request, "main/catalog.html", context)


@login_required
def venue_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    venue = (
        Venue.objects.select_related("category")
        .prefetch_related("addons", Prefetch("reviews", queryset=Review.objects.select_related("user")))
        .annotate(booking_count=Count("bookings"))
        .get(pk=pk)
    )
    review_form = ReviewForm()
    is_wishlisted = WishlistItem.objects.filter(user=request.user, venue=venue).exists()
    context = {
        "venue": venue,
        "review_form": review_form,
        "is_wishlisted": is_wishlisted,
    }
    return render(request, "main/venue_detail.html", context)


@login_required
@require_POST
def add_review(request: HttpRequest, pk: int) -> HttpResponse:
    venue = get_object_or_404(Venue, pk=pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        Review.objects.create(
            user=request.user,
            venue=venue,
            rating=form.cleaned_data["rating"],
            comment=form.cleaned_data["comment"],
        )
        messages.success(request, "Review added successfully.")
    else:
        messages.error(request, "Could not add review. Please check the form and try again.")
    return redirect("venue_detail", pk=venue.pk)


@login_required
@require_POST
def wishlist_toggle(request: HttpRequest, venue_id: int) -> HttpResponse:
    venue = get_object_or_404(Venue, pk=venue_id)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, venue=venue)
    if not created:
        wishlist_item.delete()
        messages.info(request, f"Removed {venue.name} from your wishlist.")
    else:
        messages.success(request, f"Added {venue.name} to your wishlist.")
    next_url = request.POST.get("next") or reverse("home")
    return redirect(next_url)


@login_required
def wishlist_view(request: HttpRequest) -> HttpResponse:
    items = WishlistItem.objects.select_related("venue", "venue__category").filter(user=request.user)
    return render(request, "main/wishlist.html", {"items": items})


@login_required
def booking_view(request: HttpRequest, pk: int) -> HttpResponse:
    venue = get_object_or_404(Venue.objects.prefetch_related("addons"), pk=pk)
    if request.method == "POST":
        form = BookingForm(request.POST, venue=venue)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.venue = venue
            booking.status = Booking.STATUS_WAITING
            booking.save()
            form.save_m2m()
            booking.calculate_totals()
            messages.info(request, "Booking created. Please complete the payment to confirm.")
            return redirect("booking_payment", pk=booking.pk)
    else:
        form = BookingForm(venue=venue)

    context = {
        "venue": venue,
        "form": form,
    }
    return render(request, "main/booking_form.html", context)


@login_required
def booking_payment_view(request: HttpRequest, pk: int) -> HttpResponse:
    booking = get_object_or_404(
        Booking.objects.select_related("venue", "venue__category").prefetch_related("addons"), pk=pk, user=request.user
    )
    form = PaymentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        booking.payment_method = form.cleaned_data["payment_method"]
        booking.status = Booking.STATUS_CONFIRMED
        booking.save(update_fields=["payment_method", "status"])
        messages.success(request, "Payment confirmed! Enjoy your game.")
        return redirect("booking_success", pk=booking.pk)

    context = {
        "booking": booking,
        "form": form,
        "deposit": booking.deposit_amount,
        "subtotal": booking.subtotal,
        "grand_total": booking.grand_total,
    }
    return render(request, "main/booking_payment.html", context)


@login_required
def booking_success_view(request: HttpRequest, pk: int) -> HttpResponse:
    booking = get_object_or_404(
        Booking.objects.select_related("venue", "venue__category"), pk=pk, user=request.user
    )
    return render(request, "main/booking_success.html", {"booking": booking})
