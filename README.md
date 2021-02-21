# JSProg - Joystick Programmer

This program can be used to assign various operations to be executed when
you press a button on your joystick or move an axis. It is possible to
define some controls or combinations thereof as *shift* states, allowing
you to use certain controls for several purposes depending on the actual
shift state.

The actions to be executed are implemented as Lua scripts at the lowest
level ensuring flexibility. However, configuration is usually done at a
higher level (e.g. simply specifying key combinations to be "pressed"
when a button is pressed). Yet, it is possible to provide Lua snippets
to be executed for cases not covered by the higher-level configuration
support.

It is possible to define several *profiles* for a certain type of
joysticks. A profile can be defined to be automatically loaded when
a joystick of the given type is attached to the computer.

## Building

The software can be built after cloning the Git repository as follows:

1. git submodule init
2. git submodule update
3. ./configure
4. make
5. make install
