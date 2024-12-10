from django.contrib import admin

from .models import Order, Customer, ShippingAddress

admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(ShippingAddress)
