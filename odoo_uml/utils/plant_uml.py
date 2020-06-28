# -*- coding: utf-8 -*-


def bold(string):
    return '**{0}**'.format(string)


def italic(string):
    return '//{0}//'.format(string)


def mono(string):
    return '""{0}""'.format(string)


def stroke(string):
    return '--{0}--'.format(string)


def wave(string):
    return '~~{0}~~'.format(string)


def under(string):
    return '__{0}__'.format(string)


def tabs(size=0):
    str_tabs = ''
    while size > len(str_tabs):
        str_tabs += '\t'
    return str_tabs


class StringUtil(object):
    def __init__(self):
        self.buffer = str()
        self.stack = []

    def newline(self):
        return self.append('\n').append(tabs(len(self.stack)))

    def tab(self):
        return self.append('\t')

    def clear(self):
        self.buffer = str()
        return self

    def output(self):
        return self.buffer

    def restart(self):
        self.stack = []
        return self.clear()

    def append(self, string=''):
        self.buffer += string
        return self

    def push(self):
        self.stack.append(self.buffer)
        return self.clear()

    def pop(self):
        self.buffer = self.stack.pop() + self.buffer
        return self


class PlantUMLClassDiagram(StringUtil):
    def __init__(self, title=None, header=None, footer=None):
        super(PlantUMLClassDiagram, self).__init__()
        self.title = title
        self.header = header
        self.footer = footer

    def begin_uml(self):
        self.append('@startuml').newline()
        if self.title is not None:
            self.add_title(self.title).newline()

        if self.header is not None:
            self.add_header(self.header, 'right')
        return self

    def add_header(self, header, align='center'):
        if align not in [None, 'left', 'right', 'center']:
            align = None
        if align is not None:
            self.append('{0} '.format(align))
        return self.append('header').newline().append(header).newline().append('endheader').newline()

    def add_footer(self, footer, align='center'):
        if align not in [None, 'left', 'right', 'center']:
            align = None
        if align is not None:
            self.append('{0} '.format(align))
        return self.append('footer').newline().append(footer).newline().append('endfooter').newline()

    def begin_package(self, name, stereotype=None, color=None, alias=None):
        tokens = ['package', '"%s"' % str(name)]
        if alias is not None:
            tokens.extend(['as', str(alias)])
        if stereotype is not None:
            tokens.extend(['<<%s>>' % str(stereotype)])
        if color is not None:
            tokens.append(str(color))
        tokens.append('{')
        return self.append(' '.join(tokens)).push().newline()

    def add_dependency(self, name1='NoName1', name2='NoName2', alias1=None, alias2=None):
        tokens = [
            alias1 if alias1 is not None else name1,
            '..>',
            alias2 if alias2 is not None else name2
        ]
        return self.append(' '.join(tokens)).newline()

    def add_floating_note(self, note, alias):
        return self.append('note "{0}" as {1}'.format(note, alias)).newline()

    def add_title(self, title):
        return self.append('title {0}'.format(title)).newline()

    def end_package(self):
        return self.pop().newline().append('}').newline()

    def end_uml(self):
        if self.footer is not None:
            self.add_footer(self.footer, align='left')
        self.append('hide empty members').newline()
        return self.append('@enduml')

    # , stereotype=None, alias=None, icon=None, icon_color=None, class_color=None
    def begin_class(self, name, **kwargs):
        tokens = ['class']
        if kwargs.get('alias', None) is not None:
            tokens.append('"{0}" as {1}'.format(
                name,
                kwargs.get('alias')
            ))
        else:
            tokens.append(name)

        if kwargs.get('icon', None) is not None:
            if kwargs.get('stereotype', None) is not None:
                tokens.append('<<({0}, {1}) {2}>>'.format(
                    kwargs.get('icon'),
                    kwargs.get('icon_color', 'yellow'),
                    kwargs.get('stereotype')
                ))
            else:
                tokens.append('<<({0}, {1})>>'.format(
                    kwargs.get('icon'),
                    kwargs.get('icon_color', 'yellow')
                ))
        else:
            if kwargs.get('stereotype', None) is not None:
                tokens.append('<<{0}>>'.format(
                    kwargs.get('stereotype')
                ))

        if kwargs.get('class_color', None) is not None:
            tokens.append(kwargs.get('class_color'))

        tokens.append('{')
        self.append(' '.join(tokens)).push().newline()
        return self

    def add_section(self, sec_type='--', title=None):
        if title is None:
            return self.append(sec_type).newline()
        else:
            return self.append('{0} {1} {0}'.format(sec_type, title)).newline()

    def end_class(self):
        return self.pop().append('}').newline()

    # visibility='-', name='method', attr_type='string', tags=None, is_static=False, default
    def add_attribute(self, attribute=None, **kwargs):
        if attribute is not None:
            return self.append(attribute).newline()

        tokens = []
        if kwargs.get('is_static', False):
            tokens.append('{static}')
        if kwargs.get('visibility', None) is not None:
            tokens.append(kwargs.get('visibility'))

        if kwargs.get('attr_type', None) is None:
            tokens.append(kwargs.get('name', 'attr_no_name'))
        else:
            tokens.append('{0}: {1}'.format(
                kwargs.get('name', 'attr_no_name'),
                kwargs.get('attr_type')
            ))
        if 'default' in kwargs:
            tokens.append('=')
            if kwargs.get('default') is None:
                tokens.append('None')
            elif isinstance(kwargs.get('default'), str):
                tokens.append('\'{0}\''.format(kwargs.get('default')))
            else:
                tokens.append(str(kwargs.get('default')))

        self.append(' '.join(tokens))

        if kwargs.get('tags', None) is not None:
            if isinstance(kwargs.get('tags'), str):
                self.append(' {{{0}}}'.format(kwargs.get('tags')))
            if isinstance(kwargs.get('tags'), list):
                self.append(' {{{0}}}'.format(', '.join(kwargs.get('tags'))))

        return self.newline()

    # visibility=None, name=None, ret_type=None, params=None, tags=None
    def add_method(self, method=None, **kwargs):
        if method is not None:
            return self.append(method).newline()

        tokens = []
        if kwargs.get('is_static', False):
            tokens.append('{static}')
        else:
            if kwargs.get('is_abstract', False):
                tokens.append('{abstaract}')
        if kwargs.get('visibility', None) is not None:
            tokens.append(kwargs.get('visibility'))
        params = []
        if kwargs.get('params', None) is not None:
            if isinstance(kwargs.get('params'), str):
                params.append(kwargs.get('params'))
            if isinstance(kwargs.get('params'), list):
                for param in kwargs.get('params'):
                    if isinstance(param, str):
                        params.append(param)
                    if isinstance(param, tuple):
                        params.append('{0}: {1}'.format(*param))
        tokens.append('{0}({1})'.format(
            kwargs.get('name', 'no_named_method'),
            ', '.join(params)
        ))
        self.append(' '.join(tokens))

        if kwargs.get('ret_type', None) is not None:
            self.append(': {0}'.format(kwargs.get('ret_type')))

        if kwargs.get('tags', None) is not None:
            if isinstance(kwargs.get('tags'), str):
                self.append(' {{{0}}}'.format(kwargs.get('tags')))
            if isinstance(kwargs.get('tags'), list):
                self.append(' {{{0}}}'.format(', '.join(kwargs.get('tags'))))

        return self.newline()

    # card1, card2, name
    def add_association(self, alias1, alias2, **kwargs):
        tokens = [alias1]
        if kwargs.get('card1', None) is not None:
            tokens.append('"{0}"'.format(kwargs.get('card1')))
        tokens.append('--')
        if kwargs.get('card2', None) is not None:
            tokens.append('"{0}"'.format(kwargs.get('card2')))
        tokens.append(alias2)
        if kwargs.get('name', None) is not None:
            tokens.append(': {0}'.format(kwargs.get('name')))
        return self.append(' '.join(tokens)).newline()

    def add_composition(self, alias1, alias2, **kwargs):
        tokens = [alias1]
        if kwargs.get('card1', None) is not None:
            tokens.append('"{0}"'.format(kwargs.get('card1')))
        if kwargs.get('inverse', None):
            tokens.append('*-->')
        else:
            tokens.append('*--')
        if kwargs.get('card2', None) is not None:
            tokens.append('"{0}"'.format(kwargs.get('card2')))
        tokens.append(alias2)
        if kwargs.get('name', None) is not None:
            tokens.append(': {0}'.format(kwargs.get('name')))
        return self.append(' '.join(tokens)).newline()

    def add_aggregation(self, alias1, alias2, **kwargs):
        tokens = [alias1]
        if kwargs.get('card1', None) is not None:
            tokens.append('"{0}"'.format(kwargs.get('card1')))
        if kwargs.get('inverse', None):
            tokens.append('o-->')
        else:
            tokens.append('o--')
        if kwargs.get('card2', None) is not None:
            tokens.append('"{0}"'.format(kwargs.get('card2')))
        tokens.append(alias2)
        if kwargs.get('name', None) is not None:
            tokens.append(': {0}'.format(kwargs.get('name')))
        return self.append(' '.join(tokens)).newline()

    def add_implementation(self, alias1, alias2, label=None):
        if label is not None:
            return self.append('{1} <|.. {0} : {2}'.format(alias1, alias2, label)).newline()
        return self.append('{1} <|.. {0}'.format(alias1, alias2)).newline()

    def add_inherit(self, alias1, alias2):
        return self.append('{1} <|-- {0}'.format(alias1, alias2)).newline()

    def add_association_class(self, alias1, alias2, alias3, **kwargs):
        self.add_association(alias1, alias2, **kwargs)
        return self.append('({0}, {1}) .. {2}'.format(alias1, alias2, alias3)).newline()
