#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Teardown app

# Drop database tables.
flask db drop --yes-i-know

# Clean environment.
[ -d "$DIR/static" ] && rm -Rf "$DIR/static"
[ -d "$DIR/instance" ] && rm -Rf "$DIR/instance"
