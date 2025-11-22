# Generated migration for dual inventory system

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_recipe_recipeingredient'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='inventory_a',
            field=models.FloatField(default=0, help_text='Main Warehouse Stock'),
        ),
        migrations.AddField(
            model_name='product',
            name='inventory_b',
            field=models.FloatField(default=0, help_text='Expendable Stock (used for orders)'),
        ),
        migrations.AddField(
            model_name='product',
            name='cost_per_unit',
            field=models.FloatField(default=0, help_text='Cost per unit for ingredients'),
        ),
    ]
