# Generated by Django 3.1.6 on 2021-03-23 12:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_workbench', '0018_auto_20210321_2120'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='chief',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='slave_department', to='user_workbench.userprofile'),
        ),
    ]
