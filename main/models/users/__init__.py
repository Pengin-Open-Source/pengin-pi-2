from django.db import models
import uuid
from datetime import datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=102)
    name = models.CharField(max_length=100)
    validated = models.BooleanField(default=False)
    validation_date = models.DateTimeField(default=datetime.utcnow)
    validation_id = models.UUIDField(default=uuid.uuid4, unique=True)
    prt = models.UUIDField(default=uuid.uuid4, unique=True)
    prt_reset_date = models.DateTimeField(null=True, blank=True)
    prt_consumption_date = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        app_label = 'main'  # Explicitly set the app_label
    
    # Define unique related_name for groups and user_permissions
    groups = models.ManyToManyField(
    Group,
    verbose_name='groups',  # Wrapped in quotes
    blank=True,
    related_name='%(app_label)s_%(class)s_groups',  # Unique related_name
    related_query_name="user",
    help_text=(
        'The groups this user belongs to. A user will get all permissions '
        'granted to each of their groups.'
    ),
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',  # Wrapped in quotes
        blank=True,
        related_name='%(app_label)s_%(class)s_user_permissions',  # Unique related_name
        related_query_name="user",
        help_text='Specific permissions for this user.',
    )
    
    def __str__(self):
        return self.email
