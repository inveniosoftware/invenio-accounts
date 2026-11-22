# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""ALTCHA proof-of-work captcha support.

ALTCHA (https://altcha.org) is a privacy-friendly, self-hosted captcha: the
browser solves a small proof-of-work challenge issued and signed by this
server, and the server verifies the solution on submission. No third-party
service is contacted.
"""

import hashlib
import hmac
import warnings
from datetime import datetime, timezone

from altcha import Payload, create_challenge, verify_solution
from flask import current_app, jsonify, url_for
from invenio_i18n import gettext as _
from limits import RateLimitItemPerSecond
from markupsafe import Markup
from wtforms import Field
from wtforms.validators import ValidationError
from wtforms.widgets import html_params


def has_legacy_recaptcha_config(app):
    """Return whether the deprecated reCAPTCHA keys are configured."""
    return bool(
        app.config.get("RECAPTCHA_PUBLIC_KEY")
        and app.config.get("RECAPTCHA_PRIVATE_KEY")
    )


def warn_recaptcha_deprecated(app):
    """Warn when the deprecated reCAPTCHA configuration is used."""
    if not has_legacy_recaptcha_config(app):
        return
    message = (
        "reCAPTCHA has been replaced by ALTCHA, a privacy-friendly captcha that "
        "runs entirely on your own server: your users are no longer tracked by "
        "a third party and no cookies are needed. Since RECAPTCHA_PUBLIC_KEY and "
        "RECAPTCHA_PRIVATE_KEY are set, ALTCHA has been enabled automatically "
        "and no action is required for now. To silence this warning, remove "
        "these keys and set ACCOUNTS_ALTCHA_ENABLED = True. Support for the "
        "reCAPTCHA keys will be removed in a future release."
    )
    # Let templates (e.g. to include the widget bundle) see ALTCHA as enabled.
    app.config["ACCOUNTS_ALTCHA_ENABLED"] = True
    warnings.warn(message, DeprecationWarning, stacklevel=3)
    # DeprecationWarnings are hidden by default, so also tell the operators.
    app.logger.warning(message)


def warn_altcha_replay_unprotected(app):
    """Warn when ALTCHA is enabled but replay protection is unavailable.

    Used challenges are recorded in the rate limiter storage of Invenio-App.
    With ``RATELIMIT_ENABLED = False`` there is no such storage, so a solved
    challenge can be reused until it expires.
    """
    if not is_altcha_enabled(app) or app.config.get("RATELIMIT_ENABLED", True):
        return
    app.logger.warning(
        "ALTCHA replay protection is inactive because rate limiting is disabled "
        "(RATELIMIT_ENABLED = False): a solved challenge can be reused until it "
        "expires (ACCOUNTS_ALTCHA_EXPIRES)."
    )


def is_altcha_enabled(app):
    """Return whether ALTCHA is enabled for the given application.

    It protects the registration, forgot-password and resend-confirmation
    forms. The deprecated reCAPTCHA keys also enable it.
    """
    return bool(app.config.get("ACCOUNTS_ALTCHA_ENABLED")) or (
        has_legacy_recaptcha_config(app)
    )


def _hmac_secret():
    """Return the secret used to sign challenges.

    Defaults to a key derived from ``SECRET_KEY`` so that the raw secret key is
    never used directly for a different purpose.
    """
    secret = current_app.config.get("ACCOUNTS_ALTCHA_HMAC_KEY")
    if secret:
        return secret
    return hmac.new(
        current_app.config["SECRET_KEY"].encode("utf-8"),
        b"invenio-accounts-altcha",
        hashlib.sha256,
    ).hexdigest()


def create_altcha_challenge():
    """Create a new signed ALTCHA challenge."""
    expires = current_app.config["ACCOUNTS_ALTCHA_EXPIRES"]
    return create_challenge(
        algorithm=current_app.config["ACCOUNTS_ALTCHA_ALGORITHM"],
        cost=current_app.config["ACCOUNTS_ALTCHA_COST"],
        expires_at=datetime.now(timezone.utc) + expires,
        hmac_secret=_hmac_secret(),
    )


def challenge_view():
    """Return a fresh ALTCHA challenge as JSON."""
    response = jsonify(create_altcha_challenge().to_dict())
    response.headers["Cache-Control"] = "no-store"
    return response


def _mark_used(signature):
    """Record a challenge as used. Return ``False`` if it already was.

    Uses the rate limiter storage from Invenio-App (when available) so that a
    solved challenge cannot be replayed until it expires. With a shared
    storage (e.g. Redis), this protection works across processes.
    """
    app_ext = current_app.extensions.get("invenio-app")
    limiter = getattr(app_ext, "limiter", None)
    if limiter is None or not current_app.config.get("RATELIMIT_ENABLED", True):
        return True
    expires = current_app.config["ACCOUNTS_ALTCHA_EXPIRES"]
    item = RateLimitItemPerSecond(1, max(int(expires.total_seconds()), 1))
    return limiter.limiter.hit(item, "invenio-accounts-altcha", signature)


def verify_altcha_payload(data):
    """Verify a base64-encoded ALTCHA payload submitted by the widget."""
    if not data:
        return False
    try:
        payload = Payload.from_base64(data)
    except (ValueError, KeyError, TypeError, RecursionError):
        return False
    if not verify_solution(payload, _hmac_secret()).verified:
        return False
    # A verified payload always carries a valid challenge signature.
    return _mark_used(payload.challenge.signature)


class AltchaWidget:
    """Render the ``<altcha-widget>`` web component."""

    def __call__(self, field, **kwargs):
        """Render the widget."""
        for name, value in current_app.config.get(
            "ACCOUNTS_ALTCHA_WIDGET_ATTRS", {}
        ).items():
            kwargs.setdefault(name, value)
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("name", field.name)
        kwargs.setdefault("challenge", url_for("invenio_accounts.altcha_challenge"))
        return Markup("<altcha-widget {0}></altcha-widget>").format(
            Markup(html_params(**kwargs))
        )


class AltchaField(Field):
    """Form field validating an ALTCHA proof-of-work solution."""

    widget = AltchaWidget()

    def __init__(self, label="", validators=None, **kwargs):
        """Initialize the field."""
        super().__init__(label, validators, **kwargs)

    def _value(self):
        return ""

    def process_formdata(self, valuelist):
        """Keep the raw base64 payload."""
        self.data = valuelist[0] if valuelist else None

    def pre_validate(self, form):
        """Verify the submitted solution."""
        if not verify_altcha_payload(self.data):
            raise ValidationError(
                _("Please complete the verification that you are not a robot.")
            )
