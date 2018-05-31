from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import Group

from smart_selects.db_fields import ChainedForeignKey

def allEqual(iterable):
   return iterable[1:] == iterable[:-1]

class GameplayMode(models.Model):
    class Meta:
        verbose_name_plural = 'GameplayModes'

    name = models.CharField(max_length=256)
    description = models.CharField(max_length=4096, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    editing_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='gameplay_modes', blank=True)

    def __str__(self):
        return str(self.name)

class Research(models.Model):
    class Meta:
        verbose_name_plural = 'Researches'

    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE, related_name='researches')
    name = models.CharField(max_length=256)

    def __str__(self):
        return str(self.name)

class ResearchPrerequisite(models.Model):
    class Meta:
        verbose_name_plural = 'ResearchPrerequisites'

    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE)
    research = ChainedForeignKey(
        Research,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        on_delete=models.CASCADE,
        related_name='prerequisites'
    )
    prerequisite = ChainedForeignKey(
        Research,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        on_delete=models.CASCADE,
        related_name='required_by'
    )

    def clean(self):
        if not allEqual([self.research.gameplay_mode, self.gameplay_mode, self.prerequisite.gameplay_mode]):
            raise ValidationError(_('GameplayMode mismatch in ResearchPrerequisite.'))

    def __str__(self):
        return 'Research {0} requires {1}'.format(str(self.research), str(self.prerequisite))

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

    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=128)
    state = models.IntegerField(choices=STATE_CHOICES, default=SOLID_STATE, blank=True)
    required_research = ChainedForeignKey(
        Research,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='unlocked_items',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None
    )

    def clean(self):
        if (self.required_research is not None) and (self.gameplay_mode != self.required_research.gameplay_mode):
            raise ValidationError(_('GameplayMode mismatch in Item.'))

    def __str__(self):
        return str(self.name)

class MachineType(models.Model):
    class Meta:
        verbose_name_plural = 'MachineTypes'

    gameplay_mode = models.ForeignKey(GameplayMode, related_name='machine_types', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    def __str__(self):
        return str(self.name)

class FiniteResourceType(models.Model):
    class Meta:
        verbose_name_plural = 'FiniteResourceTypes'

    gameplay_mode = models.ForeignKey(GameplayMode, related_name='finite_resource_types', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)

    def __str__(self):
        return str(self.name)

class FiniteResource(models.Model):
    class Meta:
        verbose_name_plural = 'FiniteResources'

    gameplay_mode = models.ForeignKey(GameplayMode, related_name='finite_resources', on_delete=models.CASCADE)
    item = ChainedForeignKey(
        Item,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='finite_resource',
        on_delete=models.CASCADE,
        unique=True
    )
    finite_resource_type = ChainedForeignKey(
        FiniteResourceType,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='finite_resources',
        on_delete=models.CASCADE
    )
    mining_hardness = models.DecimalField(max_digits=6, decimal_places=3)
    mining_time = models.DecimalField(max_digits=6, decimal_places=3)

    def clean(self):
        if not allEqual([self.gameplay_mode, self.item.gameplay_mode, self.finite_resource_type.gameplay_mode]):
            raise ValidationError(_('GameplayMode mismatch in FiniteResource.'))

        if (self.mining_hardness <= 0):
            raise ValidationError(_('Mining hardness must be positive.'))

        if (self.mining_time <= 0):
            raise ValidationError(_('Mining time must be positive.'))

    def __str__(self):
        return str(self.item.name)

class FiniteResourceCollectionIngredient(models.Model):
    class Meta:
        verbose_name_plural = 'FiniteResourceCollectionIngredients'

    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE)
    resource = ChainedForeignKey(
        FiniteResource,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='collection_ingredients',
        on_delete=models.CASCADE
    )
    item = ChainedForeignKey(
        Item,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        on_delete=models.CASCADE
    )
    count = models.IntegerField()

    def clean(self):
        if not allEqual([self.gameplay_mode, self.resource.gameplay_mode, self.item.gameplay_mode]):
            raise ValidationError(_('GameplayMode mismatch in FiniteResourceCollectionIngredient.'))

        if (self.count <= 0):
            raise ValidationError(_('Count must be positive.'))

    def __str__(self):
        return '{0} resource collection requires {1}x{2}'.format(str(self.resource), str(self.count), str(self.item))

class FiniteResourceCollector(models.Model):
    class Meta:
        verbose_name_plural = 'FiniteResourceCollectors'

    gameplay_mode = models.ForeignKey(GameplayMode, related_name='resource_collectors', on_delete=models.CASCADE)
    item = ChainedForeignKey(
        Item,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='finite_resource_collector',
        on_delete=models.CASCADE,
        unique=True
    )
    finite_resource_type = ChainedForeignKey(
        FiniteResourceType,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='finite_resource_collectors',
        on_delete=models.CASCADE
    )
    mining_power = models.DecimalField(max_digits=6, decimal_places=3)
    mining_speed = models.DecimalField(max_digits=6, decimal_places=3)
    power_usage_kW = models.IntegerField(blank=False, default=0)
    tier = models.IntegerField(default=1, blank=False)

    def clean(self):
        if not allEqual([self.gameplay_mode, self.item.gameplay_mode, self.finite_resource_type.gameplay_mode]):
            raise ValidationError(_('GameplayMode mismatch in FiniteResourceCollector.'))

        if (self.mining_power <= 0):
            raise ValidationError(_('Mining power must be positive.'))

        if (self.mining_speed <= 0):
            raise ValidationError(_('Mining speed must be positive.'))

        if (self.power_usage_kW < 0):
            raise ValidationError(_('Power usage must be nonnegative.'))

        if (self.tier < 0):
            raise ValidationError(_('Tier must be nonnegative.'))

    def __str__(self):
        return str(self.item)

