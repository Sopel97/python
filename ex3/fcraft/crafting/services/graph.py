class Graph:
    class Options:
        def __init__(self, **kwargs):
            self._dict = dict()

            for key, value in kwargs.items():
                self._dict[key] = value

        def __getitem__(self, key):
            keys = key.split('.');
            current = self._dict
            for key in keys:
                current = current[key]

            return current

        def __contains__(self, key):
            return self._dict.__contains__(key)

        def __setitem__(self, key, value):
            keys = key.split('.');
            current = self._dict
            num_keys = len(keys)
            for i in range(0, num_keys-1):
                k = keys[i]
                if k not in current:
                    current[k] = Graph.Options()
                current = current[k]

            current[keys[-1]] = value

        @classmethod
        def to_string(cls, value):
            if type(value) is bool:
                return 'true' if value == True else 'false'

            return repr(value)

        def to_vis_js_format(self):
            params =  ['{0}:{1}'.format(key, Graph.Options.to_string(value)) for key, value in self._dict.items()]

            return '{0}'.format(','.join(params))

        def __repr__(self):
            return '{{{0}}}'.format(self.to_vis_js_format())

    class Node:
        def __init__(self, group, node_id, **kwargs):
            self.group = group
            self.node_id = node_id
            self.options = Graph.Options(**kwargs)
            self.out_edges = []
            self.in_edges = []

        def to_vis_js_format(self):
            params = [
                'id:{!r}'.format(self.node_id)
            ]
            if self.group.name is not None:
                params += ['group:{!r}'.format(self.group.name)]
            params += [self.options.to_vis_js_format()]

            return '{{{0}}}'.format(','.join(params))

        def add_in_edge(self, edge):
            self.in_edges += [edge]

        def add_out_edge(self, edge):
            self.out_edges += [edge]

    class Edge:
        def __init__(self, group, from_id, to_id, **kwargs):
            self.group = group
            self.from_id = from_id
            self.to_id = to_id
            self.options = Graph.Options(**kwargs)

        def to_vis_js_format(self):
            params = [
                'from:{!r}'.format(self.from_id),
                'to:{!r}'.format(self.to_id)
            ]
            if self.group.name is not None:
                params += ['{0}:{1!r}'.format(key, value) for key, value in self.group.options.items()]
            params += [self.options.to_vis_js_format()]

            return '{{{0}}}'.format(','.join(params))

    class Group:
        def __init__(self, graph, name, **kwargs):
            self.graph = graph
            self.name = name
            self.options = Graph.Options(**kwargs)

        def add_option(self, key, val):
            self.options[key] = val

        def to_vis_js_format(self):
            params = [self.options.to_vis_js_format()]

            if self.name is None:
                return '{{{0}}}'.format(','.join(params))
            else:
                return '{0}:{{{1}}}'.format(self.name, ','.join(params))

    class NodeGroup(Group):
        def create_node(self, node_id, **kwargs):
            node = Graph.Node(self, node_id, **kwargs)
            self.graph.add_node(node)
            return node

    class EdgeGroup(Group):
        def create_edge(self, from_id, to_id, **kwargs):
            edge = Graph.Edge(self, from_id, to_id, **kwargs)
            self.graph.add_edge(edge)
            return edge

    def __init__(self):
        self.node_groups = dict()
        self.default_node_group = Graph.NodeGroup(self, None)
        self.edge_groups = dict()
        self.default_edge_group = Graph.EdgeGroup(self, None)
        self.options = Graph.Options()
        self.layout = Graph.Options()
        self.nodes = dict()

    @property
    def edges(self):
        for node_id, node in self.nodes.items():
            for edge in node.out_edges:
                yield edge

    def get_default_node_group(self):
        return self.default_node_group

    def get_default_edge_group(self):
        return self.default_edge_group

    def create_node_group(self, name, **kwargs):
        group = Graph.NodeGroup(self, name, **kwargs)
        self.node_groups[name] = group
        return group

    def create_edge_group(self, name, **kwargs):
        group = Graph.EdgeGroup(self, name, **kwargs)
        self.edge_groups[name] = group
        return group

    def add_node(self, node):
        self.nodes[node.node_id] = node

    def add_edge(self, edge):
        self.nodes[edge.from_id].add_out_edge(edge)
        self.nodes[edge.to_id].add_in_edge(edge)

    def to_vis_js_format(self, container_name):
        node_list = ','.join([node.to_vis_js_format() for node_id, node in self.nodes.items()])
        edge_list = ','.join([edge.to_vis_js_format() for edge in self.edges])
        node_group_list = ','.join([group.to_vis_js_format() for group_name, group in self.node_groups.items()])

        return ''.join(
            [
                'var nodes = new vis.DataSet([{}]);'.format(node_list),
                'var edges = new vis.DataSet([{}]);'.format(edge_list),
                'var options = {{{0}, groups:{{{1}}}}};'.format(self.options.to_vis_js_format(), node_group_list),
                'var container = document.getElementById({!r});'.format(container_name),
                'var data = { nodes:nodes, edges:edges };',
                'var network = new vis.Network(container, data, options);'
            ]
        )

