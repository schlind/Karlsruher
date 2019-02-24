#!/usr/bin/env sh
python3 -m pytest --verbose --cov=karlsruher --cov-report=html
python3 -m pylint karlsruher
