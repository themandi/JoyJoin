# Generated by Django 2.2.9 on 2020-03-11 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0012_merge_20200311_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='description',
            field=models.CharField(blank=True, max_length=511, null=True),
        ),
    ]
