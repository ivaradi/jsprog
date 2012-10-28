#!/bin/sh

exec dbus-send --print-reply --dest=hu.varadiistvan.JSProg /hu/varadiistvan/JSProg hu.varadiistvan.JSProg.loadProfile uint32:$1 string:"`cat $2`"
