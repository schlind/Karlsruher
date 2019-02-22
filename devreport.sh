#!/usr/bin/env sh
python3 -m unittest -v tests
python3 -m pytest --cov=karlsruher tests --cov-report=html
python3 -m pylint karlsruher

echo
echo "Release:"
echo
echo "# rm -rf build dist htmlcov *.egg-info"
echo "# python3 setup.py sdist"
echo "# python3 -m twine upload dist/*"
echo
echo
