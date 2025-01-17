# Generated by Django 3.2.16 on 2024-03-26 19:23

import django.core.validators
from django.db import migrations, models

import users.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20240325_1937'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=30, unique=True, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+\\Z', 'Only letters, numbers and special symbols @/./+/-/_ allowed in nickname'), users.validators.special_names_validator]),
        ),
    ]