class Machine(models.Model):
    class Meta:
        verbose_name_plural = 'Machines'

    gameplay_mode = models.ForeignKey(GameplayMode, related_name='machines', on_delete=models.CASCADE)
    item = ChainedForeignKey(
        Item,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='machine',
        on_delete=models.CASCADE,
        unique=True
    )
    machine_type = ChainedForeignKey(
        MachineType,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='machines',
        on_delete=models.CASCADE
    )
    crafting_speed = models.DecimalField(max_digits=6, decimal_places=3)
    power_usage_kW = models.IntegerField(blank=False, default=0)
    tier = models.IntegerField(default=1, blank=False)

    def clean(self):
        if not allEqual([self.item.gameplay_mode, self.gameplay_mode, self.machine_type.gameplay_mode]):
            raise ValidationError(_('GameplayMode mismatch in Machine.'))

        if (self.crafting_speed <= 0):
            raise ValidationError(_('Crafting speed must be positive.'))

        if (self.power_usage_kW < 0):
            raise ValidationError(_('Power usage must be nonnegative.'))

        if (self.tier < 0):
            raise ValidationError(_('Tier must be nonnegative.'))

    def __str__(self):
        return str(self.item)

class Recipe(models.Model):
    class Meta:
        verbose_name_plural = 'Recipes'

    gameplay_mode = models.ForeignKey(GameplayMode, related_name='recipes', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    crafting_time_ticks = models.IntegerField()
    required_research = ChainedForeignKey(
        Research,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='unlocked_recipes',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None
    )

    def clean(self):
        if (self.required_research is not None) and (self.gameplay_mode != self.required_research.gameplay_mode):
            raise ValidationError(_('GameplayMode mismatch in Recipe.'))

        if (self.crafting_time_ticks <= 0):
            raise ValidationError(_('Crafting time must be positive.'))

    def __str__(self):
        return str(self.name)

class RecipeExecutor(models.Model):
    class Meta:
        verbose_name_plural = 'RecipeExecutors'

    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE)
    recipe = ChainedForeignKey(
        Recipe,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='executors',
        on_delete=models.CASCADE
    )
    machine_type = ChainedForeignKey(
        MachineType,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='executors',
        on_delete=models.CASCADE
    )
    machine_tier_required = models.IntegerField(default=1, blank=False)

    def clean(self):
        if not allEqual([self.gameplay_mode, self.recipe.gameplay_mode, self.machine_type.gameplay_mode]):
            raise ValidationError(_('GameplayMode mismatch in RecipeExecutor.'))

        if (self.machine_tier_required < 0):
            raise ValidationError(_('Required machine tier must be nonnegative.'))

    def __str__(self):
        return 'Machine {0} executes recipe {1}'.format(str(self.machine_type), str(self.recipe))

class RecipeIngredient(models.Model):
    class Meta:
        verbose_name_plural = 'RecipeIngredients'

    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE)
    recipe = ChainedForeignKey(
        Recipe,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='ingredients',
        on_delete=models.CASCADE
    )
    item = ChainedForeignKey(
        Item,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE
    )
    count = models.IntegerField()

    def clean(self):
        if not allEqual([self.gameplay_mode, self.recipe.gameplay_mode, self.item.gameplay_mode]):
            raise ValidationError(_('GameplayMode mismatch in RecipeIngredient.'))

        if (self.count <= 0):
            raise ValidationError(_('Count must be positive.'))

    def __str__(self):
        return 'Recipe {0} requires {1}x{2}'.format(str(self.recipe), str(self.count), str(self.item))

class RecipeResult(models.Model):
    class Meta:
        verbose_name_plural = 'RecipeResults'

    gameplay_mode = models.ForeignKey(GameplayMode, on_delete=models.CASCADE)
    recipe = ChainedForeignKey(
        Recipe,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='results',
        on_delete=models.CASCADE
    )
    item = ChainedForeignKey(
        Item,
        chained_field='gameplay_mode',
        chained_model_field='gameplay_mode',
        show_all=False,
        auto_choose=False,
        sort=True,
        related_name='recipe_results',
        on_delete=models.CASCADE
    )
    count = models.IntegerField()

    def clean(self):
        if not allEqual([self.gameplay_mode, self.recipe.gameplay_mode, self.item.gameplay_mode]):
            raise ValidationError(_('GameplayMode mismatch in RecipeResult.'))

        if (self.count <= 0):
            raise ValidationError(_('Count must be positive.'))

    def __str__(self):
        return 'Recipe {0} produces {1}x{2}'.format(str(self.recipe), str(self.count), str(self.item))
