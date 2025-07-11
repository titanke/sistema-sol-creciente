# Generated by Django 5.0.6 on 2025-01-17 18:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0022_size_date_added_size_date_updated_size_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='image',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='productfeature',
            name='color',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='posApp.color'),
        ),
        migrations.AlterField(
            model_name='productfeature',
            name='size',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='posApp.size'),
        ),
        migrations.AlterField(
            model_name='products',
            name='category_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='posApp.category'),
        ),
    ]
