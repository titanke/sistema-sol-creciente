# Generated by Django 5.0.6 on 2025-01-17 06:46

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0020_salesitems_feature_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='color',
            name='date_added',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='color',
            name='date_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='color',
            name='status',
            field=models.IntegerField(default=1),
        ),
    ]
