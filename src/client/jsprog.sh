#!/bin/sh

scriptdir=`dirname $0`
scriptdir=`cd ${scriptdir} && pwd`

PYTHONPATH="${scriptdir}:${PYTHONPATH}"
export PYTHONPATH

exec python -m jsprog.jsprog "$@"
