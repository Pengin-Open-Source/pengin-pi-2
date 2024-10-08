from django.core.exceptions import ValidationError
from django.db import models
import uuid

from main.models import User, Address
from products.models import Product
from companies.models import Company


# ### Customer Models ###
class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name

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


class ShippingAddress(Address):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False)
    address = models.OneToOneField(Address, on_delete=models.CASCADE, parent_link=True)

    class Meta:
        verbose_name_plural = "Shipping addresses"


# ### Order Models ###
class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order_date = models.DateTimeField(null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False, blank=False)
    is_cancelled = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    products = models.ManyToManyField(Product, through='OrderProduct')
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.customer.name} Order, {self.order_date.strftime('%b %d, %Y')}"

    def clean(self):
        if self.shipping_address and self.shipping_address.customer != self.customer:
            raise ValidationError('Shipping address must belong to the customer.')


class OrderProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    quantity = models.PositiveIntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)

    class Meta:
        unique_together = ('order', 'product')


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
