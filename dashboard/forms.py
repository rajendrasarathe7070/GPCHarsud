from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from .utils import get_model


class DashboardLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg", "autofocus": True, "placeholder": "Username",
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg", "placeholder": "Password"}),
    )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        data = super().clean()
        username, password = data.get("username"), data.get("password")
        if not username or not password:
            return data

        # Check axes lockout before authenticate
        try:
            from axes.handlers.proxy import AxesProxyHandler
            if AxesProxyHandler.is_locked(self.request, credentials={"username": username}):
                raise ValidationError("Too many failed attempts. Try again after 1 hour.")
        except ValidationError:
            raise
        except Exception:
            pass

        try:
            user = authenticate(self.request, username=username, password=password)
        except Exception:
            raise ValidationError("Login error. Try again.")

        if user is None:
            raise ValidationError("Invalid username or password.")
        if not user.is_active:
            raise ValidationError("Account is inactive.")
        self.user = user
        return data


class TOTPVerifyForm(forms.Form):
    code = forms.CharField(
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg text-center fw-bold",
            "placeholder": "000000", "inputmode": "numeric",
            "autocomplete": "one-time-code", "autofocus": True,
            "style": "letter-spacing: 0.6rem; font-size: 1.8rem; height: 70px;",
        }),
    )


class TOTPSetupForm(TOTPVerifyForm):
    pass


def get_student_profile_form_class():
    User = get_user_model()
    return forms.modelform_factory(
        User,
        fields=["first_name", "last_name", "email", "phone", "photo", "cast_Categories", "sex", "date_of_birth", "joining_date", "study", "experience", "deprtment"],
        widgets={"date_of_birth": forms.DateInput(attrs={"type": "date"}), "joining_date": forms.DateInput(attrs={"type": "date"})},
    )


def get_student_engagement_form_class():
    StudentEngagement = get_model("studentengagement")
    if StudentEngagement is None:
        return None
    return forms.modelform_factory(
        StudentEngagement,
        fields=["roll_no", "branch_of_student", "passout_year", "got_placement", "company_name", "package_lpa", "offer_letter_details", "opted_for_higher_studies", "higher_studies_institute", "entrance_exam_details", "opted_for_entrepreneurship", "nature_of_work", "annual_turnover_lpa", "preparing_for_competitive_exams", "not_engaged_till_now"],
    )