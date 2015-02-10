set -e
set -u
branch=`git rev-parse --abbrev-ref HEAD`
if [ "$branch" != "master" ]; then
    echo "You may only generate pypi releases from the master branch!"
    exit 1
fi
git diff --exit-code
python setup.py register -r pypi
python setup.py sdist upload -r pypi
