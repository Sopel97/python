from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class GameplayMode(models.Model):
    class Meta:
        verbose_name_plural = 'GameplayModes'

    name = models.CharField(max_length=256)
    description = models.CharField(max_length=4096, blank=True)

    def __str__(self):
        return str(self.name)

class Research(models.Model):
    class Meta:
        verbose_name_plural = 'Researches'

    name = models.CharField(max_length=256)
    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE, related_name='researches')

    def __str__(self):
        return str(self.name)

class ResearchPrerequisite(models.Model):
    class Meta:
        verbose_name_plural = 'ResearchPrerequisites'

    research = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='prerequisites')
    prereqiusite = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='required_by')

    def clean(self):
        if self.research.gameplay_mode != self.prerequisite.gameplay_mode:
            raise ValidationError(_('ResearchPrerequisite requires reserach and prerequisite to be from the same GameplayMode.'))

    def __str__(self):
        return 'Research {0} requires {1}'.format(str(self.research), str(self.prereqiusite))

class Item(models.Model):
    class Meta:
        verbose_name_plural = 'Items'

    SOLID_STATE = 1
    FLUID_STATE = 2
    GAS_STATE = 3
    STATE_CHOICES = (
        (SOLID_STATE, 'solid'),
        (FLUID_STATE, 'fluid'),
        (GAS_STATE, 'gas')
    )

    name = models.CharField(max_length=128)
    state = models.IntegerField(choices=STATE_CHOICES, default=SOLID_STATE, blank=True)
    required_research = models.ForeignKey(Research, related_name='unlocked_items', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE, related_name='items')

    def clean(self):
        if (self.required_research is not None) and (self.gameplay_mode != self.required_research.gameplay_mode):
            raise ValidationError(_('Item requires required_research and this to be from the same GameplayMode.'))

    def __str__(self):
        return str(self.name)

class MachineType(models.Model):
    class Meta:
        verbose_name_plural = 'MachineTypes'

    name = models.CharField(max_length=128)
    gameplay_mode = models.ForeignKey(GameplayMode, related_name='machine_types', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)


class Machine(models.Model):
    class Meta:
        verbose_name_plural = 'Machines'

    item = models.OneToOneField(Item, on_delete=models.CASCADE, unique=True)
    machine_type = models.ForeignKey(MachineType, related_name='machines', on_delete=models.CASCADE)
    crafting_speed = models.DecimalField(max_digits=6, decimal_places=3)

    def clean(self):
        if self.item.gameplay_mode != self.machine_type.gameplay_mode:
            raise ValidationError(_('Machine requires item and machine_type to be from the same GameplayMode.'))

    def __str__(self):
        return str(self.item)

class Recipe(models.Model):
    class Meta:
        verbose_name_plural = 'Recipes'

    name = models.CharField(max_length=128)
    crafting_time_ticks = models.IntegerField()
    gameplay_mode = models.ForeignKey(GameplayMode, related_name='recipes', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)

class RecipeExecutor(models.Model):
    class Meta:
        verbose_name_plural = 'RecipeExecutors'

    recipe = models.ForeignKey(Recipe, related_name='executors', on_delete=models.CASCADE)
    machine_type = models.ForeignKey(MachineType, related_name='executors', on_delete=models.CASCADE)

    def clean(self):
        if self.recipe.gameplay_mode != self.machine_type.gameplay_mode:
            raise ValidationError(_('RecipeExecutor requires recipe and machine_type to be from the same GameplayMode.'))

    def __str__(self):
        return 'Machine {0} executes recipe {1}'.format(str(self.machine_type), str(self.recipe))

class RecipeIngredient(models.Model):
    class Meta:
        verbose_name_plural = 'RecipeIngredients'

    recipe = models.ForeignKey(Recipe, related_name='ingredients', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    count = models.IntegerField()

    def clean(self):
        if self.recipe.gameplay_mode != self.item.gameplay_mode:
            raise ValidationError(_('RecipeIngredient requires recipe and item to be from the same GameplayMode.'))

    def __str__(self):
        return 'Recipe {0} requires {1}x{2}'.format(str(self.recipe), str(self.count), str(self.item))

class RecipeResult(models.Model):
    class Meta:
        verbose_name_plural = 'RecipeResults'

    recipe = models.ForeignKey(Recipe, related_name='results', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name='recipe_results', on_delete=models.CASCADE)
    count = models.IntegerField()

    def clean(self):
        if self.recipe.gameplay_mode != self.item.gameplay_mode:
            raise ValidationError(_('RecipeResult requires recipe and item to be from the same GameplayMode.'))

    def __str__(self):
        return 'Recipe {0} produces {1}x{2}'.format(str(self.recipe), str(self.count), str(self.item))
