#!/usr/bin/env sh
echo
VERSION=$(python karlsruher/version.py)
echo "Releasing $VERSION"
if [ -z "$(git status --porcelain)" ]; then
  echo
  python3 ./setup.py sdist
  echo
  echo "Clean:"
  echo "# rm -rf build dist htmlcov *.egg-info"
  echo "# git tag -a versions/v$VERSION -m \"Tagging release v$VERSION\""
  echo '# git push --tags'
  echo
  echo "Upload:"
  echo
  echo "# python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/karlsruher-$VERSION.tar.gz"
  echo
  echo "# python3 -m twine upload dist/karlsruher-$VERSION.tar.gz"
  echo
else
  echo
  echo "# git status"
  echo "# git add ."
  echo "# git commit -m \"Preparing release v$VERSION\""
  echo "# git tag -a versions/v$VERSION -m \"Tagging release v$VERSION\""
  echo '# git push --tags'
  exit 1
fi
