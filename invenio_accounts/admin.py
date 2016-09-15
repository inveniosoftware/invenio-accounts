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

"""Admin views for invenio-accounts."""

from flask import current_app, flash
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.fields import DateTimeField
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy
from wtforms.validators import DataRequired

from .cli import commit
from .models import Role, User

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class UserView(ModelView):
    """Flask-Admin view to manage users."""

    can_view_details = True
    can_delete = False

    list_all = (
        'id', 'email', 'active', 'confirmed_at', 'last_login_at',
        'current_login_at', 'last_login_ip', 'current_login_ip', 'login_count'
    )

    column_list = \
        column_searchable_list = \
        column_sortable_list = \
        column_details_list = \
        list_all

    form_columns = ('email', 'active')

    form_args = dict(
        email=dict(label='Email', validators=[DataRequired()])
    )

    column_filters = ('id', 'email', 'active', 'confirmed_at', 'last_login_at',
                      'current_login_at', 'login_count')

    column_default_sort = ('last_login_at', True)

    form_overrides = {
        'last_login_at': DateTimeField
    }

    column_labels = {
        'current_login_ip': _('Current Login IP'),
        'last_login_ip': _('Last Login IP')
    }

    @action('inactivate', _('Inactivate'),
            _('Are you sure you want to inactivate selected users?'))
    @commit
    def action_inactivate(self, ids):
        """Inactivate users."""
        try:
            count = 0
            for user_id in ids:
                user = _datastore.get_user(user_id)
                if user is None:
                    raise ValueError(_("Cannot find user."))
                if _datastore.deactivate_user(user):
                    count += 1
            if count > 0:
                flash(_('User(s) were successfully inactivated.'), 'success')
        except Exception as exc:
            if not self.handle_view_exception(exc):
                raise

            current_app.logger.exception(str(exc))  # pragma: no cover
            flash(_('Failed to inactivate users.'),
                  'error')  # pragma: no cover

    @action('activate', _('Activate'),
            _('Are you sure you want to activate selected users?'))
    @commit
    def action_activate(self, ids):
        """Inactivate users."""
        try:
            count = 0
            for user_id in ids:
                user = _datastore.get_user(user_id)
                if user is None:
                    raise ValueError(_("Cannot find user."))
                if _datastore.activate_user(user):
                    count += 1
            if count > 0:
                flash(_('User(s) were successfully inactivated.'), 'success')
        except Exception as exc:
            if not self.handle_view_exception(exc):
                raise

            current_app.logger.exception(str(exc))  # pragma: no cover
            flash(_('Failed to activate users.'), 'error')  # pragma: no cover


class RoleView(ModelView):
    """Admin view for roles."""

    can_view_details = True

    list_all = ('id', 'name', 'description')

    column_list = \
        form_columns = \
        column_searchable_list = \
        column_filters = \
        column_details_list = \
        columns_sortable_list = \
        list_all


user_adminview = {
    'model': User,
    'modelview': UserView,
    'category': _('User Management')
}

role_adminview = {
    'model': Role,
    'modelview': RoleView,
    'category': _('User Management')
}

__all__ = ('user_adminview', 'role_adminview')
