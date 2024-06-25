from django.core.exceptions import ValidationError
from django.db import models
import uuid

from main.models import User
from products.models import Product
from companies.models import Company


# ### Customer Models ###
class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50, null=False, blank=False)

    def clean(self):
        if self.user and self.company:
            raise ValidationError('Customer cannot have both user and company relationships.')
        if not self.user and not self.company:
            raise ValidationError('Customer must have either a user or a company relationship.')
        self.name = self.company.name if self.company else self.user.name
        if not self.name:
            self.name = "Unnamed Customer"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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


# ### Order Models ###
class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order_date = models.DateTimeField(null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False, blank=False)
    is_cancelled = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False)


class OrderList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    quantity = models.PositiveIntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)

    class Meta:
        unique_together = (('order', 'product'),)


# ### Order Workflow Models ###

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
