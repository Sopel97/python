from django.contrib import admin

from .models import *

admin.site.register(GameplayMode)
admin.site.register(Research)
admin.site.register(ResearchPrerequisite)
admin.site.register(Item)
admin.site.register(MachineType)
admin.site.register(Machine)
admin.site.register(Recipe)
admin.site.register(RecipeExecutor)
admin.site.register(RecipeIngredient)
admin.site.register(RecipeResult)