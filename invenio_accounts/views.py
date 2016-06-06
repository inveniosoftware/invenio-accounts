# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

from flask import Blueprint, current_app
from flask_babelex import lazy_gettext as _
from flask_menu import current_menu

blueprint = Blueprint(
    'invenio_accounts',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.record_once
def post_ext_init(state):
    """."""
    app = state.app

    app.config.setdefault(
        "ACCOUNTS_SITENAME",
        app.config.get("THEME_SITENAME", "Invenio"))
    app.config.setdefault(
        "ACCOUNTS_BASE_TEMPLATE",
        app.config.get("BASE_TEMPLATE",
                       "invenio_accounts/base.html"))
    app.config.setdefault(
        "ACCOUNTS_COVER_TEMPLATE",
        app.config.get("COVER_TEMPLATE",
                       "invenio_accounts/base_cover.html"))
    app.config.setdefault(
        "ACCOUNTS_SETTINGS_TEMPLATE",
        app.config.get("SETTINGS_TEMPLATE",
                       "invenio_accounts/settings/base.html"))


@blueprint.before_app_first_request
def init_menu():
    """Initialize menu before first request."""
    # Register breadcrumb root
    item = current_menu.submenu('breadcrumbs.settings')
    item.register('', _('Account'))
    item = current_menu.submenu('breadcrumbs.{0}'.format(
        current_app.config['SECURITY_BLUEPRINT_NAME']))

    if current_app.config.get('SECURITY_CHANGEABLE', True):
        item.register('', _('Change password'))

        # Register settings menu
        item = current_menu.submenu('settings.change_password')
        item.register(
            "{0}.change_password".format(
                current_app.config['SECURITY_BLUEPRINT_NAME']),
            # NOTE: Menu item text (icon replaced by a user icon).
            _('%(icon)s Change password',
                icon='<i class="fa fa-key fa-fw"></i>'),
            order=1)

        # Register breadcrumb
        item = current_menu.submenu('breadcrumbs.{0}.change_password'.format(
            current_app.config['SECURITY_BLUEPRINT_NAME']))
        item.register(
            "{0}.change_password".format(
                current_app.config['SECURITY_BLUEPRINT_NAME']),
            _("Change password"),
            order=0,
        )
