# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Per-account rate limit helpers for authentication views."""

from flask import current_app
from limits import parse_many


def _enforce_limit(key, limit_key, key_prefix_key, message_key):
    limit_value = current_app.config.get(limit_key)
    if not limit_value or not key:
        return True, None

    limiter_ext = current_app.extensions["invenio-app"].limiter
    key_prefix = current_app.config[key_prefix_key]

    for item in parse_many(limit_value):
        allowed = limiter_ext.limiter.hit(item, key_prefix, key)
        if not allowed:
            return False, current_app.config[message_key]
    return True, None


def _email_key(email):
    """Return the rate limit key for a submitted email address.

    Login and forgot-password limits are keyed on the submitted address rather
    than on the user ID, so that they apply in the same way whether or not an
    account exists. Otherwise, hitting the limit would reveal that the address
    is registered.
    """
    if not email:
        return None
    return str(email).strip().lower()


def enforce_forgot_password_limit(email):
    """Return result for forgot-password per-account rate limit."""
    return _enforce_limit(
        key=_email_key(email),
        limit_key="ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT",
        key_prefix_key="ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT_KEY_PREFIX",
        message_key="ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT_MSG",
    )


def enforce_login_limit(email):
    """Return result for login per-account rate limit."""
    return _enforce_limit(
        key=_email_key(email),
        limit_key="ACCOUNTS_LOGIN_RATELIMIT",
        key_prefix_key="ACCOUNTS_LOGIN_RATELIMIT_KEY_PREFIX",
        message_key="ACCOUNTS_LOGIN_RATELIMIT_MSG",
    )


def enforce_send_confirmation_limit(user):
    """Return result for send-confirmation per-account rate limit."""
    user_id = getattr(user, "id", None)
    return _enforce_limit(
        key=str(user_id) if user_id is not None else None,
        limit_key="ACCOUNTS_SEND_CONFIRMATION_RATELIMIT",
        key_prefix_key="ACCOUNTS_SEND_CONFIRMATION_RATELIMIT_KEY_PREFIX",
        message_key="ACCOUNTS_SEND_CONFIRMATION_RATELIMIT_MSG",
    )
