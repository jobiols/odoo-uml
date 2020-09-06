#!/bin/sh
# correr localmente todos los tests de la localizacion
# ----------------------------------------------------

# restaurar la base de test vacia
cp /odoo_ar/odoo-11.0/backup_test/default_test.zip /odoo_ar/odoo-11.0/test11/backup_dir/
oe --restore -d tatakua_test -c tatakua -f test11_test.zip

# correr los tests
sudo docker run --rm -it \
    -v /odoo_ar/odoo-11.0/tatakua/config:/opt/odoo/etc/ \
    -v /odoo_ar/odoo-11.0/tatakua/data_dir:/opt/odoo/data \
    -v /odoo_ar/odoo-11.0/tatakua/sources:/opt/odoo/custom-addons \
    --link pg-test11:db \
    jobiols/odoo-ent:11.0 -- \
       -i  odoo_uml \
   --stop-after-init -d tatakua_test --test-enable
