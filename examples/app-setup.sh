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
npm install -g node-sass@3.8.0 clean-css@3.4.19 requirejs@2.2.0 uglify-js@2.7.3

# Install assets
flask npm
cd static
npm install
cd ..
flask collect
flask assets build

# Create the database
flask db init
flask db create
