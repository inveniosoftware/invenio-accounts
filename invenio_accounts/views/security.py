# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2024 KTH Royal Institute of Technology.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication."""

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_security import current_user
from invenio_db import db
from invenio_i18n import gettext as _

from ..forms import RevokeForm
from ..models import SessionActivity
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
