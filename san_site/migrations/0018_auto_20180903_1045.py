# Generated by Django 2.1.1 on 2018-09-03 07:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('san_site', '0017_auto_20180903_0928'),
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guid', models.CharField(db_index=True, max_length=50)),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(max_length=20)),
                ('sort', models.IntegerField(default=500)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_deleted', models.BooleanField(default=False)),
                ('change_password', models.BooleanField(default=False)),
            ],
        ),
        migrations.RemoveField(
            model_name='customer',
            name='change_password',
        ),
        migrations.AddField(
            model_name='person',
            name='customer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='san_site.Customer'),
        ),
        migrations.AddField(
            model_name='person',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
