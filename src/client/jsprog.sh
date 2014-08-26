#!/bin/sh

scriptdir=`dirname $0`

PYTHONPATH="${scriptdir}:${PYTHONPATH}"
export PYTHONPATH

exec python -m jsprog.jsprog "$@"
