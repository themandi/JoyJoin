# Generated by Django 2.2.9 on 2020-02-12 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0008_post_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='user_tags',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
