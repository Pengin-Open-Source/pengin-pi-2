from django.db import models
import uuid

from main.models import User
from products.models import Product
from companies.models import Company


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=False)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order_date = models.DateTimeField(null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False)
    is_cancelled = models.BooleanField(default=False)


class OrderList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    quantity = models.IntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)


# class OrderChangeRequest(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     data = models.CharField(max_length=255)
#     order_id = models.ForeignKey('Order', on_delete=models.CASCADE, null=False)
#     order_date = models.DateTimeField(null=True)
#     customer_id = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
#     timestamp = models.DateTimeField(null=True)
#     author = models.ForeignKey('User', on_delete=models.CASCADE, null=False)


# class OrderHistory(models.Model):
#     NEW_ORDER = "NEW_ORDER"
#     UPDATED_ORDER = "UPDATED_ORDER"
#     CANCELLED_ORDER = "CANCELLED_ORDER"
#
#     TYPE_CHOICES = [
#         (NEW_ORDER, "new order"),
#         (UPDATED_ORDER, "update order"),
#         (CANCELLED_ORDER, "cancelled order"),
#     ]
#
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#     data = models.CharField(max_length=255)
#     order_id = models.ForeignKey('Order', on_delete=models.CASCADE, null=False)
#     timestamp = models.DateTimeField(null=True)
#     author = models.ForeignKey('User', on_delete=models.CASCADE, null=False)
#     type = models.CharField(choices=TYPE_CHOICES, max_length=36)


class ShippingAddress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    phone = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False)


class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    contract_type = models.CharField(max_length=100)
    content = models.TextField()
    service_date = models.DateTimeField(null=True)
    expiration_date = models.DateTimeField(null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False)
