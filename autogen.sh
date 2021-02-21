#!/bin/sh

rm -rf config.cache autom4te.cache

autoreconf -i -I autotools

rm -rf autom4te.cache
