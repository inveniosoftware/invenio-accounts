#!/bin/sh

DIR=`dirname "$0"`

cd "$DIR"
export FLASK_APP=app.py

# Drop database tables.
flask db drop --yes-i-know

# Clean environment.
[ -d "$DIR/static" ] && rm -Rf "$DIR/static"
[ -d "$DIR/instance" ] && rm -Rf "$DIR/instance"
