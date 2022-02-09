# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C)      2021 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    "pytest-invenio>=1.4.2"
]

extras_require = {
    'admin': [
        'invenio-admin>=1.2.1',
    ],
    'docs': [
        'Sphinx==4.2.0',
    ],
    'mysql': [
        'invenio-db[versioning,mysql]>=1.0.11',
    ],
    'postgresql': [
        'invenio-db[versioning,postgresql]>=1.0.11',
    ],
    'sqlite': [
        'invenio-db[versioning]>=1.0.11',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name[0] == ':':
        continue
    if name in ('mysql', 'postgresql', 'sqlite'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=2.8',
]

install_requires = [
    'cryptography>=3.0.0',
    'Flask-Breadcrumbs>=0.4.0',
    'Flask-KVSession-Invenio>=0.6.3',
    'Flask-Mail>=0.9.1',
    'Flask-Menu>=0.5.0',
    'Flask-Security-Invenio>=3.1.1',
    'invenio-base>=1.2.5',
    'invenio-celery>=1.2.3',
    'invenio-i18n>=1.3.1',
    'invenio-rest>=1.2.4',
    'invenio-theme>=1.3.4',
    'maxminddb-geolite2>=2017.404',
    'passlib>=1.7.1',
    'pyjwt>=1.5.0',
    'redis>=2.10.5',
    'simplekv>=0.11.2',
    'ua-parser>=0.7.3',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_accounts', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-accounts',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio accounts user role login',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-accounts',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'roles = invenio_accounts.cli:roles',
            'users = invenio_accounts.cli:users',
        ],
        'invenio_admin.views': [
            'invenio_accounts_user = invenio_accounts.admin:user_adminview',
            'invenio_accounts_role = invenio_accounts.admin:role_adminview',
            'invenio_accounts_session = '
            'invenio_accounts.admin:session_adminview',
            'invenio_accounts_user_identity = '
            'invenio_accounts.admin:user_identity_adminview',
        ],
        'invenio_base.api_apps': [
            'invenio_accounts_rest = invenio_accounts:InvenioAccountsREST',
        ],
        'invenio_base.apps': [
            'invenio_accounts_ui = invenio_accounts:InvenioAccountsUI',
        ],
        'invenio_base.blueprints': [
            'invenio_accounts = invenio_accounts.views.settings:blueprint',
        ],
        'invenio_base.api_blueprints': [
            'invenio_accounts_rest_auth = '
            'invenio_accounts.views.rest:create_blueprint',
        ],
        'invenio_celery.tasks': [
            'invenio_accounts = invenio_accounts.tasks',
        ],
        'invenio_db.alembic': [
            'invenio_accounts = invenio_accounts:alembic',
        ],
        'invenio_db.models': [
            'invenio_accounts = invenio_accounts.models',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_accounts',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 5 - Production/Stable',
    ],
)
