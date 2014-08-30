PYTHON=python
.PHONY: none messages compile
LOCS=-l fi -l en
MM_ARGS=${LOCS} -i KirppuVenv --no-location

none:

messages:
	${PYTHON} manage.py makemessages -d djangojs ${MM_ARGS}
	${PYTHON} manage.py makemessages -d django ${MM_ARGS}

compile:
	${PYTHON} manage.py compilemessages
