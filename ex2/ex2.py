import json
import sys
import re

class Color:
    tuple_pattern = re.compile(r'\(([0-9]+)[,]([0-9]+)[,]([0-9]+)\)')
    html_pattern = re.compile(r'#([0-9a-fA-F][0-9a-fA-F])([0-9a-fA-F][0-9a-fA-F])([0-9a-fA-F][0-9a-fA-F])')

    @classmethod
    def from_json(cls, json_node, palette):
        content = ''.join(json_node.split())
        match = Color.tuple_pattern.fullmatch(content)
        if match:
            return Color(int(match[1]), int(match[2]), int(match[3]))

        match = Color.html_pattern.fullmatch(content)
        if match:
            return Color(int(match[1], 16), int(match[2], 16), int(match[3], 16))

        return palette[content]

    def __init__(self, r, g, b):
        self._r = r
        self._g = g
        self._b = b

    @property
    def r(self):
        return self._r

    @property
    def g(self):
        return self._g

    @property
    def b(self):
        return self._b

    def __repr__(self):
        return '({}, {}, {})'.format(self._r, self._g, self._b)

    def __str__(self):
        return self.__repr__()

class ColorPalette:
    def __init__(self):
        self._colors = dict()

    def add_color(self, name, color):
        self._colors[name] = color

    def __getitem__(self, name):
        return self._colors[name]

class Shape:
    pass

class Point(Shape):
    @classmethod
    def from_json(cls, json_node):
        return Point(json_node['x'], json_node['y'])

    def __init__(self, x, y):
        self._x = x
        self._y = y

    def __add__(self, other):
        return Point(self._x + other._x, self._y + other._y)

    def __sub__(self, other):
        return Point(self._x - other._x, self._y - other._y)

    def __repr__(self):
        return 'Point({}, {})'.format(self._x, self._y)

    def __str__(self):
        return self.__repr__()

class Polygon(Shape):
    @classmethod
    def from_json(cls, json_node):
        return Polygon([Point(x, y) for x, y in json_node['points']])

    def __init__(self, vertices):
        self._vertices = vertices

    def __repr__(self):
        return 'Polygon({})'.format(repr(self._vertices))

    def __str__(self):
        return self.__repr__()

class Rectangle(Shape):
    @classmethod
    def from_json(cls, json_node):
        m = Point.from_json(json_node)
        return Rectangle(m, m + Point(json_node['width'], json_node['height']))

    def __init__(self, min, max):
        self._min = min
        self._max = max

    def __repr__(self):
        return 'Rectangle({}, {})'.format(repr(self._min), repr(self._max))

    def __str__(self):
        return self.__repr__()

class Square(Shape):
    @classmethod
    def from_json(cls, json_node):
        return Square(Point.from_json(json_node), json_node['size'])

    def __init__(self, min, size):
        self._min = min
        self._size = size

    def __repr__(self):
        return 'Square({}, {})'.format(repr(self._min), self._size)

    def __str__(self):
        return self.__repr__()

class Circle(Shape):
    @classmethod
    def from_json(cls, json_node):
        return Circle(Point.from_json(json_node), json_node['radius'])

    def __init__(self, origin, radius):
        self._origin = origin
        self._radius = radius

    def __repr__(self):
        return 'Circle({}, {})'.format(repr(self._origin), self._radius)

    def __str__(self):
        return self.__repr__()

class ColoredShape:
    @classmethod
    def from_json(cls, json_node, shape_cls, palette):
        return ColoredShape(shape_cls.from_json(json_node), Color.from_json(json_node['color'], palette))

    def __init__(self, shape, color):
        self._shape = shape
        self._color = color

    def __repr__(self):
        return 'ColoredShape({}, {})'.format(repr(self._shape), repr(self._color))

    def __str__(self):
        return self.__repr__()

class ShapeList:
    shape_types = {
        'point' : Point,
        'polygon' : Polygon,
        'rectangle' : Rectangle,
        'square' : Square,
        'circle' : Circle
    }

    @classmethod
    def from_json(cls, json_node, palette):
        shape_list = ShapeList()

        for json_shape_node in json_node:
            shape_type = ShapeList.shape_types[json_shape_node['type']]
            colored_shape = ColoredShape.from_json(json_shape_node, shape_type, palette)
            shape_list.add_shape(colored_shape)

        return shape_list

    def __init__(self):
        self._shapes = []

    def add_shape(self, shape):
        self._shapes.append(shape)

    def __repr__(self):
        return repr(self._shapes)

    def __str__(self):
        return str(self._shapes)


def main():
    palette = ColorPalette()
    palette.add_color('red', Color(255, 0, 0))
    palette.add_color('green', Color(0, 255, 0))
    palette.add_color('blue', Color(0, 0, 255))

    json_content = json.load(open(sys.argv[1]))
    print(repr(ShapeList.from_json(json_content['Figures'], palette)))

    print(palette['green'])

if __name__ == '__main__':
    main()