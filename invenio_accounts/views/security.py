# SPDX-FileCopyrightText: 2017-2026 CERN.
# SPDX-FileCopyrightText: 2024 KTH Royal Institute of Technology.
# SPDX-FileCopyrightText: 2024 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Invenio user management and authentication."""

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_security import current_user
from invenio_db import db
from invenio_i18n import gettext as _

from ..forms import ReauthSendCodeForm, ReauthVerifyCodeForm, RevokeForm
from ..models import SessionActivity
from ..reauth import (
    ReauthError,
    has_pending_code,
    is_reauth_fresh,
    is_safe_next_url,
    send_reauth_code,
    verify_reauth_code,
)
from ..sessions import delete_session


@login_required
def security():
    """View for security page."""
    sessions = SessionActivity.query_by_user(user_id=current_user.get_id()).all()
    current_session = None
    for index, session in enumerate(sessions):
        if SessionActivity.is_current(session.sid_s):
            current_session = session
            del sessions[index]

    # If the current session is still `None`, filter it out
    sessions = [current_session] + sessions if current_session is not None else sessions

    return render_template(
        current_app.config["ACCOUNTS_SETTINGS_SECURITY_TEMPLATE"],
        formclass=RevokeForm,
        sessions=sessions,
        is_current=SessionActivity.is_current,
    )


@login_required
def revoke_session():
    """Revoke a session."""
    form = RevokeForm(request.form)
    if not form.validate_on_submit():
        abort(403)

    sid_s = form.data["sid_s"]
    if (
        db.session.query(SessionActivity)
        .filter_by(user_id=current_user.get_id(), sid_s=sid_s)
        .count()
        == 1
    ):
        delete_session(sid_s=sid_s)
        db.session.commit()
        if not SessionActivity.is_current(sid_s=sid_s):
            # if it's the same session doesn't show the message, otherwise
            # the session will be still open without the database record
            flash(
                _("Session %(sid_s)s successfully removed.") % {"sid_s": sid_s},
                "success",
            )
    else:
        flash(_("Unable to remove the session %(sid_s)s.") % {"sid_s": sid_s}, "error")
    return redirect(url_for("invenio_accounts.security"))


@login_required
def reauth():
    """View for re-authenticating with a code sent by email."""
    next_url = request.args.get("next")
    if not is_safe_next_url(next_url):
        next_url = "/"

    if request.method == "GET" and is_reauth_fresh():
        return redirect(next_url)

    send_form = ReauthSendCodeForm(prefix="send")
    verify_form = ReauthVerifyCodeForm(prefix="verify")
    action = request.form.get("action")

    if action == "send" and send_form.validate_on_submit():
        try:
            send_reauth_code()
            flash(
                _("A verification code has been sent to %(email)s.")
                % {"email": current_user.email},
                category="success",
            )
        except ReauthError as e:
            flash(str(e), category="error")
        return redirect(url_for(".reauth", next=next_url))

    if action == "verify" and verify_form.validate_on_submit():
        if verify_reauth_code(verify_form.code.data):
            return redirect(next_url)
        verify_form.code.errors.append(
            _("The code is invalid or has expired. Please try again.")
        )

    return render_template(
        current_app.config["ACCOUNTS_REAUTH_TEMPLATE"],
        send_form=send_form,
        verify_form=verify_form,
        code_sent=has_pending_code(),
        next_url=next_url,
    )
