# Generated by Django 3.0.3 on 2020-07-26 13:32

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('assignment', '0007_auto_20200718_1932'),
        ('student', '0003_file_question'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationForStudent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_filled', models.DateTimeField(default=django.utils.timezone.now)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assignment.Assignment')),
            ],
        ),
    ]
