#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Setup app
mkdir $DIR/instance

mkdir static

# Install specific dependencies
pip install -r requirements.txt

flask collect
flask webpack buildall

# Create the database
flask db init
flask db create
