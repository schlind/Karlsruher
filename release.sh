#!/usr/bin/env sh
echo
VERSION=$(python3 karlsruher/version.py)
echo "Releasing $VERSION"
if [ -z "$(git status --porcelain)" ]; then
  echo
  python3 ./setup.py sdist
  git tag -a v$VERSION -m "Tagging release v$VERSION"
  echo
  echo "Upload:"
  echo '# git push --tags'
  echo "# python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/karlsruher-$VERSION.tar.gz"
  echo "# python3 -m twine upload dist/karlsruher-$VERSION.tar.gz"
  echo
else
  echo
  echo "# git status"
  echo "# git add ."
  echo "# git commit -m \"Preparing release v$VERSION\""
  echo '# git push'
  exit 1
fi
