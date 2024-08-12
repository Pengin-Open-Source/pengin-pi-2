# Generated by Django 5.0.6 on 2024-06-06 22:49

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='priority',
            field=models.IntegerField(default=10000),
        ),
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.UUIDField(default=uuid.UUID('b1f96bc8-57f4-4604-9a42-54d19c7e5cb0'), primary_key=True, serialize=False),
        ),
    ]