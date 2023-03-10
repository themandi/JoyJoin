# Generated by Django 2.2.9 on 2020-03-30 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0015_merge_20200316_2142'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='_level',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='login',
            field=models.CharField(max_length=31, unique=True),
        ),
        migrations.AddConstraint(
            model_name='vote',
            constraint=models.UniqueConstraint(fields=('user', 'post'), name='vote_unique_post_user'),
        ),
    ]
