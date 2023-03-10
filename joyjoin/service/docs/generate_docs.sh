#!/bin/bash

# To jest skrypt generujący dokumentację JoyJoin [WIP]

EXCLUDE_PATTERNS="
../joyjoin/*/admin.py
../joyjoin/*/apps.py
../joyjoin/*/migrations/*
../joyjoin/*/tests.py
../joyjoin/*/urls.py
../joyjoin/joyjoin/*
../joyjoin/manage.py
"

sphinx-apidoc -f -e -o source ../joyjoin/ ../joyjoin/manage.py $EXCLUDE_PATTERNS
make clean
make html
cp -r build/html/* ~/public_html/joyjoin/sphinx/
find /home/hubert/public_html/joyjoin/sphinx/ -type d -exec chmod 755 {} +
find /home/hubert/public_html/joyjoin/sphinx/ -type f -exec chmod 644 {} +
