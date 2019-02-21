#!/usr/bin/env sh

python3 -m unittest -v && python3 -m karlsruher -help
python3 -m pylint karlsruher
python3 -m pytest --cov=karlsruher tests --cov-report=html
