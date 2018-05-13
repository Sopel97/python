# Generated by Django 2.0.5 on 2018-05-13 21:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crafting', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='item',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='crafting.Item'),
        ),
        migrations.AlterField(
            model_name='reciperesult',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe_results', to='crafting.Item'),
        ),
    ]
