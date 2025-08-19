# admin.py
from django.contrib import admin

from main.forms import GroupManagerDjangoSiteFormAdmin

from .models import User, Address, SubGroup, GroupToGroupAccess, GroupManager

admin.site.register(User)
admin.site.register(Address)
admin.site.register(SubGroup)
admin.site.register(GroupToGroupAccess)
admin.site.register(GroupManager, GroupManagerDjangoSiteFormAdmin)
