PYTHON=python
.PHONY: none messages compile

none:

messages:
	${PYTHON} manage.py makemessages\
 -d djangojs -d django\
 -l fi -l en\
 -i KirppuVenv

compile:
	${PYTHON} manage.py compilemessages
