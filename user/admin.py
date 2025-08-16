from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import Company, Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    ordering = ("created_at",)

    fields = (
        "name",
        "cnpj",
        "created_at",
        "updated_at",
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    ordering = ("created_at",)

    fields = (
        "name",
        "organization",
        "created_at",
        "updated_at",
        "is_active",
        "inactive_since",
        "status",
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ("email", "display_name", "is_staff", "is_superuser")
    list_filter = ("is_staff", "is_superuser", "role")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("username", "display_name", "company")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "display_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    search_fields = ("email", "username", "display_name")
    ordering = ("email",)
