# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Test example app."""

import os
import signal
import subprocess
import time

from six import b


def setup_module(module):
    """Set up before all tests."""
    # switch to examples/app.py
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exampleappdir = os.path.join(project_dir, 'examples')
    os.chdir(exampleappdir)


def teardown_module(module):
    """Tear down after all tests."""
    cmd = 'FLASK_APP=app.py flask db drop --yes-i-know'
    subprocess.call(cmd, shell=True)


def test_example_app():
    """Test example app."""
    # Starting example web app
    cmd = './app-recreate.sh'
    webapp = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              preexec_fn=os.setsid, shell=True)

    # wait until npm is finished installing modules
    for out in webapp.stdout:
        if b('Installing npm utilities') in out:
            break
    # and start the timeout to run tests
    time.sleep(120)

    # Testing open index page
    cmd = 'curl -v http://127.0.0.1:5000/'
    output = subprocess.check_output(cmd, shell=True)
    assert b'You are not logged in' in output

    # Stopping example web app
    os.killpg(webapp.pid, signal.SIGTERM)
