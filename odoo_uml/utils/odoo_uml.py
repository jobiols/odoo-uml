# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################
import logging
import inspect
from os import path, unlink
from subprocess import Popen
from base64 import b64encode
from tempfile import NamedTemporaryFile

from openerp import models, _
from .plant_uml import PlantUMLClassDiagram, italic, bold

PIPE = -1
PLANT_UML_PATH = path.realpath(
    path.join(path.dirname(__file__), '..', 'bin', 'plantuml.jar')
)

API_DECORATORS = [
    'multi',
    'one',
    'model',
    'model_cr',
    'model_cr_context',
    'cr',
    'cr_context',
    'cr_uid',
    'cr_uid_context',
    'cr_uid_id',
    'cr_uid_id_context',
    'cr_uid_ids',
    'cr_uid_ids_context',
    'cr_uid_records',
    'cr_uid_records_context',
    'v8'
]


def GET_METHODS(CLS, module_name=None):
    import wdb;wdb.set_trace()

    members = inspect.getmembers(CLS, predicate=lambda m: inspect.ismethod(m))
    methods = []
    for name, value in members:
        if module_name:
            try:
                module = str(inspect.getmodule(value))
                if module_name in module:
                    methods.append(name)
            except AttributeError:
                pass
        else:
            methods.append(name)

    return methods

BASE_MODEL_METHODS = GET_METHODS(models.Model)
BASE_ABSTRACT_METHODS = GET_METHODS(models.AbstractModel)
BASE_TRANSIENT_METHODS = GET_METHODS(models.TransientModel)
EXCLUDE_METHODS = []

_logger = logging.getLogger(__name__)


class UtilMixin(object):
    @staticmethod
    def execute_cmd(*args):
        ''' Execute external command in system context.

            :param list *args: a list of string to build and exec command.
            :return: excecution standar output.
            :rtype: str
        '''
        _logger.info('Run external command: %s.', ' '.join(args))
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        std_out = str()
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                std_out += line
                _logger.info(line)
        return std_out

    @staticmethod
    def produce_alias(string):
        return string.replace(' ', '_').replace('.', '_').lower()

    @staticmethod
    def produce_model_alias(module, model):
        return UtilMixin.produce_alias('{0}_{1}'.format(module.name, model.model))

    def to_puml(self):
        ''' Override this method with correct PlantUML generation strategy.
        '''
        raise NotImplementedError()

    def to_png_base64(self):
        ''' Return diagram as PNG in base64 encode.

            :return: image as base64 encoded.
            :rtype: string
        '''
        b64image, self.log = self._produce_diagram_image()
        return b64image

    def _produce_diagram_image(self):
        f_out_puml = NamedTemporaryFile(mode='w', delete=False)
        f_out_puml.write(self.to_puml())
        f_out_puml.close()

        log = UtilMixin.execute_cmd(
            'java', '-jar', PLANT_UML_PATH, '-tpng', '-v',
            f_out_puml.name, '-o', '"%s"' % path.dirname(f_out_puml.name)
        )

        f_out_diagram = open("%s.png" % f_out_puml.name,'rb')
        image = b64encode(f_out_diagram.read())
        f_out_diagram.close()

        unlink(f_out_puml.name)
        unlink(f_out_diagram.name)

        return image, log


