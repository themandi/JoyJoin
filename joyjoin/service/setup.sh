#!/bin/bash

echo To jest skrypt startowy JoyJoin napisany przez HJ \(v1.00\)
echo Ustawi on wirtualne środowisko Pythona i zainstaluje w nim Django
echo Powinien zostać wykonany tylko raz po sklonowaniu repozytorium,
echo *koniecznie* z katalogu w którym znajduje się skrypt
echo

echo $NAME python3 -m venv ./venv
echo
python3 -m venv venv
echo

echo $NAME source ./venv/bin/activate
echo
source venv/bin/activate
echo

echo $NAME pip install --upgrade pip
echo
pip install --upgrade pip
echo

echo $NAME pip install django
echo
pip install django
echo
