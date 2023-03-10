#!/bin/bash

URLS="
    /all/
    /create/
    /login/
    /post/1/
    /register/
    /report/
    /sec/programming/
    /sec/programming/tags/
    /settings/
    /user/monika/
"

SERVER_URL=localhost:8000

for URL in $URLS ; do
    echo "Sprawdzanie URL: " $URL
    wget --quiet --output-document tmpfile.html $SERVER_URL$URL
    html5check.py tmpfile.html
    rm tmpfile.html
    echo
done
