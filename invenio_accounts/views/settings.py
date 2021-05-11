# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication."""

from __future__ import absolute_import, print_function

from flask import Blueprint, current_app
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_menu import current_menu
from invenio_theme.proxies import current_theme_icons

blueprint = Blueprint(
    'invenio_accounts',
    __name__,
    url_prefix='/account/settings',
    template_folder='../templates',
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
    # Register root breadcrumbs
    item = current_menu.submenu('breadcrumbs.settings')
    item.register('invenio_userprofiles.profile', _('Account'))

    # - Register menu
    # - Change password
    if current_app.config.get('SECURITY_CHANGEABLE', True):
        view_name = '{}.change_password'.format(
            current_app.config['SECURITY_BLUEPRINT_NAME'])

        item = current_menu.submenu('settings.change_password')
        item.register(
            view_name,
            # NOTE: Menu item text (icon replaced by a key icon).
            _('%(icon)s Change password',
                icon=f'<i class="{current_theme_icons.key}"></i>'),
            order=1)

        # Breadcrumb for change password
        #
        # The breadcrumbs works by decorating the view functions with a
        # __breadcrumb__ field. Since the change password view is defined in
        # Flask-Security, we need to this hack to in order to decorate the view
        # function with the __breadcrumb__ field.
        decorator = register_breadcrumb(
            current_app,
            'breadcrumbs.settings.change_password',
            _('Change password')
        )
        current_app.view_functions[view_name] = decorator(
            current_app.view_functions[view_name])


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
