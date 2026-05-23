# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-License-Identifier: MIT

"""Account signals."""

from blinker import Namespace

_signals = Namespace()


datastore_pre_commit = _signals.signal("datastore-pre-commit")
"""Signal sent before the session has been commited.

Parameters:
- ``session`` - a database session

Example receiver:

.. code-block:: python
   def receiver(sender, session):
       # ...

"""


datastore_post_commit = _signals.signal("datastore-post-commit")
"""Signal sent after the session has been commited.

Parameters:
- ``session`` - a database session

Example receiver:

.. code-block:: python
   def receiver(sender, session):
       # ...

"""
