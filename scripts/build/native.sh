#!/bin/bash

set -e -u -x

distribution="${1}"

cd "${DRONE_WORKSPACE}"

git config --global user.email "drone@nowhere.org"
git config --global user.name "Drone User"

git submodule update --init

git fetch origin debian/dist/${distribution}/${DRONE_TARGET_BRANCH}
git checkout origin/debian/dist/${distribution}/${DRONE_TARGET_BRANCH}

export DEBIAN_FRONTEND=noninteractive
echo "y" | mk-build-deps --install debian/control

git checkout "${DRONE_COMMIT}"

./autogen.sh
./configure
make dist

basever="$(cat configure.ac | grep "AC_INIT" | sed -E 's:AC_INIT\(jsprog, ([0-9.]+), .+:\1:')"

cd ..
tar xf "${DRONE_WORKSPACE}/jsprog-${basever}.tar.gz"

cd "jsprog-${basever}"
./configure
make
make install
