# Generated by Django 2.2.9 on 2020-02-10 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0007_auto_20200210_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(to='common.Tag'),
        ),
    ]
