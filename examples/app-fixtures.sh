#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Setup fixtures

# Create a user
flask users create info@inveniosoftware.org --password 123456
flask users activate info@inveniosoftware.org
