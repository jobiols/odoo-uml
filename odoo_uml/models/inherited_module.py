
# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import logging

from odoo import models, fields, api, _

try:
    from odoo.addons.odoo_uml.utils.plant_uml import PlantUMLClassDiagram, bold, italic
except ImportError:
    from ..utils.plant_uml import PlantUMLClassDiagram, bold, italic

try:
    from odoo.addons.odoo_uml.utils.odoo_uml import PackageDiagram, InvPackageDiagram, ClassDiagram
except ImportError:
    from ..utils.odoo_uml import PackageDiagram, InvPackageDiagram, ClassDiagram

_logger = logging.getLogger(__name__)


class Module(models.Model):
    _inherit = 'ir.module.module'

    # *************************************************************************
    # Dependency Diagrams
    # *************************************************************************

    # Direct Dependency
    puml_dependency_diagram = fields.Text(
        u'Dependency diagram',
        compute='_compute_diagrams'
    )

    puml_dependency_diagram_png = fields.Binary(
        string=u'Dependency Diagram Image',
        help='Dependency diagram as encode base64 PNG image.',
        compute='_compute_diagrams'
    )

    # Inverse Dependency
    puml_inv_dependency_diagram = fields.Text(
        u'Inverse Dependency diagram',
        compute='_compute_diagrams'
    )

    puml_inv_dependency_diagram_png = fields.Binary(
        string=u'Inverse Dependency Diagram Image',
        help='Dependency diagram as encode base64 PNG image.',
        compute='_compute_diagrams'
    )

    # *************************************************************************
    # Class Diagrams
    # *************************************************************************

    # Class Diagram
    puml_class_diagram = fields.Text(
        u'Class diagram',
        compute='_compute_diagrams'
    )

    puml_class_diagram_png = fields.Binary(
        string=u'Class Diagram Image',
        help='Class diagram as encode base64 PNG image.',
        compute='_compute_diagrams'
    )

    puml_diagram_log = fields.Text(
        u'Dependency diagram log',
        compute='_compute_diagrams'
    )

    puml_package_human_name = fields.Boolean(
        string=u'More descriptive name',
        help='Enable show more descriptive name of the module.',
        default=False
    )

    puml_internal_struct = fields.Boolean(
        string=u'Show internal structure',
        help='Enable show internal estructure of the module.',
        default=False
    )

    @api.depends(
        'puml_internal_struct',
        'puml_package_human_name',
        'name',
        'dependencies_id',
        'dependencies_id.depend_id',
        'dependencies_id.depend_id.name'
    )
    def _compute_diagrams(self):
        footer = _(
            '\n\n\n'
            ' \t\t//     Powered by **Odoo UML** with **PlantUML** technology// .'
            ' //Author//: Armando Robert Lobo <mailto:arobertlobo5@gmail.com> '
        )
        for module in self:
            header = _('\n\n| **Module**: | {0} |\n| **Description**: | {1} |\n| **Author**: | {2} |\n').format(
                module.name,
                module.summary,
                module.author
            )
            kwargs = {
                'show_internal': module.puml_internal_struct,
                'show_descriptive_name': module.puml_package_human_name,
                'env': self.env
            }
            diagram = PackageDiagram(
                self,
                title=_('Module Dependency Diagram'),
                header=header,
                footer=footer,
                **kwargs
            )
            module.puml_dependency_diagram_png = diagram.to_png_base64()

            diagram = InvPackageDiagram(
                self,
                title=_('Module Inverse Dependency Diagram'),
                header=header,
                footer=footer,
                **kwargs
            )
            module.puml_inv_dependency_diagram_png = diagram.to_png_base64()

            diagram = ClassDiagram(
                self,
                title=_('Models Class Diagram'),
                header=header,
                footer=footer,
                **kwargs
            )
            module.puml_class_diagram_png = diagram.to_png_base64()
