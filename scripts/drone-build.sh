#!/bin/bash

set -e -u

workspace=$(mktemp -d)

usage() {
    echo "Usage: $0 [-c <commit ID>] [-b branch] [-w workspace] image command..."
}

scriptdir=$(cd $(dirname $0) && pwd)
repodir=$(readlink -f "${scriptdir}/..")

commit_id=""
target_branch="master"
workspace=""

while getopts "c:b:w:" o; do
    case "${o}" in
        c)
            commit_id="${OPTARG}"
            ;;
        b)
            target_branch="${OPTARG}"
            ;;
        w)
            workspace="${OPTARG}"
            ;;
        *)
            usage 1>&2
            exit 1
            ;;
    esac
done

shift $(($OPTIND - 1))

image="${1}"
shift

if test -z "${workspace}"; then
    workspace=$(mktemp -d)
    trap "rm -rf ${workspace}" EXIT
fi

sourcedir="${workspace}/jsprog"
mkdir -p "${sourcedir}"
git init "${sourcedir}"

cd "${sourcedir}"
git remote add origin "${repodir}"
git fetch origin "+refs/heads/${target_branch}"
if test -z "${commit_id}"; then
    commit_id=$(git rev-parse FETCH_HEAD)
fi
git  checkout "${commit_id}" -b "${target_branch}"

docker run --rm -v "${workspace}:/drone" -v "${repodir}:${repodir}:ro" -w "/drone" -e HOME=/drone -e "DRONE_TARGET_BRANCH=${target_branch}" -e "DRONE_COMMIT=${commit_id}" -e "DRONE_WORKSPACE=/drone/jsprog" "${image}" "$@"
