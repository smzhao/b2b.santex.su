# Generated by Django 2.1.1 on 2018-09-16 13:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('san_site', '0041_auto_20180916_1609'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prices',
            name='promo',
            field=models.BooleanField(default=False),
        ),
    ]