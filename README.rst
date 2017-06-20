..
    This file is part of Invenio.
    Copyright (C) 2015, 2016 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.

==================
 Invenio-Accounts
==================

.. image:: https://img.shields.io/travis/inveniosoftware/invenio-accounts.svg
        :target: https://travis-ci.org/inveniosoftware/invenio-accounts

.. image:: https://img.shields.io/coveralls/inveniosoftware/invenio-accounts.svg
        :target: https://coveralls.io/r/inveniosoftware/invenio-accounts

.. image:: https://img.shields.io/github/tag/inveniosoftware/invenio-accounts.svg
        :target: https://github.com/inveniosoftware/invenio-accounts/releases

.. image:: https://img.shields.io/pypi/dm/invenio-accounts.svg
        :target: https://pypi.python.org/pypi/invenio-accounts

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio-accounts.svg
        :target: https://github.com/inveniosoftware/invenio-accounts/blob/master/LICENSE

Invenio user management and authentication.

Features:

- User and role management.
- User registration, password reset/recovery and email verification.
- Administration interface and CLI for managing users.
- Session based authentication with session theft protection as well as
  "remember me" support.
- Strong cryptographic password hashing with support for migrating password
  hashes (including Invenio v1.x) to new stronger algorithms.
- Session activity tracking allowing users to e.g. logout of all devices.
- Server-side session management.
- JSON Web Token encoding and decoding support useful for e.g. CSRF-protection
  in REST APIs.

Invenio-Accounts relies on the following community packages to do all the
heavy-lifting:

- `Flask-Security <https://flask-security.readthedocs.io>`_
- `Flask-Login <https://flask-login.readthedocs.io/>`_
- `Flask-Principal <https://pythonhosted.org/Flask-Principal/>`_
- `Flask-KVSession <http://pythonhosted.org/Flask-KVSession/>`_
- `Passlib <https://passlib.readthedocs.io/>`_

Further documentation is available on
https://invenio-accounts.readthedocs.io/
