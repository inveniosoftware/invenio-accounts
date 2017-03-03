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

from flask import Blueprint, current_app, flash, redirect, render_template, \
    request, url_for
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import login_required
from flask_menu import current_menu, register_menu
from flask_security import current_user
from invenio_db import db

from .forms import RevokeForm
from .models import SessionActivity
from .sessions import delete_session

blueprint = Blueprint(
    'invenio_accounts',
    __name__,
    url_prefix='/account/settings',
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


@blueprint.before_app_first_request
def check_security_settings():
    """Warn if session cookie is not secure in production."""
    in_production = not (current_app.debug or current_app.testing)
    secure = current_app.config.get('SESSION_COOKIE_SECURE')
    if in_production and not secure:
        current_app.logger.warning(
            "SESSION_COOKIE_SECURE setting must be set to True to prevent the "
            "session cookie from being leaked over an insecure channel."
        )


@blueprint.route('/security/', methods=['GET'])
@login_required
@register_menu(
    blueprint, 'settings.security',
    # NOTE: Menu item text (icon replaced by a user icon).
    _('%(icon)s Security', icon='<i class="fa fa-shield fa-fw"></i>'),
    order=2)
@register_breadcrumb(blueprint, 'breadcrumbs.settings.security', _('Security'))
def security():
    """View for security page."""
    sessions = SessionActivity.query_by_user(
        user_id=current_user.get_id()
    ).all()
    master_session = None
    for index, session in enumerate(sessions):
        if SessionActivity.is_current(session.sid_s):
            master_session = session
            del sessions[index]
    return render_template(
        current_app.config['ACCOUNTS_SETTINGS_SECURITY_TEMPLATE'],
        formclass=RevokeForm,
        sessions=[master_session] + sessions,
        is_current=SessionActivity.is_current
    )


@blueprint.route('/sessions/revoke/', methods=['POST'])
@login_required
def revoke_session():
    """Revoke a session."""
    form = RevokeForm(request.form)
    if not form.validate_on_submit():
        abort(403)

    sid_s = form.data['sid_s']
    if SessionActivity.query.filter_by(
            user_id=current_user.get_id(), sid_s=sid_s).count() == 1:
        delete_session(sid_s=sid_s)
        db.session.commit()
        if not SessionActivity.is_current(sid_s=sid_s):
            # if it's the same session doesn't show the message, otherwise
            # the session will be still open without the database record
            flash('Session {0} successfully removed.'.format(sid_s), 'success')
    else:
        flash('Unable to remove the session {0}.'.format(sid_s), 'error')
    return redirect(url_for('invenio_accounts.security'))
