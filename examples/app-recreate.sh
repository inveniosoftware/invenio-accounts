#!/bin/sh

DIR=`dirname "$0"`

# clean environment
[ -e "$DIR/instance" ] && rm $DIR/instance -Rf
[ -e "$DIR/static" ] && rm $DIR/static -Rf
mkdir $DIR/instance
mkdir $DIR/static

export FLASK_APP=app.py

# Install specific dependencies
pip install -r requirements.txt || exit 1
echo 'Installing npm utilities...'
npm install -g node-sass@3.8.0 clean-css@3.4.19 requirejs@2.2.0 uglify-js@2.7.3 || exit 1

# Install assets
flask npm || exit 1
cd static || exit 1
npm install || exit 1
cd .. || exit 1
flask collect -v || exit 1
flask assets build || exit 1

# Create the database
flask db init || exit 1
flask db create || exit 1

# Create a user
flask users create info@inveniosoftware.org -a --password 123456 || exit 1
flask users activate info@inveniosoftware.org || exit 1

# Run the server
flask run --debugger -h 0.0.0.0 -p 5000
