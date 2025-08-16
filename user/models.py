from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import CheckConstraint, Q


class Roles(models.IntegerChoices):
    LORD = 1, "Lord"
    MANAGER = 2, "Manager"
    OPERATOR = 3, "Operator"


class CompanyStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    BLOCKED = "blocked", "Blocked"
    CANCELED = "canceled", "Canceled"
    INACTIVE = "inactive", "Inactive"


class CustomUserManager(UserManager["User"]):
    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        if not email:
            raise ValueError("Email must be set")
        email_value = self.normalize_email(email)

        display_name = extra_fields.pop("display_name", None)
        if not display_name:
            raise ValueError("display_name is required")

        username_value = extra_fields.pop("username", None)
        if not username_value:
            raise ValueError("username is required")

        user = self.model(
            email=email_value,
            username=username_value,
            display_name=display_name,
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email=email, password=password, **extra_fields)


class Organization(models.Model):

    class Meta:
        ordering = [
            "created_at",
        ]

        constraints = (
            CheckConstraint(
                condition=Q(cnpj__regex=r"^[0-9]{14}$"),
                name="cnpj_format_check",
            ),
        )

    name = models.CharField(max_length=150, unique=True)
    cnpj = models.CharField(
        max_length=14,
        validators=[RegexValidator(r"^\d{14}$", "CNPJ must have 14 digits")],
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.id} - {self.name}"


class Company(models.Model):
    class Meta:
        ordering = [
            "created_at",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "name"), name="uq_company_org_name"
            )
        ]

    name = models.CharField(max_length=150)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    inactive_since = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        choices=CompanyStatus.choices,
        default=CompanyStatus.ACTIVE,
        max_length=14,
        db_index=True,
    )

    def __str__(self) -> str:
        return f"{self.id} - {self.name}"


class User(AbstractUser):

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    display_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.IntegerField(
        choices=Roles.choices,
        default=Roles.OPERATOR,
        db_index=True,
    )
    inactivated_at = models.DateTimeField(null=True, blank=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
        "display_name",
    ]
    objects: ClassVar[UserManager["User"]] = CustomUserManager()

    @property
    def role_label(self) -> str:
        return str(Roles(self.role).label)

    def __str__(self) -> str:
        return self.display_name
