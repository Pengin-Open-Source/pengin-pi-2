# admin.py
# Credit to Gemini for assistence when working on this file
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from main.forms import GroupManagerDjangoSiteForm, UserAdminForm

from .models import User, Address, SubGroup, GroupToGroupAccess, GroupManager


class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ("name", "email", "is_superuser",
                    "is_active", "validated", "is_staff")
    ordering = ("-is_superuser", "-is_active", "name")


class GroupManagerDjangoSiteFormAdmin(admin.ModelAdmin):
    form = GroupManagerDjangoSiteForm


admin.site.register(User, UserAdmin)
admin.site.register(Address)
admin.site.register(SubGroup)
admin.site.register(GroupToGroupAccess)
admin.site.register(GroupManager, GroupManagerDjangoSiteFormAdmin)
