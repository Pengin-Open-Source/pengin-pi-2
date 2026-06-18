from django.db import models
from django.core.exceptions import ValidationError
import uuid
from datetime import datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission

# Worked with Gemini on this file.


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
        extra_fields.setdefault('validated', True)
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

    # We don't want unvalidated Managers

    def save(self, *args, **kwargs):
        # Force validation to run programmatically (e.g., in the shell)
        self.clean()

        # 1. Grab update_fields if it exists
        update_fields = kwargs.get('update_fields')

        # 2. If we are ONLY updating the login timestamp, skip our manager validation
        if update_fields and list(update_fields) == ['last_login']:
            super().save(*args, **kwargs)
            return
        # Check if the assigned manager is validated
        if not self.validated and hasattr(self, 'groups_managed') and self.groups_managed.exists():
            raise ValidationError(
                "You are trying to revoke validation for a Manager User. "
                "Revoke Management Access for any user before revoking validation."
            )

        # "Kill Switch" - if a user is inactivated, also un-validate them
        # this will help keep them out of dropdowns and immediately block
        # their access to several things even before they logout.
        if not self.is_active:
            self.validated = False
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'main'  # Explicitly set the app_label
        # We don't want invalidate staff.
        # We also don't want inactive users to still be validated,
        # because then they will still be considered valid options for say,
        # Ticket Ownership.
        constraints = [
            models.CheckConstraint(
                check=models.Q(is_staff=False) | models.Q(validated=True),
                name='prevent_unvalidated_staff'
            ),

            models.CheckConstraint(
                check=models.Q(is_active=False, validated=False) | models.Q(
                    is_active=True),
                name='unvalidate_all_inactive_users'
            )
        ]

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
        # Unique related_name
        related_name='%(app_label)s_%(class)s_user_permissions',
        related_query_name="user",
        help_text='Specific permissions for this user.',
    )

    def __str__(self):
        return str(self.email)

# GEMINI suggested a closure table for dealing with subgroup inheritance
# and also another link table for special access from one group to another across
# the hierarchy


class SubGroup(models.Model):
    ancestor = models.ForeignKey(
        Group, related_name='descendant_links', on_delete=models.CASCADE)
    descendant = models.ForeignKey(
        Group, related_name='ancestor_links', on_delete=models.CASCADE)
    depth = models.PositiveIntegerField()

    class Meta:
        unique_together = ('ancestor', 'descendant')

    def __str__(self):
        return f"{self.descendant.name}, subgroup of {self.ancestor.name}"


class GroupToGroupAccess(models.Model):
    accessed_group = models.ForeignKey(
        Group, related_name='groups_with_access_to_me', on_delete=models.CASCADE)
    group_with_access = models.ForeignKey(
        Group, related_name='has_access_to_group', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('accessed_group', 'group_with_access')

    def __str__(self):
        return f"{self.accessed_group.name} can be accessed by members of {self.group_with_access.name}"


class GroupManager(models.Model):
    """ Not to be confused with GroupManager in django.contrib.auth.models
        That GroupManager is extending models.Manager.
        This GroupManager is an ORM Model,  and defines a link table
        connecting users with Groups that they are to manage.
    """
     
    managed_group = models.ForeignKey(
        Group, related_name='group_managers', on_delete=models.CASCADE)
    manager = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='groups_managed')

    # We do not want unvalidated Group/Role Managers

    def clean(self):
        super().clean()
        # Check if the assigned manager is validated
        if not hasattr(self, 'manager') or (self.manager and not self.manager.validated):
            raise ValidationError(
                "You are trying to make an unvalidated User a manager. "
                "Validate users before giving them Management access."
            )

    def save(self, *args, **kwargs):
        # Force validation to run programmatically (e.g., in the shell)
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('managed_group', 'manager')

    def __str__(self):
        return f"{self.manager.name} manages Group/Role {self.managed_group.name}"
