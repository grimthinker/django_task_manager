# Generated by Django 3.1.6 on 2021-03-16 16:56

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_workbench', '0010_auto_20210312_0308'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='closure_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='deadline',
            field=models.DateTimeField(default=datetime.datetime(9999, 1, 1, 1, 1, 1)),
        ),
    ]
