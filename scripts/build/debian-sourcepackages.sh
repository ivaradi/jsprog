#!/bin/bash

set -e -u -x

scriptdir=$(cd $(dirname $0) && pwd)

env

UBUNTU_DISTRIBUTIONS="bionic focal jammy kinetic"
DEBIAN_DISTRIBUTIONS="buster bullseye"

PPA_RELEASE=ppa:ivaradi/jsprog
PPA_BETA=ppa:ivaradi/jsprog-beta
PPA_DEV=ppa:ivaradi/jsprog-dev

if test -z "${DRONE_WORKSPACE}"; then
    DRONE_WORKSPACE=`pwd`
fi

signopt="-us -uc"
upload="no"

set +x
if test "${DEBIAN_SECRET_KEY:-}" -a "${DEBIAN_SECRET_IV:-}"; then
    openssl aes-256-cbc -K $DEBIAN_SECRET_KEY -iv $DEBIAN_SECRET_IV -in "${scriptdir}/../signing-key.txt.enc" -d | gpg --import

    openssl aes-256-cbc -K $DEBIAN_SECRET_KEY -iv $DEBIAN_SECRET_IV -in "${scriptdir}/../oscrc.enc" -out ~/.oscrc -d

    touch ~/.upload_packages

    export DEBUILD_DPKG_BUILDPACKAGE_OPTS=-k7D14AA7B
    signopt="-k2265D8767D14AA7B"
    if test -z "${DRONE_PULL_REQUEST:-}"; then
        upload="yes"
    fi
fi
set -x

wsname=$(basename "${DRONE_WORKSPACE}")

cd "${DRONE_WORKSPACE}"

git config --global user.email "drone@nowhere.org"
git config --global user.name "Drone User"

git submodule update --init

tag="${DRONE_TAG:-}"

releasetype="dev"
if [[ "$tag" =~ ^v[0-9.]+$ ]]; then
    releasetype="release"
    ppa="${PPA_RELEASE}"
    obs_project="home:ivaradi"
elif [[ "$tag" =~ ^v[0-9.]+-.*$ ]]; then
    releasetype="beta"
    ppa="${PPA_BETA}"
    obs_project="home:ivaradi:beta"
else
    releasetype="dev"
    ppa="${PPA_DEV}"
    obs_project="home:ivaradi:alpha"
fi

basever="$(cat configure.ac | grep "AC_INIT" | sed -E 's:AC_INIT\(jsprog, ([0-9.]+), .+:\1:')"
version="${basever}-$(date +%Y%m%d.%H%M%S).$(git rev-parse --short ${DRONE_COMMIT})"

set +x
echo "===================================================================================="
echo "Building with upload=$upload, tag=$tag, releasetype=$releasetype, version=$version"
echo "===================================================================================="
set -x

cd ..
# Seems to check only the presence of the file, but it can be empty
#touch "../jsprog_${basever}.orig.tar.bz2"
#cp -a "${DRONE_WORKSPACE}" "jsprog_${version}"
tar cjf "jsprog_${version}.orig.tar.bz2" --exclude .git --transform "s:^${wsname}:jsprog_${version}:" "${wsname}"
#tar cjf "jsprog_${version}.orig.tar.bz2" --exclude .git "jsprog_${version}"

cd "${DRONE_WORKSPACE}"

for distribution in ${UBUNTU_DISTRIBUTIONS} ${DEBIAN_DISTRIBUTIONS}; do
    set +x
    echo "===================================================================================="
    echo "Building for $distribution"
    echo "===================================================================================="
    set -x

    fullversion="${version}-1.0~${distribution}1"

    git checkout -- .
    git clean -xdf

    git fetch origin debian/dist/${distribution}/${DRONE_TARGET_BRANCH}
    git checkout origin/debian/dist/${distribution}/${DRONE_TARGET_BRANCH}

    git merge ${DRONE_COMMIT} < /dev/null

    gbp dch --distribution ${distribution} --new-version=${fullversion} --ignore-branch  --git-author

    debuild -d -S ${signopt} -sa
done

cd ..
ls -al

if test "${upload}" = "yes"; then
    for distribution in ${UBUNTU_DISTRIBUTIONS}; do
        dput "${ppa}" *${distribution}*_source.changes
    done

    for distribution in ${DEBIAN_DISTRIBUTIONS}; do
        package="jsprog.${distribution}"
        subdir="${obs_project}/${package}"

        mkdir -p osc
        pushd osc
        osc co ${obs_project} ${package}
        if test "$(ls ${subdir})"; then
            osc delete ${subdir}/*
        fi

        pkgvertag="~${distribution}1"

        cp ../jsprog*.orig.tar.* ${subdir}/
        cp ../jsprog_*[0-9.][0-9]${pkgvertag}.dsc ${subdir}/
        cp ../jsprog_*[0-9.][0-9]${pkgvertag}.debian.tar* ${subdir}/
        cp ../jsprog_*[0-9.][0-9]${pkgvertag}_source.changes ${subdir}/
        osc add ${subdir}/*

        cd ${subdir}
        osc commit -m "Drone update"
        popd
    done
fi
