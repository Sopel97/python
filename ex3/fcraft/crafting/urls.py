from django.urls import path

from django.conf.urls import include, url
from django.contrib import admin

from . import views

app_name = 'crafting'
urlpatterns = [
    path('', views.gameplay_modes, name='gameplay_modes'),

    path('<int:gameplay_mode_id>/', views.gameplay_mode, name='gameplay_mode'),

    path('<int:gameplay_mode_id>/graph/', views.graph, name='graph'),

    path('<int:gameplay_mode_id>/items/', views.items, name='items'),
    path('<int:gameplay_mode_id>/items/<int:item_id>/', views.item, name='item'),

    path('<int:gameplay_mode_id>/researches/', views.researches, name='researches'),
    path('<int:gameplay_mode_id>/researches/<int:research_id>', views.research, name='research'),

    path('<int:gameplay_mode_id>/recipes/', views.recipes, name='recipes'),
    path('<int:gameplay_mode_id>/recipes/<int:recipe_id>', views.recipe, name='recipe'),

    path('<int:gameplay_mode_id>/machines/', views.machines, name='machines'),
    path('<int:gameplay_mode_id>/machines/<int:machine_id>', views.machine, name='machine'),

    path('<int:gameplay_mode_id>/machine_types/', views.machine_types, name='machine_types'),
    path('<int:gameplay_mode_id>/machine_types/<int:machine_type_id>', views.machine_type, name='machine_type')
]
