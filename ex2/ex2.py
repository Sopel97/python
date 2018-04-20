import json
import sys
import re
from PIL import Image, ImageDraw

class Color:
    tuple_pattern = re.compile(r'\(([0-9]+)[,]([0-9]+)[,]([0-9]+)\)')
    html_pattern = re.compile(r'#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})')

    @classmethod
    def from_json(cls, json_node, palette=None):
        content = ''.join(json_node.split())
        match = Color.tuple_pattern.fullmatch(content)
        if match:
            return Color(int(match[1]), int(match[2]), int(match[3]))

        match = Color.html_pattern.fullmatch(content)
        if match:
            return Color(int(match[1], 16), int(match[2], 16), int(match[3], 16))

        if palette:
            return palette[content]

    def __init__(self, r, g, b):
        self._r = r
        self._g = g
        self._b = b

    def as_tuple(self):
        return (self._r, self._g, self._b)

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
    @classmethod
    def from_json(cls, json_node):
        palette = ColorPalette()
        for name, color in json_node.items():
            palette.add_color(name, Color.from_json(color))

        return palette

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

    def as_tuple(self):
        return (self._x, self._y)

    def __add__(self, other):
        return Point(self._x + other._x, self._y + other._y)

    def __sub__(self, other):
        return Point(self._x - other._x, self._y - other._y)

    def __repr__(self):
        return 'Point({}, {})'.format(self._x, self._y)

    def __str__(self):
        return self.__repr__()

    def draw(self, renderer, color):
        renderer.point(
            [self.as_tuple()],
            fill=color.as_tuple()
        )

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

    def draw(self, renderer, color):
        renderer.polygon(
            [p.as_tuple() for p in self._vertices],
            fill=color.as_tuple()
        )

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

    def draw(self, renderer, color):
        renderer.rectangle(
            [
                self._min.as_tuple(),
                self._max.as_tuple(),
            ],
            fill=color.as_tuple()
        )

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

    def draw(self, renderer, color):
        renderer.rectangle(
            [
                self._min.as_tuple(),
                (self._min + Point(self._size, self._size)).as_tuple(),
            ],
            fill=color.as_tuple()
        )

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

    def draw(self, renderer, color):
        r = Point(self._radius, self._radius)
        renderer.ellipse(
            [
                (self._origin - r).as_tuple(),
                (self._origin + r).as_tuple(),
            ],
            fill=color.as_tuple()
        )

class ColoredShape:
    @classmethod
    def from_json(cls, json_node, shape_cls, palette=None):
        return ColoredShape(shape_cls.from_json(json_node), Color.from_json(json_node['color'], palette))

    def __init__(self, shape, color):
        self._shape = shape
        self._color = color

    def __repr__(self):
        return 'ColoredShape({}, {})'.format(repr(self._shape), repr(self._color))

    def __str__(self):
        return self.__repr__()

    def draw(self, renderer):
        self._shape.draw(renderer, self._color)

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

    def draw(self, renderer):
        for shape in self._shapes:
            shape.draw(renderer)

class Canvas:
    @classmethod
    def from_json(cls, json_node, palette=None):
        return Canvas(
            json_node['width'],
            json_node['height'],
            Color.from_json(json_node['fg_color'], palette),
            Color.from_json(json_node['bg_color'], palette)
            )

    def __init__(self, width, height, fg_color, bg_color):
        self._width = width
        self._height = height
        self._fg_color = fg_color
        self._bg_color = bg_color
        self._image = Image.new('RGB', (width, height), bg_color.as_tuple())

        self._image

    def __repr__(self):
        return 'Canvas({}, {}, {}, {})'.format(self._width, self._height, repr(self._fg_color), repr(self._bg_color))

    def __str__(self):
        return self.__repr__()

    def save_to_file(self, file_name):
        self._image.save(file_name, 'PNG')

    def draw(self, drawable):
        renderer = ImageDraw.Draw(self._image)
        drawable.draw(renderer)

def main():
    json_content = json.load(open(sys.argv[1]))
    palette = ColorPalette.from_json(json_content['Palette'])
    canvas = Canvas.from_json(json_content['Screen'], palette)
    shapes = ShapeList.from_json(json_content['Figures'], palette)
    print(repr(shapes))
    print(repr(canvas))

    canvas.draw(shapes)
    canvas.save_to_file('out.png')


if __name__ == '__main__':
    main()