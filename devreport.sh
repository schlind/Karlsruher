#!/usr/bin/env sh

python3 -m unittest -v
python3 -m pytest --cov=karlsruher tests --cov-report=html
python3 -m pylint karlsruher
