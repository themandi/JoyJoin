# Generated by Django 3.0 on 2020-03-09 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0006_auto_20191204_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='description',
            field=models.CharField(blank=True, max_length=3000, null=True),
        ),
    ]