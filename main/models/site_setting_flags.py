# Put in custom settings to be set at the site-wide level.
# You put such settings here, and not in settings.py,  when
# you want a Super User to be able to toggle the settings
# in the standard Django Site Admin, rather than having to
# restart the server every time you want to change the setting.

# Here's Gemini boilerplate code for a Singleton setting.
# Rework to make new Singleton Site settings as needed

from django.db import models

# class ClientConfiguration(models.Model):
#     enable_feature_flag = models.BooleanField(default=False, verbose_name="Enable Feature Flag")

#     class Meta:
#         verbose_name = "Client Configuration"
#         verbose_name_plural = "Client Configuration"

#     def save(self, *args, **kwargs):
#         # Enforce a single row in the database
#         self.pk = 1
#         super().save(*args, **kwargs)

#     @classmethod
#     def get_settings(cls):
#         obj, created = cls.objects.get_or_create(pk=1)
#         return obj


class SelfValidationAllowed(models.Model):
    """ Do we allow users to fully validate themselves in the system without 
        A Super User, DBA,  or someone else with privileges confirming the validation?
    """
    enable_user_self_validation = models.BooleanField(
        default=False, verbose_name="Allow New Users To Validate Themselves?")

    class Meta:
        verbose_name = "Allow User-Self Validation"
        verbose_name_plural = "Allow User Self-Validation"

    def save(self, *args, **kwargs):
        # Enforce a single row in the database
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Allow User Self-Validation"
