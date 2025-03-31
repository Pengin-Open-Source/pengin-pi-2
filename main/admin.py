# admin.py
from django.contrib import admin

from .models import User, Address, SubGroup, GroupToGroupAccess

admin.site.register(User)
admin.site.register(Address)
admin.site.register(SubGroup)
admin.site.register(GroupToGroupAccess)
