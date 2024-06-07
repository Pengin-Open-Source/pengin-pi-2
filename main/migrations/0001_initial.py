# Generated by Django 5.0.6 on 2024-06-07 17:58

import datetime
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=100, unique=True)),
                ('password', models.CharField(max_length=102)),
                ('name', models.CharField(max_length=100)),
                ('validated', models.BooleanField(default=False)),
                ('validation_date', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('validation_id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('prt', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('prt_reset_date', models.DateTimeField(blank=True, null=True)),
                ('prt_consumption_date', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='%(app_label)s_%(class)s_groups', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='%(app_label)s_%(class)s_user_permissions', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
        ),
    ]
