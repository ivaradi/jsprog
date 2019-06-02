#!/bin/sh

scriptdir=`dirname $0`
scriptdir=`cd ${scriptdir} && pwd`

PYTHONPATH="${scriptdir}:${PYTHONPATH}"
export PYTHONPATH

exec python3 -m jsprog.jsprog "$@"
