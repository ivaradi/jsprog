#!/bin/sh

exec dbus-monitor "type='signal',sender='hu.varadiistvan.JSProg',interface='hu.varadiistvan.JSProg'"
