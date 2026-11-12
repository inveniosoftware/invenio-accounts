# SPDX-FileCopyrightText: 2015-2026 CERN.
# SPDX-FileCopyrightText: 2024 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Invenio user management and authentication."""

from flask import Blueprint, abort, current_app, request
from flask_security.recoverable import send_reset_password_instructions
from flask_security.utils import config_value, do_flash, get_message
from flask_security.views import anonymous_user_required
from flask_security.views import login as base_login

from ..proxies import current_security
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


@anonymous_user_required
def forgot_password():
    """Handle a forgotten password request.

    Unlike Flask-Security's view, this shows the same message whether or not
    an account exists for the submitted email address, so that the form cannot
    be used to find out which addresses are registered. Instructions are only
    sent if the form found an account (see
    :func:`invenio_accounts.forms.forgot_password_form_factory`).
    """
    form = current_security.forgot_password_form()

    if form.validate_on_submit():
        user = getattr(form, "user", None)
        if user is not None:
            send_reset_password_instructions(user)
        do_flash(*get_message("PASSWORD_RESET_REQUEST", email=form.email.data))

    return current_security.render_template(
        config_value("FORGOT_PASSWORD_TEMPLATE"),
        forgot_password_form=form,
        **current_security._run_ctx_processor("forgot_password"),
    )


def create_settings_blueprint(app):
    """Create settings blueprint."""
    blueprint = Blueprint(
        "invenio_accounts",
        __name__,
        url_prefix="/account/settings",
        template_folder="../templates",
        static_folder="static",
    )

    blueprint.add_url_rule("/login", view_func=login)

    if app.config["ACCOUNTS_SESSION_ACTIVITY_ENABLED"]:
        blueprint.add_url_rule("/security", view_func=security, methods=["GET"])
        blueprint.add_url_rule(
            "/sessions/revoke", view_func=revoke_session, methods=["POST"]
        )

    return blueprint
