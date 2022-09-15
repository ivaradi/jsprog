# JSProg - Joystick Programmer

This program can be used to assign various key-presses or mouse movements
to be executed when you press a button on your joystick or move an axis.
It is possible to define some controls or combinations thereof as
*shift* states, allowing you to use certain controls for several
purposes depending on the actual shift state. For example,
in case of a flight simulator, if your controller has a view hat,
it can act as a view hat to look around in the neutral shift state,
but in another shift state it may be programmed to bring up camera
presets to show different parts of the instrument panels.

The actions to be executed are implemented as Lua scripts at the lowest
level ensuring flexibility. However, configuration is usually done at a
higher level using the GUI (e.g. simply specifying key combinations to
be "pressed" when a button is hit). Yet, it is possible to provide Lua
snippets to be executed for cases not covered by the higher-level
configuration support.

The program handles joystick type definitions. A few are provided,
but one can easily create and edit such definitions within the GUI.
The type definitions include proper naming of the various buttons and
axes instead of the default generated by the program and possibly
one or more pictures of the controller labeled with those names.

It is possible to define several *profiles* for a certain type of
joysticks. A profile can be defined to be automatically loaded when
a joystick of the given type is plugged into the computer.

As of now, there is no separate manual or other user documentation
for the software. However, the GUI has many detailed tooltips, which
can help using it.

## Installing

### Ubuntu Bionic, Focal, Jammy and Kinetic

The Ubuntu packaged version of the application is available in a PPA,
and can be installed as follows:

```bash
sudo add-apt-repository ppa:ivaradi/jsprog
sudo apt-get install jsprog-client
```

### Debian Bullseye

The Debian packaged version of the application can be installed from the OpenSuSE
build service:

```bash
sudo wget -nv -O /etc/apt/trusted.gpg.d/jsprog.asc https://download.opensuse.org/repositories/home:/ivaradi/Debian_11/Release.key

echo "deb https:download.opensuse.org/repositories/home:/ivaradi/Debian_11/ /" | sudo tee -a /etc/apt/sources.list.d/jsprog.list

sudo apt-get update
sudo apt-get install jsprog-client
```

It is recommended to install the `gnome-shell-extension-appindicator` package,
and enable it in the GNOME Shell. If so, all controllers will have a small icon
in the top bar with a menu.

## Building

JSProg requires the following packages as prerequisites for building:

* automake
* autoconf
* libtool
* C++ compiler
* glib >= 2.0
* gio >= 2.0
* Lua library >= 5.2
* libxml >= 2.0
* Python >= 3.6
* Python 3 DBus package
* Python 3 GI package with the following repositories: Gdk 3.0, Gtk 3.0, Gio, GLib,
  GdkPixbuf, cairo, Pango, PangoCairo 1.0 and optionally AppIndicator3 0.1

The software can be built after cloning the Git repository as follows:

1. `git submodule init`
1. `git submodule update`
1. `./autogen.sh`
1. `./configure`
1. `make`
1. `make install`
