from django.http import HttpResponse
from django.template import loader
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from .models import *

def get_object_or_None(klass, *args, **kwargs):
    """
    Uses get() to return an object or None if the object does not exist.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Note: Like with get(), a MultipleObjectsReturned will be raised if
    more than one object is found.
    """
    try:
        return klass.objects.get(*args, **kwargs)
    except ObjectDoesNotExist:
        return None

def index(request):
    return HttpResponse("crafting...")

def gameplay_mode(request, gameplay_mode_id):
    gameplay_mode = get_object_or_404(GameplayMode, pk=gameplay_mode_id)

    template = loader.get_template('gameplay_mode.html')

    context = {
        'gameplay_mode' : gameplay_mode
    }

    return HttpResponse(template.render(context, request))

def gameplay_modes(request):
    gameplay_mode_list = GameplayMode.objects.all()

    template = loader.get_template('gameplay_modes.html')

    context = {
        'gameplay_mode_list' : gameplay_mode_list
    }

    return HttpResponse(template.render(context, request))

def graph(request, gameplay_mode_id):
    return HttpResponse('graph for ' + str(gameplay_mode_id))

def items(request, gameplay_mode_id):
    item_list = get_object_or_404(GameplayMode, pk=gameplay_mode_id).items.all()

    template = loader.get_template('items/items.html')

    context = {
        'item_list' : item_list,
        'gameplay_mode_id' : gameplay_mode_id
    }

    return HttpResponse(template.render(context, request))

def item(request, gameplay_mode_id, item_id):
    item = get_object_or_404(Item, pk=item_id)
    machine = get_object_or_None(Machine, item__id=item_id)

    template = loader.get_template('items/item.html')

    context = {
        'item' : item,
        'machine' : machine
    }

    return HttpResponse(template.render(context, request))

def researches(request, gameplay_mode_id):
    research_list = get_object_or_404(GameplayMode, pk=gameplay_mode_id).researches.all()

    template = loader.get_template('researches/researches.html')

    context = {
        'research_list' : research_list,
        'gameplay_mode_id' : gameplay_mode_id
    }

    return HttpResponse(template.render(context, request))

def research(request, gameplay_mode_id, research_id):
    research = get_object_or_404(Research, pk=research_id)

    unlocked_item_list = research.unlocked_items.all()

    template = loader.get_template('researches/research.html')

    context = {
        'research' : research,
        'gameplay_mode_id' : gameplay_mode_id,
        'unlocked_item_list' : unlocked_item_list
    }

    return HttpResponse(template.render(context, request))

def machines(request, gameplay_mode_id):
    gameplay_mode = get_object_or_404(GameplayMode, pk=gameplay_mode_id)

    machine_list = Machine.objects.filter(item__gameplay_mode__id=gameplay_mode_id)

    template = loader.get_template('machines/machines.html')

    context = {
        'machine_list' : machine_list,
        'gameplay_mode_id' : gameplay_mode_id
    }

    return HttpResponse(template.render(context, request))

def machine(request, gameplay_mode_id, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)

    template = loader.get_template('machines/machine.html')

    context = {
        'machine' : machine,
        'gameplay_mode_id' : gameplay_mode_id
    }

    return HttpResponse(template.render(context, request))

def recipes(request, gameplay_mode_id):
    recipe_list = get_object_or_404(GameplayMode, pk=gameplay_mode_id).recipes.all()

    template = loader.get_template('recipes/recipes.html')

    context = {
        'recipe_list' : recipe_list,
        'gameplay_mode_id' : gameplay_mode_id
    }

    return HttpResponse(template.render(context, request))

def recipe(request, gameplay_mode_id, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)

    template = loader.get_template('recipes/recipe.html')

    context = {
        'recipe' : recipe,
        'crafting_time_ticks' : recipe.crafting_time_ticks,
        'crafting_time_seconds' : recipe.crafting_time_ticks / 60
    }

    return HttpResponse(template.render(context, request))

def machine_types(request, gameplay_mode_id):
    machine_type_list = get_object_or_404(GameplayMode, pk=gameplay_mode_id).machine_types.all()

    template = loader.get_template('machine_types/machine_types.html')

    context = {
        'machine_type_list' : machine_type_list,
        'gameplay_mode_id' : gameplay_mode_id
    }

    return HttpResponse(template.render(context, request))

def machine_type(request, gameplay_mode_id, machine_type_id):
    machine_type = get_object_or_404(MachineType, pk=machine_type_id)

    machine_list = Machine.objects.filter(machine_type__id=machine_type_id)

    template = loader.get_template('machine_types/machine_type.html')

    context = {
        'machine_type' : machine_type,
        'gameplay_mode_id' : gameplay_mode_id,
        'machine_list' : machine_list
    }

    return HttpResponse(template.render(context, request))