# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C)      2021 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-accounts views."""

from flask import abort, current_app, request
from flask_security.views import anonymous_user_required
from flask_security.views import login as base_login

from .settings import blueprint


@anonymous_user_required
@blueprint.route("/login")
def login(*args, **kwargs):
    """Disable login credential submission if local login is disabled."""
    local_login_enabled = current_app.config.get(
        "ACCOUNTS_LOCAL_LOGIN_ENABLED", True
    )

    login_form_submitted = (request.method == "POST")
    if login_form_submitted and not local_login_enabled:
        # only allow GET requests,
        # avoid credential submission/login via POST
        abort(404)

    return base_login(*args, **kwargs)


__all__ = ('blueprint', 'login')
