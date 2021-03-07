#!/bin/bash

set -e -u

scriptdir=$(readlink -f $(dirname $0))

usage() {
    echo "Usage: $0 destdir release <drone-build.sh arguments>"
}

if test $# -lt 2; then
    usage
    exit 1
fi

destdir="${1}"
shift

release="${1}"
shift

image=ivaradi/debian-build:${release}

workspace=$(mktemp -d)
trap "rm -rf ${workspace}" EXIT

"${scriptdir}/drone-build.sh" "$@" -w "${workspace}" ${image} /build/run.sh scripts/build debian-binary.sh ${release}

mkdir -p "${destdir}"
cp "${workspace}/"*.deb "${destdir}"

docker run --rm -v "${workspace}:/drone" ${image} rm -rf /drone/jsprog
