#!/usr/bin/env bash
#!/usr/bin/env bash
##############################################################################
# Genera la documentacion de los modulos, requiere la instalacion de oca
# maintainers tools en tu maquina.
# bajalo de aca --> https://github.com/OCA/maintainer-tools y lo instalas asi:
#
# $ git clone git@github.com:OCA/maintainer-tools.git
# $ cd maintainer-tools
# $ virtualenv env
# $ . env/bin/activate
# $ python setup.py install
#
source /opt/maintainer-tools/env/bin/activate
oca-gen-addon-readme \
	--org-name "jeo Software" \
	--repo-name odoo-uml \
	--branch 11.0 \
	--addons-dir "$PWD" \
	--gen-html
