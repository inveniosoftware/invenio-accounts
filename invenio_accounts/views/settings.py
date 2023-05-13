# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication."""

from flask import Blueprint, abort, current_app, request
from flask_security.views import anonymous_user_required
from flask_security.views import login as base_login
from invenio_i18n import lazy_gettext as _
from invenio_theme import menu

from .security import revoke_session, security


@anonymous_user_required
def login(*args, **kwargs):
    """Disable login credential submission if local login is disabled."""
    local_login_enabled = current_app.config.get("ACCOUNTS_LOCAL_LOGIN_ENABLED", True)

    login_form_submitted = request.method == "POST"
    if login_form_submitted and not local_login_enabled:
        # only allow GET requests,
        # avoid credential submission/login via POST
        abort(404)

    return base_login(*args, **kwargs)


def create_settings_blueprint(app):
    """Create settings blueprint."""
    blueprint = Blueprint(
        "invenio_accounts",
        __name__,
        url_prefix="/account/settings",
        template_folder="../templates",
        static_folder="static",
    )

    icons = app.extensions["invenio-theme"].icons

    blueprint.add_url_rule("/login", view_func=login)

    if app.config["ACCOUNTS_SESSION_ACTIVITY_ENABLED"]:
        blueprint.add_url_rule("/security", view_func=security, methods=["GET"])
        blueprint.add_url_rule(
            "/sessions/revoke", view_func=revoke_session, methods=["POST"]
        )

    menu.submenu("settings.security").register(
        endpoint="invenio_accounts.security",
        text=_("%(icon)s Security", icon=f'<i class="{icons.shield}"></i>'),
        order=2,
    )

    # - Register menu
    # - Change password
    if app.config.get("SECURITY_CHANGEABLE", True):
        menu.submenu("settings.change_password").register(
            endpoint=f"{app.config['SECURITY_BLUEPRINT_NAME']}.change_password",
            text=_("%(icon)s Change password", icon=f'<i class="{icons.key}"></i>'),
            order=1,
        )

    return blueprint
