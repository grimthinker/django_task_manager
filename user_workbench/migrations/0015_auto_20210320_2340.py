# Generated by Django 3.1.6 on 2021-03-20 23:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_workbench', '0014_auto_20210318_2203'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfoMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(db_index=True, default='У этого отделения нет описания', max_length=350)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('message_type', models.CharField(choices=[('rmd', 'Напоминание'), ('inf', 'Информация'), ('oth', 'Другое')], default='oth', max_length=3)),
                ('was_read', models.BooleanField(default=False)),
                ('initiator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='initiated_messages', to='user_workbench.userprofile')),
                ('receiver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_messages', to='user_workbench.userprofile')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['creation_datetime']},
        ),
        migrations.AlterField(
            model_name='task',
            name='super_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sub_tasks', to='user_workbench.task'),
        ),
        migrations.DeleteModel(
            name='ReminderSettings',
        ),
    ]