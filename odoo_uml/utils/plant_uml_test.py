# -*- coding: utf-8 -*-
import unittest

from plant_uml import *


class TestCreole(unittest.TestCase):
    def setUp(self):
        pass

    def test_bold(self):
        self.assertEqual(
            bold('a'),
            '**a**'
        )

    def test_italic(self):
        self.assertEqual(
            italic('a'),
            '//a//'
        )

    def test_mono(self):
        self.assertEqual(
            mono('a'),
            '""a""'
        )

    def test_stroke(self):
        self.assertEqual(
            stroke('a'),
            '--a--'
        )

    def test_wave(self):
        self.assertEqual(
            wave('a'),
            '~~a~~'
        )


class TestStringUtil(unittest.TestCase):
    def setUp(self):
        self.util = StringUtil()

    def test_newline(self):
        self.assertEqual(self.util.newline().output(), '\n')

    def test_tab(self):
        self.assertEqual(self.util.tab().output(), '\t')

    def test_clear(self):
        self.assertEqual(self.util.clear().output(), '', "Clear failed!")

    def test_restart(self):
        self.assertEqual(
            self.util.append('A').restart().output(),
            ''
        )

    def test_append(self):
        self.assertEqual(self.util.append('A').output(), 'A')
        self.assertEqual(self.util.append('B').output(), 'AB')

    def test_push(self):
        self.assertEqual(
            self.util.append('A').push().output(),
            ''
        )
        self.assertEqual(
            self.util.pop().output(),
            'A'
        )

    def test_pop(self):
        self.assertEqual(
            self.util
            .append('A')
            .push()
            .append('B')
            .pop()
            .output(),
            'AB'
        )


class TestPlantUMLClassDiagram(unittest.TestCase):
    def setUp(self):
        self.diagram = PlantUMLClassDiagram()

    def test_begin_uml(self):
        self.assertEqual(
            self.diagram.begin_uml().end_uml().output(),
            '@startuml\nhide empty members\n@enduml'
        )

    def test_begin_package(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo')
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" {\n\t\n}\nhide empty members\n@enduml'
        )

    def test_begin_package_stetreotype(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo', stereotype='Cloud')
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" <<Cloud>> {\n\t\n}\nhide empty members\n@enduml'
        )

    def test_begin_package_alias(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo', stereotype='Cloud', alias='pd0000')
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" as pd0000 <<Cloud>> {\n\t\n}\nhide empty members\n@enduml'
        )

    def test_begin_package_color(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo', stereotype='Cloud', alias='pd0000', color='#DDDDDD')
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" as pd0000 <<Cloud>> #DDDDDD {\n\t\n}\nhide empty members\n@enduml'
        )

    def test_begin_package_inner(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .begin_package('demo', stereotype='Cloud', alias='pd0000', color='#DDDDDD')
            .begin_package('inner', stereotype='Cloud', alias='pd0001', color='#DDDDDD')
            .end_package()
            .end_package()
            .end_uml()
            .output(),
            '@startuml\npackage "demo" as pd0000 <<Cloud>> #DDDDDD {\n\tpackage "inner" as pd0001 <<Cloud>> '
            '#DDDDDD {\n\t\t\n\t}\n\t\n}\nhide empty members\n@enduml'
        )

    def test_add_dependency(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .add_dependency('A', 'B')
            .end_uml()
            .output(),
            '@startuml\nA ..> B\nhide empty members\n@enduml'
        )

    def test_add_dependency_alias(self):
        self.assertEqual(
            self.diagram
            .begin_uml()
            .add_dependency('A', 'B')
            .end_uml()
            .output(),
            '@startuml\nA ..> B\nhide empty members\n@enduml'
        )

    def test_add_floating_note(self):
        self.assertEqual(
            self.diagram
            .add_floating_note('A', 'a')
            .output(),
            'note "A" as a\n'
        )

    def test_add_title(self):
        self.assertEqual(
            self.diagram
            .add_title('A')
            .output(),
            'title A\n'
        )

    def test_begin_class(self):
        self.assertEqual(
            self.diagram
            .begin_class(
                name='A', alias='a', icon='A', icon_color='Yellow',
                stereotype='model', class_color='#Silver'
            )
            .end_class()
            .output(),
            'class "A" as a <<(A, Yellow) model>> #Silver {\n\t}\n'
        )

    def test_add_section(self):
        self.assertEqual(
            self.diagram
            .add_section()
            .output(),
            '--\n'
        )

    def test_end_class(self):
        self.assertEqual(
            self.diagram
            .begin_class('A')
            .end_class()
            .output(),
            'class A {\n\t}\n'
        )

    def test_add_attribute_composite(self):
        self.assertEqual(
            self.diagram
            .add_attribute(
                visibility='-',
                name='attr1',
                attr_type='int',
                tags=['inverse', 'compute']
            )
            .output(),
            '- attr1: int {inverse, compute}\n'
        )

    def test_add_attribute(self):
        self.assertEqual(
            self.diagram
            .add_attribute('- attr1: int {inverse, compute}')
            .output(),
            '- attr1: int {inverse, compute}\n'
        )

    def test_add_method(self):
        self.assertEqual(
            self.diagram
            .add_method('+ test(p1: int, p2: string): void {@api.depend}')
            .output(),
            '+ test(p1: int, p2: string): void {@api.depend}\n'
        )

    def test_add_method_composite(self):
        self.assertEqual(
            self.diagram
            .add_method(
                visibility='+',
                name='test',
                params=[
                    'self',
                    ('p1', 'int'),
                    ('p2', 'string')
                ],
                ret_type='string',
                tags=['@getter']
            )
            .output(),
            '+ test(self, p1: int, p2: string): string {@getter}\n'
        )

    def test_add_association(self):
        self.assertEqual(
            self.diagram
            .add_association(
                'A', 'B',
                card1='*',
                card2='id_b'
            )
            .output(),
            'A "*" -- "id_b" B\n'
        )

    def test_add_aggregation(self):
        self.assertEqual(
            self.diagram
            .add_aggregation(
                'A', 'B',
                card1='*',
                card2='id_b'
            )
            .output(),
            'A "*" o-- "id_b" B\n'
        )

    def test_add_composition(self):
        self.assertEqual(
            self.diagram
            .add_composition(
                'A', 'B',
                card1='*',
                card2='id_b'
            )
            .output(),
            'A "*" *-- "id_b" B\n'
        )

    def test_add_association_named(self):
        self.assertEqual(
            self.diagram
            .add_association(
                'A', 'B',
                card1='*',
                card2='id_b',
                name='has >'
            )
            .output(),
            'A "*" -- "id_b" B : has >\n'
        )

    def test_add_implementation(self):
        self.assertEqual(
            self.diagram
            .add_implementation('A', 'B')
            .output(),
            'B <|.. A\n'
        )

    def test_add_inherit(self):
        self.assertEqual(
            self.diagram
            .add_inherit('A', 'B')
            .output(),
            'B <|-- A\n'
        )


if __name__ == '__main__':
    unittest.main()
