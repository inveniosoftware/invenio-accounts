# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Re-authentication of logged-in users before sensitive actions.

The user confirms a one-time code sent to their current email address. This
works the same regardless of how the user logged in (local account or any
external identity provider), and cannot be completed by a script running in
the user's browser since it needs access to the user's mailbox.

A successful re-authentication is valid for
:data:`~invenio_accounts.config.ACCOUNTS_REAUTH_WINDOW`, is bound to the user
and is cleared on login and logout. When
:data:`~invenio_accounts.config.ACCOUNTS_REAUTH_ENABLED` is ``False`` (the
default) every check passes, so modules can protect their views
unconditionally and let the instance decide.

Protect a whole view (all methods, or only some of them):

.. code-block:: python

    from flask_login import login_required
    from invenio_accounts.reauth import reauth_required

    @blueprint.route("/tokens/new/", methods=["GET", "POST"])
    @login_required
    @reauth_required()
    def token_new():
        ...

    @blueprint.route("/settings/", methods=["GET", "POST"])
    @login_required
    @reauth_required(methods=["POST"])
    def settings():
        ...

Or check only in some cases, e.g. when a specific field changes:

.. code-block:: python

    from invenio_accounts.reauth import is_reauth_fresh, reauth_redirect

    if email_changed and not is_reauth_fresh():
        return reauth_redirect(url_for(".profile"))

After re-authenticating, the user is sent back to the ``next`` URL. For
``POST`` requests the original submission is not replayed: pass a ``next_url``
pointing to the page with the form so the user can submit it again.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import urlsplit

from flask import current_app, flash, redirect, request, session, url_for
from flask_security import current_user
from flask_security.utils import send_mail, validate_redirect_url
from invenio_i18n import gettext as _

from .limiter import enforce_reauth_send_limit

SESSION_REAUTH_AT_KEY = "_accounts_reauth_at"
"""Session key storing when the user last re-authenticated."""

SESSION_REAUTH_CODE_KEY = "_accounts_reauth_code"
"""Session key storing the pending re-authentication code."""


class ReauthError(Exception):
    """Error raised when a re-authentication code cannot be sent."""


def _now():
    return datetime.now(timezone.utc).timestamp()


def _user_id():
    return str(current_user.get_id())


def _hash_code(code):
    key = current_app.config["SECRET_KEY"].encode()
    msg = f"{_user_id()}:{code}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def is_reauth_enabled():
    """Return whether re-authentication is enabled."""
    return current_app.config.get("ACCOUNTS_REAUTH_ENABLED", False)


def is_safe_next_url(url):
    """Return whether ``url`` is a safe local URL to redirect to."""
    if not url or "\\" in url or not url.startswith("/") or url.startswith("//"):
        return False
    parts = urlsplit(url)
    return not parts.scheme and not parts.netloc and validate_redirect_url(url)


def is_reauth_fresh():
    """Return whether the current user has recently re-authenticated."""
    if not is_reauth_enabled():
        return True
    if not current_user.is_authenticated:
        return False
    data = session.get(SESSION_REAUTH_AT_KEY)
    if not data or data.get("user_id") != _user_id():
        return False
    window = current_app.config["ACCOUNTS_REAUTH_WINDOW"].total_seconds()
    return _now() - data["at"] <= window


def clear_reauth(*args, **kwargs):
    """Forget any re-authentication state (signal receiver friendly)."""
    session.pop(SESSION_REAUTH_AT_KEY, None)
    session.pop(SESSION_REAUTH_CODE_KEY, None)


def _default_next_url():
    """Return the current page for ``GET``, else the (local) referring page."""
    if request.method == "GET":
        return request.full_path.rstrip("?")
    parts = urlsplit(request.referrer or "")
    if parts.netloc != urlsplit(request.host_url).netloc:
        return "/"
    referrer = parts.path + (f"?{parts.query}" if parts.query else "")
    return referrer if is_safe_next_url(referrer) else "/"


def reauth_redirect(next_url=None):
    """Redirect to the re-authentication page, coming back to ``next_url``.

    :param next_url: Local URL to come back to. Defaults to the current URL for
        ``GET`` requests and to the referring page otherwise. Unsafe URLs are
        ignored.
    """
    if not is_safe_next_url(next_url):
        next_url = _default_next_url()
    flash(_("For your security, please confirm it's you to continue."), "info")
    return redirect(url_for("invenio_accounts.reauth", next=next_url))


def reauth_required(methods=None, next_url=None):
    """Require a recent re-authentication to access a view.

    :param methods: HTTP methods to protect. Defaults to all methods.
    :param next_url: URL to come back to after re-authenticating. Defaults to
        the current URL for ``GET`` requests and to the referrer otherwise.
    """
    methods = {m.upper() for m in methods} if methods else None

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            protected = methods is None or request.method in methods
            if protected and not is_reauth_fresh():
                return reauth_redirect(next_url)
            return f(*args, **kwargs)

        return decorated

    return decorator


def has_pending_code():
    """Return whether a valid code was sent to the current user."""
    data = session.get(SESSION_REAUTH_CODE_KEY)
    return bool(data and data["user_id"] == _user_id() and data["expires"] > _now())


def send_reauth_code():
    """Generate a one-time code and email it to the current user.

    :raises ReauthError: If the user has no email or the rate limit is hit.
    """
    email = current_user.email
    if not email:
        raise ReauthError(
            _(
                "Your account has no email address. Please add one or contact "
                "support to continue."
            )
        )

    allowed, message = enforce_reauth_send_limit(current_user)
    if not allowed:
        raise ReauthError(message)

    code = f"{secrets.randbelow(10**6):06d}"
    ttl = current_app.config["ACCOUNTS_REAUTH_CODE_TTL"]
    session[SESSION_REAUTH_CODE_KEY] = {
        "user_id": _user_id(),
        "hash": _hash_code(code),
        "expires": _now() + ttl.total_seconds(),
        "attempts": 0,
    }
    send_mail(
        str(current_app.config["ACCOUNTS_REAUTH_EMAIL_SUBJECT"]),
        email,
        "reauth_code",
        user=current_user,
        code=code,
        ttl_minutes=int(ttl.total_seconds() // 60),
    )


def verify_reauth_code(code):
    """Check a code entered by the current user.

    On success the user is marked as freshly re-authenticated. A code is
    invalidated once used, expired or after too many wrong attempts.

    :returns: ``True`` if the code is valid.
    """
    data = session.get(SESSION_REAUTH_CODE_KEY)
    if not data or data["user_id"] != _user_id() or data["expires"] <= _now():
        session.pop(SESSION_REAUTH_CODE_KEY, None)
        return False

    data["attempts"] += 1
    valid = hmac.compare_digest(data["hash"], _hash_code((code or "").strip()))
    max_attempts = current_app.config["ACCOUNTS_REAUTH_MAX_ATTEMPTS"]

    if valid or data["attempts"] >= max_attempts:
        session.pop(SESSION_REAUTH_CODE_KEY, None)
    else:
        session[SESSION_REAUTH_CODE_KEY] = data

    if valid:
        session[SESSION_REAUTH_AT_KEY] = {"user_id": _user_id(), "at": _now()}
    return valid
