from django.contrib import admin
from django import forms

from .models import *

class ResearchPrerequisiteInline(admin.TabularInline):
    model = ResearchPrerequisite
    fk_name = 'research'
    extra = 0

class ResearchInline(admin.TabularInline):
    model = Research
    extra = 0
    show_change_link = True

class ResearchAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Gameplay Mode',
            {
                'fields' : ('gameplay_mode',)
            }
        ),
        (
            'Properties',
            {
                'fields' : ('name',)
            }
        )
    )

    list_filter = ('gameplay_mode',)

    inlines = [ResearchPrerequisiteInline]

admin.site.register(Research, ResearchAdmin)

admin.site.register(ResearchPrerequisite)

class MachineInline(admin.TabularInline):
    model = Machine
    extra = 0
    show_change_link = True

class ItemInline(admin.TabularInline):
    model = Item
    extra = 0
    show_change_link = True

class FiniteResourceInline(admin.TabularInline):
    model = FiniteResource
    extra = 0
    show_change_link = True

class FiniteResourceCollectorInline(admin.TabularInline):
    model = FiniteResourceCollector
    extra = 0
    show_change_link = True

class ItemAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Gameplay Mode',
            {
                'fields' : ('gameplay_mode',)
            }
        ),
        (
            'Properties',
            {
                'fields' : ('name', 'state', 'required_research')
            }
        )
    )

    list_filter = ('gameplay_mode',)

    inlines = [MachineInline, FiniteResourceInline, FiniteResourceCollectorInline]

admin.site.register(Item, ItemAdmin)

class MachineTypeInline(admin.TabularInline):
    model = MachineType
    extra = 0
    show_change_link = True

class MachineTypeAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Gameplay Mode',
            {
                'fields' : ('gameplay_mode',)
            }
        ),
        (
            'Properties',
            {
                'fields' : ('name',)
            }
        )
    )

    list_filter = ('gameplay_mode',)

    inlines = [MachineInline]

admin.site.register(MachineType, MachineTypeAdmin)

class MachineAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Gameplay Mode',
            {
                'fields' : ('gameplay_mode',)
            }
        ),
        (
            'Properties',
            {
                'fields' : ('machine_type', 'item', 'crafting_speed', 'power_usage_kW', 'tier')
            }
        )
    )

    list_filter = ('gameplay_mode',)

admin.site.register(Machine, MachineAdmin)

class RecipeExecutorInline(admin.TabularInline):
    model = RecipeExecutor
    extra = 0
    min_num = 1

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0

class RecipeResultInline(admin.TabularInline):
    model = RecipeResult
    extra = 0
    min_num = 1

class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 0
    show_change_link = True

class RecipeAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Gameplay Mode',
            {
                'fields' : ('gameplay_mode',)
            }
        ),
        (
            'Properties',
            {
                'fields' : ('name', 'crafting_time_ticks', 'required_research')
            }
        )
    )

    list_filter = ('gameplay_mode',)

    inlines = [RecipeExecutorInline, RecipeIngredientInline, RecipeResultInline]

admin.site.register(Recipe, RecipeAdmin)

admin.site.register(RecipeExecutor)

admin.site.register(RecipeIngredient)

admin.site.register(RecipeResult)

class GameplayModeAdmin(admin.ModelAdmin):
    inlines = [ItemInline, MachineTypeInline, MachineInline, RecipeInline, ResearchInline]

admin.site.register(GameplayMode, GameplayModeAdmin)

class FiniteResourceCollectionIngredientInline(admin.TabularInline):
    model = FiniteResourceCollectionIngredient
    extra = 0
    show_change_link = True

class FiniteResourceAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Gameplay Mode',
            {
                'fields' : ('gameplay_mode',)
            }
        ),
        (
            'Properties',
            {
                'fields' : ('finite_resource_type', 'item', 'mining_hardness', 'mining_time')
            }
        )
    )

    list_filter = ('gameplay_mode',)

    inlines = [FiniteResourceCollectionIngredientInline]

admin.site.register(FiniteResource, FiniteResourceAdmin)

class FiniteResourceTypeInline(admin.TabularInline):
    model = FiniteResourceType
    extra = 0
    show_change_link = True

class FiniteResourceCollectorInline(admin.TabularInline):
    model = FiniteResourceCollector
    extra = 0
    show_change_link = True

class FiniteResourceTypeAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Gameplay Mode',
            {
                'fields' : ('gameplay_mode',)
            }
        ),
        (
            'Properties',
            {
                'fields' : ('name',)
            }
        )
    )

    list_filter = ('gameplay_mode',)

    inlines = [FiniteResourceInline, FiniteResourceCollectorInline]

admin.site.register(FiniteResourceType, FiniteResourceTypeAdmin)

admin.site.register(FiniteResourceCollectionIngredient)

class FiniteResourceCollectorAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Gameplay Mode',
            {
                'fields' : ('gameplay_mode',)
            }
        ),
        (
            'Properties',
            {
                'fields' : ('finite_resource_type', 'item', 'mining_power', 'mining_speed', 'power_usage_kW', 'tier')
            }
        )
    )

    list_filter = ('gameplay_mode',)

admin.site.register(FiniteResourceCollector, FiniteResourceCollectorAdmin)
