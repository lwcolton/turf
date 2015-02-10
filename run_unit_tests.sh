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
