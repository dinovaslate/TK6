from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import AddOn, Booking, Review


class BootstrapFormMixin:
    """Apply Bootstrap form-control styling to compatible widgets."""

    bootstrap_excluded_widgets = (
        forms.CheckboxInput,
        forms.RadioSelect,
        forms.CheckboxSelectMultiple,
    )

    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, self.bootstrap_excluded_widgets):
                continue
            existing = widget.attrs.get("class", "")
            class_list = [cls for cls in existing.split() if cls]
            if "form-control" not in class_list:
                class_list.append("form-control")
            widget.attrs["class"] = " ".join(class_list)


class LoginForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Invalid username or password.")
            cleaned_data["user"] = user
        return cleaned_data


class RegisterForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
        )


class BookingForm(BootstrapFormMixin, forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    duration_hours = forms.IntegerField(min_value=1, max_value=12)
    addons = forms.ModelMultipleChoiceField(
        queryset=AddOn.objects.none(), required=False, widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Booking
        fields = ["date", "start_time", "duration_hours", "addons", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Notes or requirements"})}

    def __init__(self, *args, **kwargs):
        venue = kwargs.pop("venue", None)
        super().__init__(*args, **kwargs)
        if venue is not None:
            self.fields["addons"].queryset = venue.addons.all()
            self.fields["addons"].label_from_instance = lambda obj: f"{obj.name} - Rp{int(obj.price):,}"
        self._apply_bootstrap()


class PaymentForm(forms.Form):
    payment_method = forms.ChoiceField(choices=Booking.PAYMENT_CHOICES, widget=forms.RadioSelect)


class ReviewForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.RadioSelect,
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Share your experience"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
