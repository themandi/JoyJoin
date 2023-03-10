# Generated by Django 2.2.9 on 2020-05-22 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0031_auto_20200519_1323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='implied_tags',
            field=models.ManyToManyField(blank=True, related_name='implied_tags', to='common.Tag'),
        ),
        migrations.AlterField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='tags', to='common.Tag'),
        ),
        migrations.AlterField(
            model_name='post',
            name='user_tags',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
    ]
