#!/bin/sh

rm -rf config.cache autom4te.cache

${ACLOCAL:-aclocal} -I autotools
${AUTOCONF:-autoconf}
${AUTOMAKE:-automake} --add-missing

rm -rf autom4te.cache
