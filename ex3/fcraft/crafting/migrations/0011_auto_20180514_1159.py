# Generated by Django 2.0.5 on 2018-05-14 09:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crafting', '0010_auto_20180514_1156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='machine_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='machines', to='crafting.MachineType'),
        ),
    ]