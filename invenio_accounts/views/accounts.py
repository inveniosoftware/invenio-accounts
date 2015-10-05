# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""WebAccount Flask Blueprint."""

from __future__ import absolute_import

import warnings

from flask import Blueprint, abort, current_app, flash, g, redirect, \
    render_template, request, url_for
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from itsdangerous import BadData, SignatureExpired
from six import text_type
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import CombinedMultiDict, ImmutableMultiDict

from invenio_base.decorators import wash_arguments
from invenio_base.globals import cfg
from invenio_base.i18n import _
from invenio_ext.login import UserInfo, authenticate, login_redirect, \
    login_user, logout_user
from invenio_ext.sqlalchemy import db
from invenio_ext.sslify import ssl_required
from invenio_utils.datastructures import LazyDict, flatten_multidict

from ..errors import AccountSecurityError
from ..forms import LoginForm, LostPasswordForm, RegisterForm, \
    ResetPasswordForm
from ..models import User
from ..tokens import EmailConfirmationSerializer
from ..utils import send_reset_password_email
from ..validators import wash_login_method

blueprint = Blueprint('webaccount', __name__, url_prefix="/youraccount",
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/login', methods=['GET', 'POST'])
@wash_arguments({'nickname': (unicode, None),
                 'password': (unicode, None),
                 'login_method': (wash_login_method, 'Local'),
                 'remember': (bool, False),
                 'referer': (unicode, None)})
@register_breadcrumb(blueprint, '.login', _('Login'))
@ssl_required
def login(nickname=None, password=None, login_method=None,
          remember=False, referer=None):
    """Login."""
    if cfg.get('CFG_ACCESS_CONTROL_LEVEL_SITE') > 0:
        return abort(401)  # page is not authorized

    if 'action' in request.values:
        warnings.warn('Action argument "{}" is not used anymore.'.format(
            request.values['action']), DeprecationWarning)
    form = LoginForm(CombinedMultiDict(
        [ImmutableMultiDict({'referer': referer, 'login_method': 'Local'}
                            if referer else {'login_method': 'Local'}),
         request.values]), csrf_enabled=False)

    if request.method == "POST":
        try:
            if login_method == 'Local' and form.validate_on_submit() and \
               authenticate(nickname, password, login_method=login_method,
                            remember=remember):
                flash(
                    _("You are logged in as %(nick)s.", nick=nickname),
                    "success"
                )
                return login_redirect(referer)

            else:
                flash(_("Invalid credentials."), "error")
        except Exception as e:
            current_app.logger.error(
                'Exception during login process: %s', str(e)
            )
            flash(_("Problem with login."), "error")

    return render_template('accounts/login.html', form=form), 401


@blueprint.route('/register', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.register', _('Register'))
@ssl_required
def register():
    """Register."""
    req = request.get_legacy_request()

    # FIXME
    if cfg.get('CFG_ACCESS_CONTROL_LEVEL_SITE') > 0:
        from invenio.legacy import webuser
        return webuser.page_not_authorized(
            req, "../youraccount/register?ln=%s" % g.ln,
            navmenuid='youraccount')

    form = RegisterForm(request.values, csrf_enabled=False)

    title = _("Register")
    messages = []
    state = ""

    if form.validate_on_submit():
        from invenio.legacy import webuser
        ruid = webuser.registerUser(req, form.email.data.encode('utf8'),
                                    form.password.data.encode('utf8'),
                                    form.nickname.data.encode('utf8'),
                                    ln=g.ln)
        if ruid == 0:
            title = _("Account created")
            messages.append(_("Your account has been successfully created."))
            state = "success"
            if cfg.get('CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT') \
                    == 1:
                messages.append(_("In order to confirm its validity, "
                                  "an email message containing an account "
                                  "activation key has been sent to the given "
                                  "email address."))
                messages.append(_("Please follow instructions presented "
                                  "there in order to complete the account "
                                  "registration process."))
            if cfg.get('CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS') >= 1:
                messages.append(_("A second email will be sent when the "
                                  "account has been activated and can be "
                                  "used."))
            elif cfg['CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT'] != 1:
                user = User.query.filter(
                    User.email == form.email.data.lower()).one()
                login_user(user.get_id())
                messages.append(_("You can now access your account."))
        else:
            title = _("Registration failure")
            state = "danger"
            if ruid == 5:
                messages.append(_("Users cannot register themselves, only "
                                  "admin can register them."))
            elif ruid == 6 or ruid == 1:
                # Note, code 1 is used both for invalid email, and email
                # sending
                # problems, however the email address is validated by the form,
                # so we only have to report a problem sending the email here
                messages.append(_("The site is having troubles in sending "
                                  "you an email for confirming your email "
                                  "address."))
                messages.append(
                    _("The error has been logged and will be "
                      "taken in consideration as soon as possible."))
            else:
                # Errors [-2, (1), 2, 3, 4] taken care of by form validation
                messages.append(_("Internal error %(ruid)s", ruid=ruid))
    elif request.method == 'POST':
        title = _("Registration failure")
        state = "warning"

    return render_template('accounts/register.html', form=form, title=title,
                           messages=messages, state=state)


@blueprint.route('/logout', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.logout', _('Logout'))
@login_required
def logout():
    """Logout."""
    logout_user()
    return render_template('accounts/logout.html',
                           using_sso=False,  # FIXME SSO should use signals
                           logout_sso=None)  # FIXME not needed then


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/display', methods=['GET', 'POST'])
@login_required
@register_menu(blueprint, 'personalize', _('Personalize'))
@register_breadcrumb(blueprint, '.', _('Your account'))
def index():
    """Index."""
    redirect(url_for('accounts_settings.index'))


@blueprint.route('/lost', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.edit', _('Edit'))
@ssl_required
def lost():
    """Lost."""
    form = LostPasswordForm(request.values)

    if form.validate_on_submit():
        email = request.values['email']
        try:
            if send_reset_password_email(email=email):
                flash(_('A password reset link has been sent to %(whom)s',
                        whom=email), 'success')
            else:
                flash(_('Error happen when the email was send. '
                        'Please contact the administrator.'), 'error')
        except AccountSecurityError as e:
            flash(e, 'error')

    return render_template('accounts/lost.html', form=form)


@blueprint.route('/resetpassword', methods=['GET', 'POST'])
@wash_arguments({"reset_key": (text_type, None)})
@ssl_required
def resetpassword(reset_key):
    """Reset password form (loaded after asked new password)."""
    email = None
    try:
        email = EmailConfirmationSerializer().load_token(
            reset_key
        )['data']['email']
    except KeyError:
        flash(
            _('This request for resetting a password has already been used.'),
            'error'
        )
    except (BadData, SignatureExpired):
        flash(_('This request for resetting a password is not valid or is '
                'expired.'), 'error')

    if email is None or cfg['CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS'] >= 3:
        return redirect(url_for('webaccount.index'))

    form = ResetPasswordForm(request.values)

    if form.validate_on_submit():
        password = request.values['password']

        # change password
        user = User.query.filter_by(email=email).one()
        user.password = password
        db.session.merge(user)
        db.session.commit()

        flash(_("The password was correctly reset."), 'success')
        return redirect(url_for('webaccount.index'))

    return render_template('accounts/resetpassword.html', form=form)


@blueprint.route('/access', methods=['GET', 'POST'])
@ssl_required
def access():
    """Access."""
    try:
        email = EmailConfirmationSerializer().load_token(
            request.values['mailcookie']
        )['data']['email']

        u = User.query.filter(User.email == email).one()
        u.note = 1
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(_('Authorization failled.'), 'error')
            redirect('/')

        if current_user.is_authenticated():
            current_user.reload()
            flash(_('Your email address has been validated'), 'success')
        else:
            UserInfo(u.id).reload()
            flash(
                _('Your email address has been validated, and you can '
                  'now proceed to sign-in.'),
                'success'
            )
    except Exception:
        current_app.logger.exception("Authorization failed.")
        flash(_('The authorization token is invalid.'), 'error')
    return redirect('/')
