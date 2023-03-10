#!/bin/bash


# constants
ALPHA=1


# functions
function progress {
       echo -e "\ndeploy.sh: $1\n"
}

function abort_if_error {
       if [[ $? -ne 0 ]]; then
               progress "Last command exited with error status $?, aborting"
               exit
       fi
}


# parsing arguments

while getopts ab:dhps option; do
       case $option in
               a) NO_DEPLOYMENT=1;;
               b) DEPLOYMENT_BRANCH=$OPTARG;;
               d) DRY_RUN=1;;
               h) HELP=1;;
               p) NO_PULL=1;;
               s) NO_STATIC=1;;
       esac
done


# displaying help

if [[ $HELP -eq 1 ]]; then
       echo "Dozwolone opcje to:"
       echo "        -a    Nie wykonuje deploymentu"
       echo "        -b    Uzywa galezi podanej jako argument dla tej opcji"
       echo "        -d    Nie zmienia niczego na serwerach, nie wykonuje pulla"
       echo "        -h    Wyswietla ten komunikat pomocy"
       echo "        -p    Nie wykonuje git pull"
       echo "        -s    Nie aktualizuje plikow statycznych"
       echo "Oznaczenia opcji moga ulegac zmianom."
       exit
fi


# collecting static files

if [[ $ALPHA -eq 1 ]]; then
	cp deploy_logo/jj300x90.png joyjoin/common/static/common/img/logo/
	abort_if_error
fi
progress "Collecting static files"
source venv/bin/activate
abort_if_error
echo "STATIC_ROOT = '../static/'" >> ./joyjoin/joyjoin/settings.py
abort_if_error
python joyjoin/manage.py collectstatic --no-input --verbosity 0
abort_if_error
git reset -q --hard
abort_if_error


# preparing the app deployment

progress "Preparing the app for deployment"
SETTINGS_APPENDIX="

# Added by deploy.sh script by Hubert Jasieniecki <jasieniecki@mat.umk.pl>

ALLOWED_HOSTS = ['joyjoin.space']
CSRF_COOKIE_SECURE = True
DEBUG = False
MEDIA_ROOT = 'media/'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 1800
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

STATIC_URL = '/static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'PORT': '5432',
        'NAME': 'joyjoin_two',
        'USER': 'joyjoin',
        'PASSWORD': '',
    }
}

SECRET_KEY = ''"
echo "$SETTINGS_APPENDIX" >> ./joyjoin/joyjoin/settings.py
abort_if_error


# printing the success message
progress "Success! JoyJoin was prepared for deployment!"
echo -e "Teraz należy wykonać następujące kroki:"
echo -e "\tUstawić wartość SECRET_KEY w joyjoin/joyjoin/settings.py"
echo -e "\tZakomitować zmiany do nowej gałęzi deployment_20200517a używając obecnej daty"
echo -e "\t\tW przypadku większej ilości deploymentów dziennie użyć następnej litery alfabetu"
echo -e "\t\tNie zapomnij o dodaniu nowego katalogu static"
echo -e "\tWypchnąć zmiany do repozytorium Gandiego (git+ssh://4687577@git.dc2.gpaas.net/default.git)"
echo -e "\tWywołać deployment przez"
echo -e "\t\tssh 4687577@git.dc2.gpaas.net deploy default.git deployment_20200517a"
echo -e "\tW razie potrzeby zastępując default.git odpowiednią nazwą domenową"
