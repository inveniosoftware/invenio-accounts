=========================
 Invenio-Accounts v0.2.0
=========================

Invenio-Accounts v0.2.0 was released on October 5, 2015.

About
-----

Invenio module for managing user accounts.

*This is an experimental development preview release.*

Incompatible changes
--------------------

- Removes legacy dashboard under '/youraccount/display' and redirects
  to new settings panel.
- Moves functions from helpers to utils module and deprecates usage of
  helpers module.

Improved features
-----------------

- Removes fixed user id from fixtures as it is automatically generated
  by database engine. (closes inveniosoftware/invenio#3320)

Bug fixes
---------

- Removes dependencies to invenio.utils and replaces them with
  invenio_utils.
- Removes dependencies to invenio.testsuite and replaces them with
  invenio_testing.
- Removes calls to PluginManager consider_setuptools_entrypoints()
  removed in PyTest 2.8.0.
- Removes dependencies to invenio.ext and replaces them with
  invenio_ext.
- Adds missing `invenio_base` dependency.
- Adds return value to `userext` estimate method and fixes the table
  name.
- Nickname check rules uses only the nickname column instead of all of
  them.

Installation
------------

   $ pip install invenio-accounts==0.2.0

Documentation
-------------

   http://invenio-accounts.readthedocs.org/en/v0.2.0

Happy hacking and thanks for flying Invenio-Accounts.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: https://github.com/inveniosoftware/invenio-accounts
|   URL: http://invenio-software.org
