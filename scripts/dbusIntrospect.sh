#!/bin/sh

exec dbus-send --print-reply --dest=hu.varadiistvan.JSProg /hu/varadiistvan/JSProg org.freedesktop.DBus.Introspectable.Introspect
