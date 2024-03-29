from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from chat.models import Sector


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, display_name, password=None, **other_fields):
        if not email:
            raise ValueError("You must provide an email address")

        email = self.normalize_email(email)
        user = self.model(
            email=email, username=username, display_name=display_name, **other_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, username, display_name, password=None, **other_fields
    ):
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)

        if other_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if other_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, display_name, password, **other_fields)


class User(AbstractUser):

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    display_name = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=True)
    role = models.IntegerField(default=1)
    # sectors = models.ManyToManyField(
    #     Sector,
    #     related_name="user_sector",
    #     blank=True,
    # )
    # sectors_transfer = models.ManyToManyField(
    #     Sector,
    #     related_name="user_transfer_sector",
    #     blank=True,
    # )
    inactivated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = (
        "username",
        # "sectors",
        "display_name",
    )

    def __str__(self):
        return self.display_name
