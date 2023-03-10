#!/bin/bash

source utils/common.sh

if [[ -f db.sqlite3 ]]; then
	progress "Usuwanie bazy danych"
	rm db.sqlite3
	pdone
fi

progress "Aplikowanie migracji"
python manage.py migrate > /dev/null
pdone

progress "Generowanie danych testowych"
python manage.py shell -c "from common.generate_test_data import generate
generate()"
pdone
