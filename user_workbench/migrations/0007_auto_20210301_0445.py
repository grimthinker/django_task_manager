# Generated by Django 3.1.6 on 2021-03-01 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_workbench', '0006_auto_20210301_0426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='responsible_users',
            field=models.ManyToManyField(blank=True, related_name='assigned_tasks', to='user_workbench.UserProfile'),
        ),
    ]
