set -e
set -u
branch=`git rev-parse --abbrev-ref HEAD`
if [ "$branch" != "develop" ]; then
    echo "You may only generate releases from the develop branch!"
    exit 1
fi
git diff --exit-code
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
git checkout staging
git merge develop
git push origin staging
git checkout develop
git push origin develop
set -e
set -u
if [ $BUILDBOX_BRANCH = "develop" -o $BUILDBOX_BRANCH = "master" ]; then
    diff_staging=`git diff --quiet origin/staging; echo $?`
    if [ "$diff_staging" -eq 0 ]; then
        echo "Exiting because this is a release"
        exit 0
    fi
fi
tox
git checkout master
git merge $BUILDBOX_COMMIT
git push origin master
git checkout $BUILDBOX_COMMIT

set -e
set -u
branch=`git rev-parse --abbrev-ref HEAD`
if [ "$branch" != "master" ]; then
    echo "You may only generate pypi releases from the master branch!"
    exit 1
fi
git diff --exit-code
git pull origin master
python setup.py register -r pypi
python setup.py sdist upload -r pypi
