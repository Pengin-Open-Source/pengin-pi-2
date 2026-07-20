# admin.py
# Credit to Gemini for assistence when working on this file
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from main.forms import GroupManagerDjangoSiteForm, UserAdminForm, AllowUserSelfValidationForm

from .models import User, Address, SubGroup, GroupToGroupAccess, GroupManager,  SelfValidationAllowed


class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ("name", "email", "is_superuser",
                    "is_active", "validated", "is_staff")
    ordering = ("-is_superuser", "-is_active", "name")


class AllowUserSelfValidationAdmin(admin.ModelAdmin):
    form = AllowUserSelfValidationForm

    # Bypass the list view entirely and open the edit form directly
    # There is only once instance of this object in the table (Singleton)
    # If it doesn't exist,  it will be created now

    def changelist_view(self, request, extra_context=None):
        obj, created = SelfValidationAllowed.objects.get_or_create(pk=1)
        return redirect(
            reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_change",
                args=[obj.pk],
            )
        )

    # SuperUser can't add
    def has_add_permission(self, request):
        if SelfValidationAllowed.objects.exists():
            return False
        return super().has_add_permission(request)

    # Super User Can't delete

    def has_delete_permission(self, request, obj=None):
        return False


class GroupManagerDjangoSiteFormAdmin(admin.ModelAdmin):
    form = GroupManagerDjangoSiteForm


admin.site.register(User, UserAdmin)
admin.site.register(SelfValidationAllowed, AllowUserSelfValidationAdmin)
admin.site.register(Address)
admin.site.register(SubGroup)
admin.site.register(GroupToGroupAccess)
admin.site.register(GroupManager, GroupManagerDjangoSiteFormAdmin)
