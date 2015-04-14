set -e
set -u
branch=`git rev-parse --abbrev-ref HEAD`
if [ "$branch" != "develop" ]; then
    echo "You may only generate releases from the develop branch!"
    exit 1
fi
git diff --exit-code

tox

current_version=`cat version`
echo "Current version: $current_version"
read -e -p "Enter new version: " new_version
echo "Using $new_version"
read -r -p "Are you sure? [Y/n]" response
response=${response,,} # tolower
if [[ $response =~ ^(n|no| ) ]]; then
    exit 1
fi
echo $new_version > version
git add version
git commit -m "Release $new_version"
git tag -a $new_version -m "Release $new_version"
git push origin develop

git checkout master
git merge develop
git push origin master

python setup.py register -r pypi
python setup.py sdist upload -r pypi
