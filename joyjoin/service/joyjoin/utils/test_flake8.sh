#!/bin/bash

if command -v flake8; then
	flake8 --extend-ignore=E261,E501 --exclude=utils/html5check.py
else
	echo "Nie masz zainstalowanego flake8"
	echo "Aby zainstalować użyj"
	echo -e "\tpip install --upgrade flake8"
fi
