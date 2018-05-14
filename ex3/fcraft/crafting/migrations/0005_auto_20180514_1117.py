# Generated by Django 2.0.5 on 2018-05-14 09:17

from django.db import migrations
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('crafting', '0004_auto_20180514_1030'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='required_research',
            field=smart_selects.db_fields.ChainedForeignKey(blank=True, chained_field='gameplay_mode', chained_model_field='gameplay_mode', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unlocked_items', to='crafting.Research'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='item',
            field=smart_selects.db_fields.ChainedForeignKey(chained_field='machine_type__gameplay_mode', chained_model_field='gameplay_mode', on_delete=django.db.models.deletion.CASCADE, to='crafting.Item', unique=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='machine_type',
            field=smart_selects.db_fields.ChainedForeignKey(chained_field='gameplay_mode', chained_model_field='gameplay_mode', on_delete=django.db.models.deletion.CASCADE, related_name='machines', to='crafting.MachineType'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='required_research',
            field=smart_selects.db_fields.ChainedForeignKey(blank=True, chained_field='gameplay_mode', chained_model_field='gameplay_mode', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unlocked_recipes', to='crafting.Research'),
        ),
        migrations.AlterField(
            model_name='researchprerequisite',
            name='prereqiusite',
            field=smart_selects.db_fields.ChainedForeignKey(chained_field='gameplay_mode', chained_model_field='gameplay_mode', on_delete=django.db.models.deletion.CASCADE, related_name='required_by', to='crafting.Research'),
        ),
    ]
