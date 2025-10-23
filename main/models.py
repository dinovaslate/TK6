from decimal import Decimal

from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - human readable representation
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="venues")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    facilities = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - human readable representation
        return self.name

    @property
    def starting_price(self) -> Decimal:
        return self.price_per_hour


class AddOn(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="addons")
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.venue.name})"


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "venue")
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user} → {self.venue}"


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Review by {self.user} for {self.venue}"


class Booking(models.Model):
    STATUS_WAITING = "waiting"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_WAITING, "Waiting for confirmation"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_COMPLETED, "Completed"),
    ]

    PAYMENT_QRIS = "qris"
    PAYMENT_GOPAY = "gopay"
    PAYMENT_CHOICES = [
        (PAYMENT_QRIS, "QRIS"),
        (PAYMENT_GOPAY, "GoPay"),
    ]

    DEPOSIT_AMOUNT = Decimal("10000.00")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="bookings")
    date = models.DateField()
    start_time = models.TimeField()
    duration_hours = models.PositiveIntegerField(default=1)
    addons = models.ManyToManyField(AddOn, blank=True, related_name="bookings")
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=DEPOSIT_AMOUNT)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Booking #{self.pk} - {self.venue.name}"

    def calculate_totals(self) -> None:
        addon_total = sum(addon.price for addon in self.addons.all())
        venue_total = self.venue.price_per_hour * Decimal(self.duration_hours)
        self.subtotal = venue_total + addon_total
        self.deposit_amount = self.DEPOSIT_AMOUNT
        self.grand_total = self.subtotal + self.deposit_amount
        self.save(update_fields=["subtotal", "deposit_amount", "grand_total"])

# Create your models here.
