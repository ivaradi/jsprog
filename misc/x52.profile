<?xml version="1.0"?>
<joystickProfile name="Proba3" autoLoad="yes">
  <identity>
    <inputID busType="usb" vendor="06a3" product="075c" version="0111"/>
    <name>Saitek Saitek X52 Flight Control System</name>
    <phys>usb-0000:00:1d.0-1.5/input0</phys>
    <uniq/>
  </identity>
  <shiftLevels>
    <shiftLevel>
      <shiftState/>
      <shiftState>
        <key name="BTN_PINKIE" value="1"/>
      </shiftState>
    </shiftLevel>
    <shiftLevel>
      <shiftState/>
      <shiftState>
        <key name="BTN_BASE4" value="1"/>
      </shiftState>
    </shiftLevel>
  </shiftLevels>
  <keys>
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
  </keys>
</joystickProfile>
