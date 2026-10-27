from django.urls import path
from . import views, auth_views

app_name = "dashboard"

urlpatterns = [
    # Auth
    path("login/",  auth_views.login_view,  name="login"),
    path("logout/", auth_views.logout_view, name="logout"),

    # 2FA
    path("2fa/setup-prompt/", auth_views.totp_setup_prompt, name="totp_setup_prompt"),
    path("2fa/setup/",        auth_views.totp_setup,        name="totp_setup"),
    path("2fa/verify/",       auth_views.totp_verify,       name="totp_verify"),
    path("2fa/skip/",         auth_views.totp_skip,         name="totp_skip"),

    # Core
    path("",                       views.dashboard_router,      name="router"),
    path("staff/",                 views.staff_dashboard,       name="staff"),
    path("student/",               views.student_dashboard,     name="student"),
    path("student/edit/",          views.student_profile_edit,  name="student_profile_edit"),

    # List / Add / Edit / Delete
    path("model/<str:model_key>/",              views.model_list_view,   name="model_list"),
    path("model/<str:model_key>/add/",          views.model_add_view,    name="model_add"),
    path("model/<str:model_key>/<int:pk>/edit/",    views.model_edit_view,   name="model_edit"),
    path("model/<str:model_key>/<int:pk>/delete/",  views.model_delete_view, name="model_delete"),
]