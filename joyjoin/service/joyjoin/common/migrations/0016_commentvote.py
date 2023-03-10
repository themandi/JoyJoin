# Generated by Django 2.2.10 on 2020-03-31 16:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0015_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reaction', models.SmallIntegerField()),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.Comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.User')),
            ],
        ),
    ]
