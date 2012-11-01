#!/bin/sh

exec dbus-send --print-reply --dest=hu.varadiistvan.JSProg /hu/varadiistvan/JSProg hu.varadiistvan.JSProg.startControlSignals uint32:$1
