from django.contrib import admin

from .models import Order, Customer

admin.site.register(Order)
admin.site.register(Customer)
