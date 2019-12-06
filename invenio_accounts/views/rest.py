# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API user management and authentication."""

from __future__ import absolute_import, print_function

from flask import Blueprint, after_this_request, current_app, jsonify
from flask.views import MethodView
from flask_login import login_required
from flask_security import current_user
from flask_security.changeable import change_user_password
from flask_security.confirmable import confirm_email_token_status, \
    confirm_user, requires_confirmation
from flask_security.decorators import anonymous_user_required
from flask_security.recoverable import reset_password_token_status, \
    update_password
from flask_security.signals import reset_password_instructions_sent
from flask_security.utils import config_value, get_message, login_user, \
    logout_user, send_mail, verify_and_update_password
from invenio_db import db
from invenio_rest.errors import FieldError, RESTValidationError
from webargs import ValidationError, fields, validate
from webargs.flaskparser import FlaskParser as FlaskParserBase

from invenio_accounts.models import SessionActivity
from invenio_accounts.sessions import delete_session

from ..proxies import current_datastore, current_security
from ..utils import default_confirmation_link_func, \
    default_reset_password_link_func, obj_or_import_string, register_user


def role_to_dict(role):
    """Serialize a new role to dict.

    :param role: a new role to serialize into dict.
    :return: dict from role.
    :rtype: dict.
    """
    return dict(
        id=role.id,
        name=role.name,
        description=role.description,
    )


def create_blueprint(app):
    """Conditionally creates the blueprint."""
    blueprint = Blueprint('invenio_accounts_rest_auth', __name__)

    security_state = app.extensions['security']

    if app.config['ACCOUNTS_REST_AUTH_VIEWS']:
        # Resolve the view classes
        authentication_views = {
            k: obj_or_import_string(v)
            for k, v in app.config.get('ACCOUNTS_REST_AUTH_VIEWS', {}).items()
        }

        blueprint.add_url_rule(
            '/login',
            view_func=authentication_views['login'].as_view('login'))
        blueprint.add_url_rule(
            '/logout',
            view_func=authentication_views['logout'].as_view('logout'))
        blueprint.add_url_rule(
            '/me',
            view_func=authentication_views['user_info'].as_view('user_info'))

        if security_state.registerable:
            blueprint.add_url_rule(
                '/register',
                view_func=authentication_views['register'].as_view('register'))

        if security_state.changeable:
            blueprint.add_url_rule(
                '/change-password',
                view_func=authentication_views['change_password'].as_view(
                    'change_password'))

        if security_state.recoverable:
            blueprint.add_url_rule(
                '/forgot-password',
                view_func=authentication_views['forgot_password'].as_view(
                    'forgot_password'))
            blueprint.add_url_rule(
                '/reset-password',
                view_func=authentication_views['reset_password'].as_view(
                    'reset_password'))

        if security_state.confirmable:
            blueprint.add_url_rule(
                '/send-confirmation-email',
                view_func=authentication_views['send_confirmation'].as_view(
                    'send_confirmation'))

            blueprint.add_url_rule(
                '/confirm-email',
                view_func=authentication_views['confirm_email'].as_view(
                    'confirm_email'))

        # TODO: Check this
        if app.config['ACCOUNTS_SESSION_ACTIVITY_ENABLED']:
            blueprint.add_url_rule(
                '/revoke-session',
                view_func=authentication_views['revoke_session'].as_view(
                    'revoke_session'))
    return blueprint


class FlaskParser(FlaskParserBase):
    """."""

    # TODO: Add error codes to all messages (e.g. 'user-already-exists')
    def handle_error(self, error, *args, **kwargs):
        """."""
        if isinstance(error, ValidationError):
            _errors = []
            for field, messages in error.messages.items():
                _errors.extend([FieldError(field, msg) for msg in messages])
            raise RESTValidationError(errors=_errors)
        super(FlaskParser, self).handle_error(error, *args, **kwargs)


webargs_parser = FlaskParser()
use_args = webargs_parser.use_args
use_kwargs = webargs_parser.use_kwargs


#
# Field validators
#
def user_exists(email):
    """Validate that a user exists."""
    if not current_datastore.get_user(email):
        raise ValidationError(get_message('USER_DOES_NOT_EXIST')[0])


def unique_user_email(email):
    """Validate unique user email."""
    if current_datastore.get_user(email) is not None:
        raise ValidationError(
            get_message('EMAIL_ALREADY_ASSOCIATED', email=email)[0])


