# Generated by Django 2.0.5 on 2018-05-31 12:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crafting', '0026_auto_20180531_1406'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gameplaymode',
            name='editing_groups',
        ),
    ]
