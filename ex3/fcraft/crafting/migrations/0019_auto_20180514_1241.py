# Generated by Django 2.0.5 on 2018-05-14 10:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crafting', '0018_researchprerequisite_gameplay_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researchprerequisite',
            name='gameplay_mode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crafting.GameplayMode'),
        ),
    ]
