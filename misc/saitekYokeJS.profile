<?xml version="1.0"?>
<joystickProfile name="Saitek X-Plane" autoLoad="yes">
  <identity>
    <inputID busType="usb" vendor="06a3" product="0bac" version="0100"/>
    <name>Saitek Saitek Pro Flight Yoke</name>
    <uniq/>
  </identity>
  <virtualControls>
    <virtualControl name="POVHat">
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="0" toValue="0"/>
        <axis name="ABS_HAT0Y" fromValue="0" toValue="0"/>
      </virtualState>
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="0" toValue="0"/>
        <axis name="ABS_HAT0Y" fromValue="-1" toValue="-1"/>
      </virtualState>
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="1" toValue="1"/>
        <axis name="ABS_HAT0Y" fromValue="-1" toValue="-1"/>
      </virtualState>
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="1" toValue="1"/>
        <axis name="ABS_HAT0Y" fromValue="0" toValue="0"/>
      </virtualState>
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="1" toValue="1"/>
        <axis name="ABS_HAT0Y" fromValue="1" toValue="1"/>
      </virtualState>
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="0" toValue="0"/>
        <axis name="ABS_HAT0Y" fromValue="1" toValue="1"/>
      </virtualState>
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="-1" toValue="-1"/>
        <axis name="ABS_HAT0Y" fromValue="1" toValue="1"/>
      </virtualState>
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="-1" toValue="-1"/>
        <axis name="ABS_HAT0Y" fromValue="0" toValue="0"/>
      </virtualState>
      <virtualState>
        <axis name="ABS_HAT0X" fromValue="-1" toValue="-1"/>
        <axis name="ABS_HAT0Y" fromValue="-1" toValue="-1"/>
      </virtualState>
    </virtualControl>
  </virtualControls>
  <shiftLevels>
    <shiftLevel>
      <virtualState/>
      <virtualState>
        <key name="BTN_BASE" value="1"/>
      </virtualState>
      <virtualState>
        <key name="BTN_BASE2" value="1"/>
      </virtualState>
    </shiftLevel>
  </shiftLevels>
  <controls>
    <virtualControl name="POVHat">
      <virtualState value="0"> <!-- Center -->
        <shift fromState="0" toState="2">
          <action type="nop"/>
        </shift>
      </virtualState>

      <virtualState value="1">  <!-- Forward -->
        <shift fromState="0" toState="0">
          <action type="simple">
            <keyCombination leftControl="yes" leftShift="yes">KEY_F8</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="1">
          <action type="simple">
            <keyCombination>KEY_KP0</keyCombination>
          </action>
        </shift>
        <shift fromState="2" toState="2">
          <action type="simple">
            <keyCombination>KEY_KP4</keyCombination>
          </action>
        </shift>
      </virtualState>

      <virtualState value="2"> <!-- Forward right -->
        <shift fromState="0" toState="0">
          <action type="simple">
            <keyCombination leftControl="yes" leftShift="yes">KEY_F1</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="2">
          <action type="nop"/>
        </shift>
      </virtualState>

      <virtualState value="3"> <!-- Right -->
        <shift fromState="0" toState="0">
          <action type="simple">
            <keyCombination leftControl="yes" leftShift="yes">KEY_F2</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="1">
          <action type="simple">
            <keyCombination>KEY_KP1</keyCombination>
          </action>
        </shift>
        <shift fromState="2" toState="2">
          <action type="simple">
            <keyCombination>KEY_KP5</keyCombination>
          </action>
        </shift>
      </virtualState>

      <virtualState value="4"> <!-- Backward right -->
        <shift fromState="0" toState="0">
          <action type="simple">
            <keyCombination leftControl="yes" leftShift="yes">KEY_F3</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="2">
          <action type="nop"/>
        </shift>
      </virtualState>

      <virtualState value="5">  <!-- Backward -->
        <shift fromState="0" toState="0">
          <action type="simple">
            <keyCombination leftControl="yes" leftShift="yes">KEY_F4</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="1">
          <action type="simple">
            <keyCombination>KEY_KP2</keyCombination>
          </action>
        </shift>
        <shift fromState="2" toState="2">
          <action type="simple">
            <keyCombination>KEY_KP6</keyCombination>
          </action>
        </shift>
      </virtualState>

      <virtualState value="6"> <!-- Backward left -->
        <shift fromState="0" toState="0">
          <action type="simple">
            <keyCombination leftControl="yes" leftShift="yes">KEY_F5</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="2">
          <action type="nop"/>
        </shift>
      </virtualState>

      <virtualState value="7">  <!-- Left -->
        <shift fromState="0" toState="0">
          <action type="simple">
            <keyCombination leftControl="yes" leftShift="yes">KEY_F6</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="1">
          <action type="simple">
            <keyCombination>KEY_KP3</keyCombination>
          </action>
        </shift>
        <shift fromState="2" toState="2">
          <action type="simple">
            <keyCombination>KEY_KP7</keyCombination>
          </action>
        </shift>
      </virtualState>

      <virtualState value="8">  <!-- Forward left -->
        <shift fromState="0" toState="0">
          <action type="simple">
            <keyCombination leftControl="yes" leftShift="yes">KEY_F7</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="2">
          <action type="nop"/>
        </shift>
      </virtualState>

    </virtualControl>
  </controls>
</joystickProfile>