class ClassDiagram(PlantUMLClassDiagram, UtilMixin):
    ''' Parse Module and generate Models Class Diagram.
    '''

    def __init__(self, module, title=None, header=None, footer=None, **kwargs):
        self._marks = []  #: Useful marks.
        self._dependecy_index = []  #: A ordered module list of dependencies priorities.
        self._module = module       #: A module.
        #: Hash dictionary when module name is key and list of models in module is a value.
        self._module_models = {}
        self._config = kwargs       #: Initial config options.
        self._puml = None           #: PlantUML generated.
        UtilMixin.__init__(self)
        PlantUMLClassDiagram.__init__(
            self,
            title=title,
            header=header,
            footer=footer
        )

    @staticmethod
    def list_models(module):
        ''' List all models in a module.

            :param ir.module.module module: modulo.
            :return: a model list inside module.
            :rtype: ir.model[]
        '''
        models = module.env['ir.model'].sudo().search([])
        found = []
        for model in models:
            if module.name in model.modules.split(', '):
                found.append(model)
        return found

    @staticmethod
    def produce_model_name(model, **kwargs):
        ''' Produce a model name for class. Apply CamelCaseNotation at name.

            :param ir.model model: model.
            :param bool show_original_model_name: include name in tags using natural odoo notation.
            :param bool from_external_module: include in tags external module name.
            :return: string model name acts a class PlantUML name's.
            :rtype: str
        '''
        name_format = '{0}'
        if not isinstance(model, str):
            model = model.model

        # Abstract class with name in italic
        if kwargs.get('stereotype', None) in ['abstract']:
            name_format = italic(name_format)

        name = name_format.format(
            ''.join([sub.capitalize() for sub in model.replace('_', '.').split('.')])
        )
        tags = []
        # Show as tag the original name of model if not "show_model_onfig_options".
        if kwargs.get('show_original_model_name', False):
            tags.append('name=\'{0}\''.format(model))

        if tags:
            name += '\\n{{{0}}}'.format(
                ', '.join(tags)
            )

        # If from dependency module add module name
        if kwargs.get('from_external_module', None) is not None:
            name += '\\n//(from **{0}**)//'.format(
                kwargs.get('from_external_module').name
            )

        return name

    @staticmethod
    def produce_model_stereotype(model, **kwargs):
        ''' Evaluate model and produce steretype fully tuple with 3 elements
            (stereotype, class_icon, icon_color) according to options. Note: class_icon can by
            'M' if model is regular model, or 'A' if abstract model, or 'W' for transient model (common used
            for wizards).

            :param ir.model model: a model.
            :param str color_transient_model_icon: icon color if model is transient (default 'SteelBlue').
            :param str color_normal_model_icon: icon color in normal model (default 'Darkorange').
            :param str color_abstract_model_icon: icon color in abstract model (default 'Gray').
            :return: a ternary tuple with stereotype, class_icon, icon_color.
            :rtype: tuple
        '''
        rec = ClassDiagram.record_model(model)
        class_stereotype, class_icon, icon_color = 'model', 'M', kwargs.get('color_normal_model_icon', 'Darkorange')
        if model.transient:
            class_stereotype, class_icon = 'transient', 'W'
            icon_color = kwargs.get('color_transient_model_icon', 'SteelBlue')
        if rec._abstract:
            class_stereotype, class_icon = 'abstract', 'A'
            icon_color = kwargs.get('color_abstract_model_icon', 'Gray')
        return class_stereotype, class_icon, icon_color

    @staticmethod
    def record_model(model):
        ''' Return a record for model.

            :return: model.env[model.model]
        '''
        return model.env[model.model].sudo()

    @staticmethod
    def record_field(field):
        ''' Return a field object form ir.model.fields

            :return: ClassDiagram.record_model(field.model_id)._fields[field.name]
        '''
        return ClassDiagram.record_model(field.model_id)._fields[field.name]

    def __check_requeriments(self):
        if self._module.state == 'uninstalled':
            self.add_floating_note(
                _('Module not installed. Please install it first.'),
                '{0}_not_installed'.format(self._module.name)
            )

        if not self._module_models[self._module.name] and self._module.state == 'installed':
            self.add_floating_note(
                _('No models detected in module.'),
                '{0}_no_models'.format(self._module.name)
            )

        return self

    @staticmethod
    def _get_field_properties(field):
        properties_name = [
            # Common
            'default',  # None
            'states',   # None
            'index',    # False
            'size',     # None
            'translate',  # False
            'groups',  # None
            'domain',  # None
            'deprecated',  # undefinef or None
            'inherited',  # if appear in inherits
            # Related Attributes
            'related',  # default None if not then store is False and copy False
            # Compute Attributes
            'compute',
            'inverse',
            'search',
            # Company Depends
            'company_dependent',
            # Sparse
            'sparse',
            # Extra properties
            'group_operator',
            'readonly',
            'store',
            'copy',
            'manual',
            'required',
            'name',
            'args',
            'inverse_name',  # one2many
            'auto_join',     # one2many, many2one
            'delegate'  # in inherits
        ]
        properties = dict.fromkeys(properties_name, None)
        rec_field = ClassDiagram.record_field(field)
        for key in properties_name:
            properties[key] = getattr(rec_field, key, None)
        return properties

    def inverse_field_many2one(self, model, field):
        module_2o, model_2o = self._resolve(field.relation)
        for field_2o in model_2o.field_id.filtered(lambda r: r.ttype == 'one2many'):
            properties = ClassDiagram._get_field_properties(field_2o)
            if properties['inverse_name'] == field.name and field_2o.relation == model.model:
                return field_2o
        return None

    def produce_attribute_features_tags(self, field, **kwargs):
        tags = []
        properties = ClassDiagram._get_field_properties(field)
        # Attribute critical features, always show.
        if properties['required']:
            tags.append('required')
        if properties['readonly']:
            tags.append('readonly')

        # If feature "show_attribute_features" enabled then include tags.
        if kwargs.get('show_attribute_features', True):
            if properties['group_operator'] is not None and 'group_operator' in properties['args']:
                tags.append('//group//=\'{0}\''.format(properties['group_operator']))
            if properties['related']:
                tags.append('//related//=\'{0}\''.format('.'.join(properties['related'])))
                if properties['store'] and 'store' not in tags:
                    tags.append(italic('store'))
                if properties['copy'] and 'copy' not in tags:
                    tags.append(italic('copy'))
            elif properties['compute'] or properties['company_dependent']:
                if properties['compute']:
                    tags.append(italic('compute'))
                if properties['company_dependent']:
                    tags.append(italic('property'))
                if properties['store'] and 'store' not in tags:
                    tags.append(italic('store'))
                if properties['copy'] and 'copy' not in tags:
                    tags.append(italic('copy'))
                if properties['inverse']:
                    tags.append(italic('inverse'))
                else:
                    if 'readonly' not in tags:
                        tags.append(italic('readonly'))
                if properties['search']:
                    tags.append(italic('search'))

            if properties['groups']:
                tags.append(italic('groups'))
            if properties['states']:
                tags.append(italic('states'))
            if properties['index']:
                tags.append(italic('index'))
            if properties['domain']:
                tags.append('domain')
            if properties['translate']:
                tags.append('translate')
            if properties['manual']:
                tags.append('manual')
            if properties['auto_join']:
                tags.append('autojoin')
            if callable(properties['default']):
                tags.append('default')
            # TODO: Override and Overrided
        return tags

    def produce_attribute(self, field, **kwargs):
        properties = ClassDiagram._get_field_properties(field)
        # No produce attribute if it is an inherits (part of delegation inheritance)
        if properties['delegate']:
            return self
        tags = self.produce_attribute_features_tags(field, **kwargs)
        attr_type = bold(field.ttype.capitalize())
        if field.ttype in ['char', 'reference'] and field.size:
            attr_type = '{0}({1})'.format(attr_type, field.size)
        if field.ttype in ['many2one']:
            attr_type = '{0}'.format(bold(ClassDiagram.produce_model_name(field.relation)))
        if field.ttype in ['one2many', 'many2many']:
            attr_type = '{0}[]'.format(bold(ClassDiagram.produce_model_name(field.relation)))
            if field.ttype == 'many2many':
                tags.append(italic('many2many'))

        attr_def = {
            'visibility': '+',
            'name': field.name,
            'attr_type':  attr_type
        }

        if tags:
            attr_def['tags'] = ', '.join(tags)

        return self.add_attribute(**attr_def)

    def produce_attributes(self, model, **kwargs):
        ''' Produce attributes for model.

            :return: self
            :rtype: ClassDiagram
        '''
        if not kwargs.get('show_model_attributes', True):
            return self

        inherited_field = 0
        for field in model.field_id:
            # Exclude __las_update (concurrency check field) and display_name
            if field.name in ['__last_update', 'display_name']:
                continue
            # Exclude log attributes
            if not kwargs.get('show_log_attributes', False):
                if field.name in ['create_date', 'write_date', 'create_uid', 'write_uid']:
                    continue
            # If feature "show_only_own_attrs" disabled all fields are included.
            if self._module.name not in field.modules.split(', ') and kwargs.get('show_only_own_attrs', True):
                inherited_field += 1
                continue
            self.produce_attribute(field, **kwargs)

        if inherited_field > 0:
            self.add_attribute('//...and {0} others inherited attr.//'.format(inherited_field))
        return self

    def produce_model_features_options(self, model, **kwargs):
        ''' Produce model features in a first class section.

            :param ir.model model: a model.
            :param bool show_model_config_options: enable show feature config options for model (default True).
            :return: self
            :rtype: ClassDiagram
        '''
        # Show model features options
        rec = ClassDiagram.record_model(model)
        if kwargs.get('show_model_config_options', True):
            if rec._inherit is not None:
                if isinstance(rec._inherit, str):
                    self.add_attribute('_inherit = \'{0}\''.format(rec._inherit))
                    if model.model != rec._inherit:
                        self.add_attribute('_name = \'{0}\''.format(model.model))
                if isinstance(rec._inherit, list):
                    if model.model != rec._inherit[0]:
                        self.add_attribute('_name = \'{0}\''.format(model.model))
                    if len(rec._inherit) > 1:
                        self.add_attribute('_inherit = [{0}]'.format(
                            ', '.join(['\'{0}\''.format(inherit) for inherit in rec._inherit])
                        ))
                    else:
                        self.add_attribute('_inherit = \'{0}\''.format(rec._inherit[0]))
            else:
                self.add_attribute('_name = \'{0}\''.format(model.model))

            if rec._table is not None and rec._table != model.model.replace('.', '_'):
                self.add_attribute('_table = \'{0}\''.format(rec._table))
            if not rec._auto:
                self.add_attribute('_auto = False')
            if rec._date_name != 'date':
                self.add_attribute('_date_name = \'{0}\''.format(rec._date_name))
            if rec._fold_name != 'fold':
                self.add_attribute('_fold_name = \'{0}\''.format(rec._fold_name))
            if rec._rec_name is not None and rec._rec_name != 'name':
                self.add_attribute('_rec_name = \'{0}\''.format(rec._rec_name))
            if rec._order != 'id':
                self.add_attribute('_order = \'{0}\''.format(rec._order))
            # MPTT
            if rec._parent_name != 'parent_id':
                self.add_attribute('_parent_name = \'{0}\''.format(rec._parent_name))
            if rec._parent_store:
                self.add_attribute('_parent_store = True')
            if rec._parent_order:
                self.add_attribute('_parent_order = {0}'.format(rec._parent_order))

            if rec._inherits:
                self.add_section('..', '//inherits from//')
                for model, field in rec._inherits.iteritems():
                    self.add_attribute('+ {0}:{1}'.format(
                        field, bold(ClassDiagram.produce_model_name(model))
                    ))

            self.add_section('==')
        return self

    def __detect_methods(self, model):
        module, model = self._resolve(model.model)
        rec = ClassDiagram.record_model(model)
        methods = GET_METHODS(rec, module.name)
        overrrides = []
        bases = [rec._inherit] if isinstance(rec._inherit, str) else rec._inherit
        bases_methods = []

        if not bases:
            if isinstance(model, models.TransientModel):
                rec_base = models.TransientModel
                bases_methods = BASE_TRANSIENT_METHODS
            elif isinstance(model, models.Model):
                rec_base = models.Model
                bases_methods = BASE_MODEL_METHODS
            elif isinstance(model, models.AbstractModel):
                rec_base = models.AbstractModel
                bases_methods = BASE_ABSTRACT_METHODS
            bases = [False]
        for base in bases:
            if base:
                module_base, model_base = self._resolve(base, near=model.model != base)
                if module_base is None or model_base is None:
                    continue
                rec_base = ClassDiagram.record_model(model_base)
                bases_methods = GET_METHODS(rec_base, module_name=module_base.name)
            for method in bases_methods:
                if method in methods:
                    # are equal?
                    base_method = getattr(rec_base, method).__func__
                    own_method = getattr(rec, method).__func__
                    if base_method == own_method:
                        methods.remove(method)
                    else:
                        overrrides.append(method)
        return methods, overrrides

    def produce_methods(self, model, **kwargs):
        if not kwargs.get('show_model_methods', True):
            return self

        methods, overrides = self.__detect_methods(model)
        rec = ClassDiagram.record_model(model)
        hash_methods = {key: value for key, value in inspect.getmembers(rec)}
        if methods:
            self.add_section()
        for method in methods:
            if method.startswith('__'):
                visibility = '-'
            elif method.startswith('_'):
                visibility = '#'
            else:
                visibility = '+'

            params = inspect.formatargspec(*inspect.getargspec(hash_methods[method]))[1:-1]
            tags = []
            if method in overrides:
                tags.append('//override//')
            try:
                if hash_methods[method]._api in API_DECORATORS:
                    tags.append(italic(hash_methods[method]._api))
            except AttributeError:
                pass
            self.add_method(
                visibility=visibility,
                name=method,
                params=params,
                tags=tags if tags else None
            )

    def produce_constraints(self, model, **kwargs):
        pass

    def ensure_external_model(self, module, model, **kwargs):
        alias_inherit = UtilMixin.produce_model_alias(module, model)
        if alias_inherit not in self._marks:
            self._marks.append(alias_inherit)
            self.produce_class(model, **dict(
                kwargs,
                from_external_module=module,
                show_model_config_options=False,
                show_model_attributes=False,
                show_model_methods=False,
                show_model_constrains=False,
                show_original_model_name=False
            ))

    def add_delegation_inheritance(self, alias1, alias2, field):
        return self.append('{1} "{2}" <|--* {0}'.format(alias1, alias2, field)).newline()

    @staticmethod
    def __default_m2m_namerel(model, comodel):
        model = ClassDiagram.record_model(model)
        comodel = ClassDiagram.record_model(comodel)
        tables = sorted([model._table, comodel._table])
        if tables[0] == tables[1]:
            _logger.error("Fail M2M default relation: %s", tables[0])
        return '%s_%s_rel' % tuple(tables)

    def __produce_m2m_classrel(self, **kwargs):
        alias = UtilMixin.produce_alias('{0}_{1}'.format(self._module.name, kwargs.get('relation')))
        if alias not in self._marks:
            self._marks.append(alias)
            self.begin_class(
                name=ClassDiagram.produce_model_name(kwargs.get('relation')),
                stereotype='table',
                icon='T',
                alias=alias
            )
            # Attributes
            self.add_attribute(
                visibility='+',
                name=kwargs.get('column1'),
                attr_type=bold(ClassDiagram.produce_model_name(kwargs.get('model')))
            )
            self.add_attribute(
                visibility='+',
                name=kwargs.get('column2'),
                attr_type=bold(ClassDiagram.produce_model_name(kwargs.get('comodel')))
            )
            self.end_class()

            self.add_association_class(
                ClassDiagram.produce_model_alias(
                    kwargs.get('module'), kwargs.get('model')
                ),
                ClassDiagram.produce_model_alias(
                    kwargs.get('comodule'), kwargs.get('comodel')
                ),
                alias,
                card1='*',
                card2='*'
            )
        return self

    def produce_many2many_association(self, model, **kwargs):
        for field in model.field_id.filtered(lambda r: r.ttype == 'many2many'):
            # If feature "show_only_own_attrs" disabled all fields are included.
            if self._module.name not in field.modules.split(', ') and kwargs.get('show_only_own_attrs', True):
                continue

            rec = ClassDiagram.record_model(model)
            rec_field = ClassDiagram.record_field(field)
            module_2m, model_2m = self._resolve(rec_field.comodel_name)
            if module_2m is None or model_2m is None:
                _logger.warn(
                    "Extrange many2many relationship in %s, %s for %s",
                    model.model, field.name, rec_field.comodel_name
                )
                return self
            rec_m2 = ClassDiagram.record_model(model_2m)
            if module_2m.name != self._module.name:
                self.ensure_external_model(module_2m, model_2m, **kwargs)
            relation = rec_field.relation
            if not relation:
                relation = field.relation_table
            if not relation:
                _logger.warn(
                    "Need a default M2M relation with: %s and %s. Field relations: %s and %s",
                    model.model, model_2m.model, rec_field.relation, field.relation_table
                )
                relation = ClassDiagram.__default_m2m_namerel(model, model_2m)
            column1 = rec_field.column1 if rec_field.column1 else '%s_id' % rec._table
            column2 = rec_field.column2 if rec_field.column2 else '%s_id' % rec_m2._table
            module_rel, model_rel = self._resolve(relation)
            # If defined then ensure
            if model_rel:
                self.ensure_external_model(module_rel, model_rel, **kwargs)
            else:
                self.__produce_m2m_classrel(**dict(
                    kwargs,
                    model=model,
                    module=self._module,
                    field=field,
                    comodel=model_2m,
                    comodule=module_2m,
                    relation=relation,
                    column1=column1,
                    column2=column2
                ))

        return self

    def produce_association(self, model, **kwargs):
        for field in model.field_id.filtered(lambda r: r.ttype in ['many2one', 'one2many']):
            # Exclude log attributes
            if not kwargs.get('show_log_attributes', False):
                if field.name in ['create_uid', 'write_uid']:
                    continue
            # If feature "show_only_own_attrs" disabled all fields are included.
            if self._module.name not in field.modules.split(', ') and kwargs.get('show_only_own_attrs', True):
                continue

            properties = ClassDiagram._get_field_properties(field)
            # No produce attribute if it is an inherits (part of delegation inheritance)
            if properties['delegate']:
                return self

            module_2o, model_2o = self._resolve(field.relation)
            self.ensure_external_model(module_2o, model_2o, **kwargs)
            alias1 = UtilMixin.produce_model_alias(self._module, model)
            alias2 = UtilMixin.produce_model_alias(module_2o, model_2o)
            relation = None
            if field.ttype == 'many2one':
                if module_2o is None or model_2o is None:
                    _logger.info("Extrange many2one relationship in %s", model.name)
                    return self
                inverse = self.inverse_field_many2one(model, field)
                relation = dict(
                    alias1=alias1,
                    alias2=alias2,
                    card1='{0} *'.format(inverse.name) if inverse is not None else '*',
                    card2='{0} 1'.format(field.name),
                    name='<<restrict>>' if field.on_delete == 'restrict' else None,
                    inverse=inverse
                )

            if field.ttype == 'one2many' and module_2o.name != self._module.name:
                properties = ClassDiagram._get_field_properties(field)
                inverse = properties['inverse_name']
                relation = dict(
                    alias1=alias2,
                    alias2=alias1,
                    card1='{0} *'.format(inverse.name) if inverse is not None else '*',
                    card2='{0} 1'.format(field.name),
                    name='<<restrict>>' if field.on_delete == 'restrict' else None,
                    inverse=inverse
                )

            # Probably one2many in this module will be generate from many2one of other model
            if relation is None:
                return self

            if field.on_delete in ['cascade', 'restrict']:
                self.add_composition(**relation)
            else:
                self.add_aggregation(**relation)

        return self

    def produce_inherits_relations(self, model, **kwargs):
        rec = ClassDiagram.record_model(model)
        for inherit, field in rec._inherits.iteritems():
            module_inherit, model_inherit = self._resolve(inherit)
            if model_inherit is None or module_inherit is None:
                _logger.info("Extrange inherith(s) in %s", model.name)
                return self
            self.ensure_external_model(module_inherit, model_inherit, **kwargs)
            # Delegation (Delegation Inheritance)
            self.add_delegation_inheritance(
                UtilMixin.produce_model_alias(self._module, model),
                UtilMixin.produce_model_alias(module_inherit, model_inherit),
                field
            )

    def produce_inherit_relations(self, model, **kwargs):
        rec = ClassDiagram.record_model(model)
        inherit_list = rec._inherit if isinstance(rec._inherit, (list, tuple,)) else [rec._inherit]
        for inherit in inherit_list:
            # two posibilities
            if model.model == inherit:
                module_inherit, model_inherit = self._resolve(inherit, near=False)
                if model_inherit is None or module_inherit is None:
                    _logger.warn("Extrange inherith in %s (Class Inheritance) with %s", model.model, inherit)
                    return self
                self.ensure_external_model(module_inherit, model_inherit, **kwargs)
                # Extension (Class Inheritance)
                self.add_implementation(
                    UtilMixin.produce_model_alias(self._module, model),
                    UtilMixin.produce_model_alias(module_inherit, model_inherit),
                    label='<<extend>>'
                )
            else:
                module_inherit, model_inherit = self._resolve(inherit)
                if model_inherit is None or module_inherit is None:
                    _logger.warn("Extrange inherith in %s (Prototype Inheritance) with %s", model.model, inherit)
                    return self
                self.ensure_external_model(module_inherit, model_inherit, **kwargs)
                # Prototype (Prototype Inheritance)
                self.add_inherit(
                    UtilMixin.produce_model_alias(self._module, model),
                    UtilMixin.produce_model_alias(module_inherit, model_inherit)
                )
        return self

    def produce_class_relation(self, model, **kwargs):
        # inherit
        rec = ClassDiagram.record_model(model)
        if rec._inherit is not None:
            self.produce_inherit_relations(model, **kwargs)
        # inherits
        if rec._inherits:
            self.produce_inherits_relations(model, **kwargs)
        # composite & aggregate
        self.produce_association(model, **kwargs)
        # many2many
        self.produce_many2many_association(model, **kwargs)
        # enums
        return self

    def produce_relations_from_models(self):
        if self._config.get('show_relations', True):
            for model in self._module_models[self._module.name]:
                self.produce_class_relation(model, **self._config)

    def produce_class(self, model, **kwargs):
        class_stereotype, class_icon, icon_color = ClassDiagram.produce_model_stereotype(model, **kwargs)
        if kwargs.get('from_external_module', None) is not None:
            module = kwargs.get('from_external_module')
        else:
            module = self._resolve_module(model)
        model_alias = UtilMixin.produce_alias('{0}_{1}'.format(module.name, model.model))

        if 'show_original_model_name' not in kwargs:
            show_original_model_name = not kwargs.get('show_model_config_options', True)
        else:
            show_original_model_name = kwargs.get('show_original_model_name')

        self.begin_class(
            ClassDiagram.produce_model_name(model, **dict(
                kwargs,
                stereotype=class_stereotype,
                show_original_model_name=show_original_model_name
            )),
            alias=model_alias,
            icon=class_icon,
            icon_color=icon_color,
            stereotype=class_stereotype,
            class_color='#Yellow' if module == self._module else None
        )

        self.produce_model_features_options(model, **kwargs)
        self.produce_attributes(model, **kwargs)
        self.produce_methods(model, **kwargs)
        self.produce_constraints(model, **kwargs)

        return self.end_class()

    def produce_classes_from_models(self):
        for model in self._module_models[self._module.name]:
            model_alias = UtilMixin.produce_model_alias(self._module, model)
            if model_alias not in self._marks:
                self._marks.append(model_alias)
                self.produce_class(model, **self._config)

    def to_puml(self):
        if self._puml is None:
            self.begin_uml()
            self._produce_modules_models_herarchy()
            self.__check_requeriments()
            self.produce_classes_from_models()
            self.produce_relations_from_models()
            self._puml = self.end_uml().output()
        return self._puml

    def _produce_modules_models_herarchy(self):
        ''' Produce internal index with a WidthFirstSearch algorithm over dependecy
            hierarchy. Create a hash of models for each module.

            :return: self
            :rtype: ClassDiagram
        '''
        self._dependecy_index = []
        self._marks = []
        self._module_models = {}
        self._alias_hash = {}

        stack1, stack2 = [self._module], []
        while stack1:
            mod = stack1.pop()
            self._marks.append(mod.name)
            self._dependecy_index.append(mod)
            self._module_models[mod.name] = ClassDiagram.list_models(mod)
            # buil alias hash
            for model in self._module_models[mod.name]:
                alias = UtilMixin.produce_alias('{0}_{1}'.format(mod.name, model.model))
                self._alias_hash[alias] = model
            for dependency in mod.dependencies_id:
                dep = dependency.depend_id
                if dep.name not in self._marks:
                    stack2.append(dep)
            if not stack1:
                stack1, stack2 = stack2, []

        self._marks = []
        return self

    def _resolve_module(self, model, near=True):
        ''' Search in dependency herarchy the first module that contains the model. If
            model not found return None.

            :param ir.model|str model: a model to resolve module.
            :return: module.
            :rtype: ir.module.module
        '''
        model_name = model if isinstance(model, str) else model.model
        dependency = self._dependecy_index if near else self._dependecy_index[1:]
        for module in dependency:
            if model_name in [mod.model for mod in self._module_models[module.name]]:
                return module

        return self._module

    def _resolve_model(self, name, near=True):
        dependency = self._dependecy_index if near else self._dependecy_index[1:]
        for module in dependency:
            for model in self._module_models[module.name]:
                if model.model == name:
                    return model

        return None

    def _resolve(self, model_name, near=True):
        dep = self._dependecy_index if near else self._dependecy_index[1:]
        for module in dep:
            for model in self._module_models[module.name]:
                if model_name == model.model:
                    return module, model
        return None, None


