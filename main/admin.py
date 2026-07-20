# admin.py
from django.contrib import admin

from main.forms import GroupManagerDjangoSiteForm, UserAdminForm, AllowUserSelfValidationForm

from .models import User, Address, SubGroup, GroupToGroupAccess, GroupManager,  SelfValidationAllowed

# part of Gemini's solution to "uncheck validation automatically


class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ("name", "email", "is_superuser",
                    "is_active", "validated", "is_staff")
    ordering = ("-is_superuser", "-is_active", "name")


class AllowUserSelfValidationAdmin(admin.ModelAdmin):
    form = AllowUserSelfValidationForm


class GroupManagerDjangoSiteFormAdmin(admin.ModelAdmin):
    form = GroupManagerDjangoSiteForm


admin.site.register(User, UserAdmin)
admin.site.register(SelfValidationAllowed, AllowUserSelfValidationAdmin)
admin.site.register(Address)
admin.site.register(SubGroup)
admin.site.register(GroupToGroupAccess)
admin.site.register(GroupManager, GroupManagerDjangoSiteFormAdmin)
