from django.http import HttpResponse
from django.template import loader
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from .models import *
from .services.graph import *

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

def graphs(request, gameplay_mode_id):
    template = loader.get_template('graphs/graphs.html')

    context = {
        'gameplay_mode_id' : gameplay_mode_id
    }

    return HttpResponse(template.render(context, request))

def create_full_graph(gameplay_mode_id):
    g = Graph()
    machine_group = g.create_node_group(name='machine', shape='box', color='yellow')
    item_group = g.create_node_group(name='item', shape='ellipse', color='#aaaaaa')
    collector_group = g.create_node_group(name='collector', shape='box', color='red')
    default_node_group = g.get_default_node_group()
    default_edge_group = g.get_default_edge_group()

    g.options['nodes.shape'] = 'dot'
    g.options['nodes.size'] = 20
    g.options['edges.arrows'] = 'to'
    g.options['edges.font.strokeWidth'] = 0
    g.options['edges.font.color'] = '#cccccc'
    g.options['edges.font.size'] = 14
    g.options['edges.font.align'] = 'top'
    g.options['edges.length'] = 150
    g.options['edges.smooth.type'] = 'continuous'
    g.options['layout.hierarchical.enabled'] = True
    g.options['layout.hierarchical.sortMethod'] = 'directed'
    g.options['layout.hierarchical.direction'] = 'UD'
    g.options['layout.hierarchical.parentCentralization'] = False
    g.options['layout.hierarchical.treeSpacing'] = 250
    g.options['layout.hierarchical.nodeSpacing'] = 200
    g.options['configure.enabled'] = False
    #g.options['configure.filter'] = 'nodes,edges'
    g.options['manipulation.enabled'] = True
    g.options['manipulation.deleteNode'] = True
    g.options['manipulation.addNode'] = False
    g.options['manipulation.addEdge'] = False
    g.options['manipulation.deleteEdge'] = False
    g.options['interaction.multiselect'] = True
    g.options['physics'] = False

    for item in Item.objects.filter(gameplay_mode__id=gameplay_mode_id):
        node_id = item.id
        item_group.create_node(node_id, label=item.name)

    best_machines = dict()
    for machine_type in MachineType.objects.filter(gameplay_mode__id=gameplay_mode_id):
        machines = machine_type.machines
        best_machines[machine_type.id] = max(machines.filter(gameplay_mode__id=gameplay_mode_id), key=lambda m: m.tier)

    best_collectors = dict()
    for resource_type in FiniteResourceType.objects.filter(gameplay_mode__id=gameplay_mode_id):
        collectors = resource_type.finite_resource_collectors
        best_collectors[resource_type.id] = max(collectors.filter(gameplay_mode__id=gameplay_mode_id), key=lambda m: m.tier)

    for finite_resource in FiniteResource.objects.filter(gameplay_mode__id=gameplay_mode_id):
        resource_type = finite_resource.finite_resource_type
        collector = best_collectors[resource_type.id]
        node_id = 'f{}'.format(finite_resource.id)
        collector_group.create_node(node_id, label=collector.item.name)

        collection_rate_rps = float((collector.mining_power - finite_resource.mining_hardness) * (collector.mining_speed / finite_resource.mining_time))

        for ingredient in finite_resource.collection_ingredients.filter(gameplay_mode__id=gameplay_mode_id):
            rate = float(collection_rate_rps*ingredient.count)
            default_edge_group.create_edge(ingredient.item.id, node_id, label='{:.3f}/s'.format(rate), transfer_rate=rate, base_transfer_rate=rate)

        default_edge_group.create_edge(node_id, finite_resource.item.id, label='{:.3f}/s'.format(collection_rate_rps), transfer_rate=collection_rate_rps, base_transfer_rate=collection_rate_rps)


    for recipe in Recipe.objects.filter(gameplay_mode__id=gameplay_mode_id):
        machine_type = recipe.executors.first().machine_type
        machine = best_machines[machine_type.id]
        node_id = 'r{}'.format(recipe.id)
        machine_group.create_node(node_id, label=machine.item.name)

        making_time_s = (float(recipe.crafting_time_ticks) / 60) / float(machine.crafting_speed)

        for ingredient in recipe.ingredients.filter(gameplay_mode__id=gameplay_mode_id):
            rate = float((1/making_time_s)*ingredient.count)
            default_edge_group.create_edge(ingredient.item.id, node_id, label='{:.3f}/s'.format(rate), transfer_rate=rate, base_transfer_rate=rate)

        for result in recipe.results.filter(gameplay_mode__id=gameplay_mode_id):
            rate = float((1/making_time_s)*result.count)
            default_edge_group.create_edge(node_id, result.item.id, label='{:.3f}/s'.format(rate), transfer_rate=rate, base_transfer_rate=rate)

    return g

def full_graph(request, gameplay_mode_id):
    template = loader.get_template('graphs/full_graph.html')

    g = create_full_graph(gameplay_mode_id)

    context = {
        'gameplay_mode_id' : gameplay_mode_id,
        'graph' : g.to_vis_js_format('mynetwork')
    }

    return HttpResponse(template.render(context, request))

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