class PackageDiagram(ClassDiagram):
    ''' Parse module and generate Module Dependecy Diagram
    '''
    @staticmethod
    def produce_package_name(module, **kwargs):
        ''' Produce package name from module object (ir.module.module) and some config options:
            -   show_package_status: show module install status as tag.
            -   show_descriptive_name: show human descriptive name.

            :param ir.module.module module: module object
            :param bool show_package_status: (default True)
            :param bool show_descriptive_name: (default False)
            :return: package name formated
            :rtype: str
        '''
        tags = []
        if module.auto_install:
            tags.append('auto-install')

        if kwargs.get('show_package_status', True):
            tags.append('state=\'{0}\''.format(module.state))

        if kwargs.get('show_descriptive_name', False):
            tags.insert(0, 'name=%s' % module.name)
            return u'{0}\\n{{{1}}}'.format(module.short_desc, ', '.join(tags))

        if tags:
            return u'{0}\\n{{{1}}}'.format(module.name, ', '.join(tags))

        return module.name

    @staticmethod
    def produce_package_stereotype(module, **kwargs):
        ''' Produce package stereotype for module, it can be <<application>> or <<module>>.

            :param str module_application_stereotype: (default 'application')
            :param str module_module_stereotype: (default 'module')
            :return: stereotype
            :rtype: str
        '''
        if module.application:
            return kwargs.get('module_application_stereotype', 'application')
        else:
            return kwargs.get('module_module_stereotype', 'module')

    @staticmethod
    def produce_package_color(module, **kwargs):
        ''' Produce package color according to module is appliation or not.

            :param str color_application_package: a valid PlantUML color constant (default '#Silver').
            :param str color_module_package: a valid PlantUML color constant -for module- (default '#White').
            :return: a color constant.
            :rtype: str
        '''
        if module.application:
            return kwargs.get('color_application_package', '#Silver')
        else:
            return kwargs.get('color_module_package', '#White')

    def __init__(self, module, title=None, header=None, footer=None, **kwargs):
        super(PackageDiagram, self).__init__(
            module,
            title=title,
            header=header,
            footer=footer,
            **kwargs
        )

    def produce_package(self, module, **kwargs):
        ''' Produce a new package into diagram. Higligh main package and use some config options.

            :param str color_package_self: color to higligh the main package (default '#Yellow').
            :param str package_color: default package color (None).
            :param bool show_main_description: include note inside package with summary and author (default False).
            :return: self
            :rtype: PackageDiagram
        '''
        self._marks.append(module.name)
        # High light main self package
        if module == self._module:
            color = kwargs.get('color_package_self', '#Yellow')
        else:
            color = kwargs.get('package_color', None)

        self.begin_package(
            PackageDiagram.produce_package_name(module, **kwargs),
            stereotype=PackageDiagram.produce_package_stereotype(
                module,
                **kwargs
            ),
            color=color,
            alias=UtilMixin.produce_alias(module.name)
        )
        if kwargs.get('show_main_description', False):
            self.produce_description(module)

        return self.end_package()

    def produce_dependency(self, dependency, **kwargs):
        ''' Strategy to adquire and draw into diagram the package direct dependencies.
            Note: override to change dependency resolution estrategy.

            :param ir.module.module dependency: a module dependency to draw into diagram.
            :return: self
            :rtype: PackageDiagram
        '''
        if dependency.name not in self._marks:
            self.produce_package(dependency, **dict(
                kwargs,
                package_color=PackageDiagram.produce_package_color(
                    dependency, **kwargs
                )
            ))

            for sub in dependency.dependencies_id:
                self.produce_dependency(
                    sub.depend_id, **kwargs
                ).add_dependency(
                    alias1=UtilMixin.produce_alias(dependency.name),
                    alias2=UtilMixin.produce_alias(sub.depend_id.name)
                )
        return self

    def produce_description(self, module):
        ''' Produce floating note with summary and author package.
        '''
        return self.add_floating_note(
            u'<b>Summary</b>: {0}\\n<b>Author</b>: {1}'.format(
                module.summary,
                module.author
            ),
            u'description_{0}'.format(
                UtilMixin.produce_alias(self.module.name)
            )
        )

    def to_puml(self):
        ''' Return a PlantUML Package Diagram as (direct) Dependency Module Diagram.
        '''
        if self._puml is None:
            self._puml = self.begin_uml().produce_dependency(
                self._module, **self._config
            ).end_uml().output()
        return self._puml


class InvPackageDiagram(PackageDiagram):
    ''' Parse module and generate Inverse Module Dependecy Diagram.
    '''
    def __init__(self, module, **kwargs):
        super(InvPackageDiagram, self).__init__(module, **kwargs)

    def produce_dependency(self, dependency, **kwargs):
        ''' Override from :py:class:`odoo_uml.utils.odoo_uml.PackageDiagram` to compute
            inverse dependencies.

            :param ir.module.module dependency: a module dependency to draw into diagram.
            :return: self
            :rtype: InvPackageDiagram
        '''
        env = dependency.env
        if dependency.name not in self._marks:
            self.produce_package(dependency, **dict(
                kwargs,
                package_color=PackageDiagram.produce_package_color(
                    dependency, **kwargs
                )
            ))

            depends_ids = env['ir.module.module'].sudo().search([
                ('dependencies_id.name', '=', dependency.name)
            ])

            for depends in depends_ids:
                self.produce_dependency(
                    depends, **kwargs
                ).add_dependency(
                    alias1=UtilMixin.produce_alias(depends.name),
                    alias2=UtilMixin.produce_alias(dependency.name)
                )

        return self
