#!/bin/bash
/code/venv/bin/coverage run /code/src/manage.py test
/code/venv/bin/coverage report
