# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Forgot-password rate limit helpers."""

from flask import current_app
from limits import parse_many


def _enforce_user_limit(user, limit_key, key_prefix_key, message_key):
    limit_value = current_app.config.get(limit_key)
    if not limit_value:
        return True, None

    limiter_ext = current_app.extensions["invenio-app"].limiter
    key_prefix = current_app.config[key_prefix_key]

    user_id = getattr(user, "id", None)
    if user_id is None:
        return True, None

    key = str(user_id)

    for item in parse_many(limit_value):
        allowed = limiter_ext.limiter.hit(item, key_prefix, key)
        if not allowed:
            return False, current_app.config[message_key]
    return True, None


def enforce_forgot_password_limit(user):
    """Return result for forgot-password per-account rate limit."""
    return _enforce_user_limit(
        user=user,
        limit_key="ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT",
        key_prefix_key="ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT_KEY_PREFIX",
        message_key="ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT_MSG",
    )


def enforce_login_limit(user):
    """Return result for login per-account rate limit."""
    return _enforce_user_limit(
        user=user,
        limit_key="ACCOUNTS_LOGIN_RATELIMIT",
        key_prefix_key="ACCOUNTS_LOGIN_RATELIMIT_KEY_PREFIX",
        message_key="ACCOUNTS_LOGIN_RATELIMIT_MSG",
    )


def enforce_send_confirmation_limit(user):
    """Return result for send-confirmation per-account rate limit."""
    return _enforce_user_limit(
        user=user,
        limit_key="ACCOUNTS_SEND_CONFIRMATION_RATELIMIT",
        key_prefix_key="ACCOUNTS_SEND_CONFIRMATION_RATELIMIT_KEY_PREFIX",
        message_key="ACCOUNTS_SEND_CONFIRMATION_RATELIMIT_MSG",
    )
