#!/bin/bash

if [[ ! -v VIRTUALENV ]]; then
	source ../venv/bin/activate
fi

alias test='bash utils/test.sh'
alias testd='bash utils/test_django.sh'
alias testf='bash utils/test_flake8.sh'
alias testv='bash utils/test_validate.sh'
alias rdb='bash utils/refresh_db.sh'
alias pp='python manage.py shell -c "from post.print_punctation import print_punctation_for_posts
print_punctation_for_posts()"'
alias tp='python manage.py shell -c "from post.print_punctation import print_punctation_for_tags
print_punctation_for_tags()"'
