Changes
=======

Version 1.0.0b12 (released 2017-12-21)
--------------------------------------

- Module rewrite using Flask-Security.

Version 0.2.0 (released 2015-10-05)
-----------------------------------

Incompatible changes
~~~~~~~~~~~~~~~~~~~~

- Removes legacy dashboard under '/youraccount/display' and redirects
  to new settings panel.
- Moves functions from helpers to utils module and deprecates usage of
  helpers module.

Improved features
~~~~~~~~~~~~~~~~~

- Removes fixed user id from fixtures as it is automatically generated
  by database engine. (closes inveniosoftware/invenio#3320)

Bug fixes
~~~~~~~~~

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

Version 0.1.2 (released 2015-09-03)
-----------------------------------

- Changes way how the access tokens are generated from "mailcookie" to
  tokens using "itsdangerous" package.  (#7)
- Removes support for local access configuration and the automatic SSO
  logout url rediction.  (#8)
- Adds module for generating time limited tokens for password
  recovery.  (#7)
- Changes index name definition in `UserEXT` model for `id_user` and
  `method` columns.  (#5)

Version 0.1.1 (released 2015-08-25)
-----------------------------------

- Adds missing `invenio_upgrader` dependency and amends past upgrade
  recipes following its separation into standalone package.

Version 0.1.0 (released 2015-07-31)
-----------------------------------

- Initial public release.
