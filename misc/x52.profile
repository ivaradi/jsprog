<?xml version="1.0"?>
<joystickProfile name="Proba3" autoLoad="yes">
  <identity>
    <inputID busType="usb" vendor="06a3" product="075c" version="0111"/>
    <name>Saitek Saitek X52 Flight Control System</name>
    <phys>usb-0000:00:1d.0-1.5/input0</phys>
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
        <key name="BTN_PINKIE" value="1"/>
      </virtualState>
    </shiftLevel>
    <shiftLevel>
      <virtualState/>
      <virtualState>
        <key name="BTN_BASE4" value="1"/>
      </virtualState>
    </shiftLevel>
  </shiftLevels>
  <controls>
    <key name="BTN_TRIGGER">
      <shift fromState="0" toState="0">
        <shift fromState="0" toState="0">
          <action type="simple" repeatDelay="25">
            <keyCombination leftShift="yes">KEY_A</keyCombination>
            <keyCombination>KEY_B</keyCombination>
          </action>
        </shift>
        <shift fromState="1" toState="1">
          <action type="simple">
            <keyCombination leftShift="yes">KEY_C</keyCombination>
            <keyCombination>KEY_D</keyCombination>
          </action>
        </shift>
      </shift>
      <shift fromState="1" toState="1">
        <shift fromState="0" toState="1">
          <action type="simple">
            <keyCombination leftShift="yes">KEY_G</keyCombination>
            <keyCombination>KEY_H</keyCombination>
          </action>
        </shift>
      </shift>
    </key>
    <key name="BTN_BASE5">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="0">
          <action type="mouseMove" direction="vertical" a="5" repeatDelay="40"/>
        </shift>
        <shift fromState="1" toState="1">
          <action type="mouseMove" direction="vertical" a="10" repeatDelay="40"/>
        </shift>
      </shift>
    </key>
    <key name="BTN_BASE6">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="0">
          <action type="mouseMove" direction="vertical" a="-5" repeatDelay="40"/>
        </shift>
        <shift fromState="1" toState="1">
          <action type="mouseMove" direction="vertical" a="-10" repeatDelay="40"/>
        </shift>
      </shift>
    </key>
    <key name="KEY_0X12C">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="0">
          <action type="mouseMove" direction="horizontal" a="5" repeatDelay="40"/>
        </shift>
        <shift fromState="1" toState="1">
          <action type="mouseMove" direction="horizontal" a="10" repeatDelay="40"/>
        </shift>
      </shift>
    </key>
    <key name="KEY_0X12D">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="0">
          <action type="mouseMove" direction="horizontal" a="-5" repeatDelay="40"/>
        </shift>
        <shift fromState="1" toState="1">
          <action type="mouseMove" direction="horizontal" a="-10" repeatDelay="40"/>
        </shift>
      </shift>
    </key>
    <virtualControl name="POVHat">
      <virtualState value="1">
        <shift fromState="0" toState="0">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination>KEY_U</keyCombination>
            </action>
          </shift>
        </shift>
        <shift fromState="1" toState="1">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination leftShift="yes">KEY_U</keyCombination>
            </action>
          </shift>
        </shift>
      </virtualState>
      <virtualState value="2">
        <shift fromState="0" toState="0">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination>KEY_U</keyCombination>
              <keyCombination>KEY_R</keyCombination>
            </action>
          </shift>
        </shift>
        <shift fromState="1" toState="1">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination leftShift="yes">KEY_U</keyCombination>
              <keyCombination leftShift="yes">KEY_R</keyCombination>
            </action>
          </shift>
        </shift>
      </virtualState>
      <virtualState value="3">
        <shift fromState="0" toState="0">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination>KEY_R</keyCombination>
            </action>
          </shift>
        </shift>
        <shift fromState="1" toState="1">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination leftShift="yes">KEY_R</keyCombination>
            </action>
          </shift>
        </shift>
      </virtualState>
      <virtualState value="4">
        <shift fromState="0" toState="0">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination>KEY_D</keyCombination>
              <keyCombination>KEY_R</keyCombination>
            </action>
          </shift>
        </shift>
        <shift fromState="1" toState="1">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination leftShift="yes">KEY_D</keyCombination>
              <keyCombination leftShift="yes">KEY_R</keyCombination>
            </action>
          </shift>
        </shift>
      </virtualState>
      <virtualState value="5">
        <shift fromState="0" toState="0">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination>KEY_D</keyCombination>
            </action>
          </shift>
        </shift>
        <shift fromState="1" toState="1">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination leftShift="yes">KEY_D</keyCombination>
            </action>
          </shift>
        </shift>
      </virtualState>
      <virtualState value="6">
        <shift fromState="0" toState="0">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination>KEY_D</keyCombination>
              <keyCombination>KEY_L</keyCombination>
            </action>
          </shift>
        </shift>
        <shift fromState="1" toState="1">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination leftShift="yes">KEY_D</keyCombination>
              <keyCombination leftShift="yes">KEY_L</keyCombination>
            </action>
          </shift>
        </shift>
      </virtualState>
      <virtualState value="7">
        <shift fromState="0" toState="0">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination>KEY_L</keyCombination>
            </action>
          </shift>
        </shift>
        <shift fromState="1" toState="1">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination leftShift="yes">KEY_L</keyCombination>
            </action>
          </shift>
        </shift>
      </virtualState>
      <virtualState value="8">
        <shift fromState="0" toState="0">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination>KEY_U</keyCombination>
              <keyCombination>KEY_L</keyCombination>
            </action>
          </shift>
        </shift>
        <shift fromState="1" toState="1">
          <shift fromState="0" toState="1">
            <action type="simple">
              <keyCombination leftShift="yes">KEY_U</keyCombination>
              <keyCombination leftShift="yes">KEY_L</keyCombination>
            </action>
          </shift>
        </shift>
      </virtualState>
    </virtualControl>
  </controls>
</joystickProfile>
