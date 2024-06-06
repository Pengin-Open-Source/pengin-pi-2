from django.db import models
import uuid
from datetime import datetime, timezone


class Orders(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    order_date = models.DateTimeField(null=True)
    is_cancelled = models.BooleanField(default=False)


class OrderChangeRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    data = models.CharField(max_length=255)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    order_date = models.DateTimeField()
    customer_id = models.CharField(max_length=36)
    timestamp = models.DateTimeField()
    user_id = models.CharField(max_length=36)


class OrdersList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    quantity = models.IntegerField()


class OrderHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    data = models.CharField(max_length=255)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    user_id = models.CharField(max_length=36)
    type = models.CharField(max_length=36)


class ShippingAddress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    phone = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=50, unique=True)


def init_on_load(self):
    self._original_data = {}


@classmethod
def after_update_listener(cls, sender, instance, **kwargs):
    if hasattr(instance, '_original_data'):
        new_data = {field.name: getattr(instance, field.name)
                    for field in instance._meta.fields}
        old_data = instance._original_data

        if new_data != old_data:
            order_history = OrderHistory(
                order=instance,
                timestamp=datetime.now(timezone.utc),
                old_data=str(old_data),
                new_data=str(new_data),
                type='updated order',
                user_id=instance.user_uuid.uuid4()
            )
            order_history.save()

            instance._original_data = new_data


# models.signals.post_init.connect(init_on_load)
# models.signals.post_save.connect(after_update_listener, sender=Orders)