def default_user_payload(user):
    """."""
    return {
        'id': user.id,
        'email': user.email,
        'confirmed_at':
            user.confirmed_at.isoformat() if user.confirmed_at else None,
        'last_login_at':
            user.last_login_at.isoformat() if user.last_login_at else None,
        # TODO: Check roles
        'roles': [role_to_dict(role) for role in user.roles],
    }


def _abort(message, field=None, status=None):
    if field:
        raise RESTValidationError([FieldError(field, message)])
    raise RESTValidationError(description=message)


def _commit(response=None):
    current_datastore.commit()
    return response


class LoginView(MethodView):
    """View to login a user."""

    decorators = [anonymous_user_required]

    post_args = {
        'email': fields.Email(required=True, validate=[user_exists]),
        'password': fields.String(
            required=True, validate=[validate.Length(min=6, max=128)])
    }

    def success_response(self, user):
        """Return a successful login response."""
        return jsonify(default_user_payload(user))

    def verify_login(self, user, password=None, **kwargs):
        """Verify the login via password."""
        if not user.password:
            _abort(get_message('PASSWORD_NOT_SET')[0], 'password')
        if not verify_and_update_password(password, user):
            _abort(get_message('INVALID_PASSWORD')[0], 'password')
        if requires_confirmation(user):
            _abort(get_message('CONFIRMATION_REQUIRED')[0])
        if not user.is_active:
            _abort(get_message('DISABLED_ACCOUNT')[0])

    def get_user(self, email=None, **kwargs):
        """Retrieve a user by the provided arguments."""
        return current_datastore.get_user(email)

    def login_user(self, user):
        """Perform any login actions."""
        return login_user(user)

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Verify and login a user."""
        user = self.get_user(**kwargs)
        self.verify_login(user, **kwargs)
        self.login_user(user)
        return self.success_response(user)


class UserInfoView(MethodView):
    """."""

    decorators = [login_required]

    def response(self, user):
        """."""
        return jsonify(default_user_payload(user))

    def get(self):
        """."""
        return self.response(current_user)


class LogoutView(MethodView):
    """."""

    def logout_user(self):
        """."""
        if current_user.is_authenticated:
            logout_user()

    def success_response(self):
        """."""
        return jsonify({'message': 'User logged out.'})

    def post(self):
        """."""
        self.logout_user()
        return self.success_response()


class RegisterView(MethodView):
    """View to register a new user."""

    decorators = [anonymous_user_required]

    post_args = {
        'email': fields.Email(required=True, validate=[unique_user_email]),
        'password': fields.String(
            required=True, validate=[validate.Length(min=6, max=128)])
    }

    def login_user(self, user):
        """."""
        if not current_security.confirmable or \
                current_security.login_without_confirmation:
            after_this_request(_commit)
            login_user(user)

    def success_response(self, user):
        """."""
        return jsonify(default_user_payload(user))

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """."""
        user = register_user(**kwargs)
        self.login_user(user)
        return self.success_response(user)


class ForgotPasswordView(MethodView):
    """."""

    decorators = [anonymous_user_required]

    reset_password_link_func = default_reset_password_link_func

    post_args = {
        'email': fields.Email(required=True, validate=[user_exists]),
    }

    def get_user(self, email=None, **kwargs):
        """Retrieve a user by the provided arguments."""
        return current_datastore.get_user(email)

    def send_reset_password_instructions(self, user):
        """."""
        token, reset_link = self.reset_password_link_func(user)
        if config_value('SEND_PASSWORD_RESET_EMAIL'):
            send_mail(config_value('EMAIL_SUBJECT_PASSWORD_RESET'), user.email,
                      'reset_instructions', user=user, reset_link=reset_link)
            reset_password_instructions_sent.send(
                current_app._get_current_object(), user=user, token=token)

    def success_response(self, user):
        """."""
        return jsonify({'message': get_message(
            'PASSWORD_RESET_REQUEST', email=user.email)[0]})

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """."""
        user = self.get_user(**kwargs)
        self.send_reset_password_instructions(user)
        return self.success_response(user)


class ResetPasswordView(MethodView):
    """."""

    decorators = [anonymous_user_required]

    post_args = {
        'token': fields.String(required=True),
        'password': fields.String(
            required=True, validate=[validate.Length(min=6, max=128)]),
    }

    def get_user(self, token=None, **kwargs):
        """."""
        # Verify the token
        expired, invalid, user = reset_password_token_status(token)
        if invalid:
            _abort(get_message('INVALID_RESET_PASSWORD_TOKEN')[0])
        if expired:
            _abort(get_message(
                'PASSWORD_RESET_EXPIRED',
                email=user.email,
                within=current_security.reset_password_within)[0])
        return user

    def success_response(self, user):
        """."""
        return jsonify({'message': get_message('PASSWORD_RESET')[0]})

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """."""
        user = self.get_user(**kwargs)
        after_this_request(_commit)
        update_password(user, kwargs['password'])
        login_user(user)
        return self.success_response(user)


class ChangePasswordView(MethodView):
    """."""

    decorators = [login_required]

    post_args = {
        'password': fields.String(
            required=True, validate=[validate.Length(min=6, max=128)]),
        'new_password': fields.String(
            required=True, validate=[validate.Length(min=6, max=128)]),
    }

    def verify_password(self, password=None, new_password=None, **kwargs):
        """."""
        if not verify_and_update_password(password, current_user):
            _abort(get_message('INVALID_PASSWORD')[0], 'password')
        if password.data == new_password:
            _abort(get_message('PASSWORD_IS_THE_SAME')[0], 'password')

    def change_password(self, new_password=None, **kwargs):
        """."""
        after_this_request(_commit)
        change_user_password(current_user._get_current_object(), new_password)

    def success_response(self):
        """."""
        return jsonify({'message': get_message('PASSWORD_CHANGE')[0]})

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """."""
        self.verify_password(**kwargs)
        self.change_password(**kwargs)
        return self.success_response()


class SendConfirmationEmailView(MethodView):
    """View function which sends confirmation instructions."""

    decorators = [login_required]

    confirmation_link_func = default_confirmation_link_func

    post_args = {
        'email': fields.Email(required=True, validate=[user_exists]),
    }

    def get_user(self, email=None, **kwargs):
        """Retrieve a user by the provided arguments."""
        return current_datastore.get_user(email)

    def verify(self, user):
        """."""
        if user.confirmed_at is not None:
            _abort(get_message('ALREADY_CONFIRMED')[0])

    def send_confirmation_link(self, user):
        """."""
        send_email_enabled = current_security.confirmable and \
            config_value('SEND_REGISTER_EMAIL')
        if send_email_enabled:
            token, confirmation_link = self.confirmation_link_func(user)
            # TODO: check if there's another template for the confirmation link
            send_mail(
                config_value('EMAIL_SUBJECT_REGISTER'), user.email,
                'welcome', user=user, confirmation_link=confirmation_link)
            return token

    def success_response(self, user):
        """."""
        return jsonify({
            'message': get_message('CONFIRMATION_REQUEST', email=user.email)[0]
        })

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """."""
        user = self.get_user(**kwargs)
        self.verify(user)
        self.send_confirmation_link(user)
        return self.success_response(user)


class ConfirmEmailView(MethodView):
    """."""

    def get_user(self, token=None, **kwargs):
        """."""
        expired, invalid, user = confirm_email_token_status(token)

        if not user or invalid:
            _abort(get_message('INVALID_CONFIRMATION_TOKEN'))

        already_confirmed = user is not None and user.confirmed_at is not None
        if expired and not already_confirmed:
            _abort(get_message(
                'CONFIRMATION_EXPIRED',
                email=user.email,
                within=current_security.confirm_email_within))
        return user

    @use_kwargs({'token': fields.String(required=True)})
    def post(self, **kwargs):
        """View function which handles a email confirmation request."""
        user = self.get_user(**kwargs)

        if user != current_user:
            logout_user()

        if confirm_user(user):
            after_this_request(_commit)
            return jsonify({'message': get_message('EMAIL_CONFIRMED')[0]})
        else:
            return jsonify({'message': get_message('ALREADY_CONFIRMED')[0]})


class RevokeSessionView(MethodView):
    """."""

    decorators = [login_required]

    post_args = {
        'sid_s': fields.String(required=True),
    }

    @use_kwargs(post_args)
    def post(self, sid_s=None, **kwargs):
        """."""
        if SessionActivity.query.filter_by(
                user_id=current_user.get_id(), sid_s=sid_s).count() == 1:
            delete_session(sid_s=sid_s)
            db.session.commit()
            if not SessionActivity.is_current(sid_s=sid_s):
                return jsonify({
                    'message':
                        'Session {0} successfully removed.'.format(sid_s)
                })
        else:
            return jsonify({
                'message': 'Unable to remove session {0}.'.format(sid_s)}), 400
