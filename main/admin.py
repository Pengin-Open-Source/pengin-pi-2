# admin.py
from django.contrib import admin

from main.forms import GroupManagerDjangoSiteFormAdmin, UserAdminForm

from .models import User, Address, SubGroup, GroupToGroupAccess, GroupManager

# part of Gemini's solution to "uncheck validation automatically
class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm


admin.site.register(User, UserAdmin)
admin.site.register(Address)
admin.site.register(SubGroup)
admin.site.register(GroupToGroupAccess)
admin.site.register(GroupManager, GroupManagerDjangoSiteFormAdmin)
