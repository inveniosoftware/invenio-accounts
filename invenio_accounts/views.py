# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio user management and authentication."""

from __future__ import absolute_import, print_function

from flask import Blueprint

from flask_babelex import gettext as _

from flask_menu import register_menu

blueprint = Blueprint(
    'invenio_accounts',
    __name__,
    template_folder='templates',
    static_folder='static',
)


# Register menus
@register_menu(blueprint, 'settings.account', _('Account'),
               active_when=lambda: False)
def _menu_header():
    pass


@blueprint.route('/change')
@register_menu(blueprint, 'settings.account.change_password',
               _('%(icon)s Change Password',
                 icon='<i class="fa fa-key fa-fw"></i>'))
def change_password():
    """Register menu route."""
    return
