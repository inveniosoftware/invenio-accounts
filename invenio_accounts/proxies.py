# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helper proxy to the state object."""

from flask import current_app
from werkzeug.local import LocalProxy

current_accounts = LocalProxy(
    lambda: current_app.extensions['invenio-accounts']
)
"""Proxy to the current Invenio-Accounts extension."""

current_security = LocalProxy(lambda: current_app.extensions['security'])
"""Proxy to the Flask-Security extension."""

current_datastore = LocalProxy(
    lambda: current_app.extensions['security'].datastore)
"""Proxy to the current Flask-Security user datastore."""
