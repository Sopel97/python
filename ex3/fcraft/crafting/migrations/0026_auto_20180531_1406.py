# Generated by Django 2.0.5 on 2018-05-31 12:06

from django.db import migrations
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('crafting', '0025_auto_20180516_1355'),
    ]

    operations = [
        migrations.AlterField(
            model_name='finiteresource',
            name='item',
            field=smart_selects.db_fields.ChainedForeignKey(chained_field='gameplay_mode', chained_model_field='gameplay_mode', on_delete=django.db.models.deletion.CASCADE, related_name='finite_resource', to='crafting.Item', unique=True),
        ),
        migrations.AlterField(
            model_name='finiteresourcecollector',
            name='item',
            field=smart_selects.db_fields.ChainedForeignKey(chained_field='gameplay_mode', chained_model_field='gameplay_mode', on_delete=django.db.models.deletion.CASCADE, related_name='finite_resource_collector', to='crafting.Item', unique=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='item',
            field=smart_selects.db_fields.ChainedForeignKey(chained_field='gameplay_mode', chained_model_field='gameplay_mode', on_delete=django.db.models.deletion.CASCADE, related_name='machine', to='crafting.Item', unique=True),
        ),
    ]