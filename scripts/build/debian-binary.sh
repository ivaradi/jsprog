#!/bin/bash

set -e -u -x

apt-get update -y

distribution="${1}"

cd "${DRONE_WORKSPACE}"

git config --global user.email "drone@nowhere.org"
git config --global user.name "Drone User"

git submodule update --init

git fetch origin debian/dist/${distribution}/${DRONE_TARGET_BRANCH}
git checkout origin/debian/dist/${distribution}/${DRONE_TARGET_BRANCH}

git merge ${DRONE_COMMIT} < /dev/null

export DEBIAN_FRONTEND=noninteractive
echo "y" | mk-build-deps --install debian/control

debuild -us -uc -b
