# Generated by Django 3.0 on 2020-04-07 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0017_remove_tagimplication_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='image',
            field=models.ImageField(default='default.jpg', upload_to='profile_images'),
        ),
    ]
