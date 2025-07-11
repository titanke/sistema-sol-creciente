# Generated by Django 5.0.6 on 2025-01-16 17:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0018_productfeature_delete_color_delete_size'),
    ]

    operations = [
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='productfeature',
            name='color',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posApp.color'),
        ),
        migrations.AlterField(
            model_name='productfeature',
            name='size',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posApp.size'),
        ),
    ]
