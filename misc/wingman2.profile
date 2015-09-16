<?xml version="1.0"?>
<joystickProfile name="Proba2" autoLoad="no">
  <identity>
    <inputID busType="usb" vendor="046d" product="c283" version="0100"/>
    <name>Logitech Inc. WingMan Force 3D</name>
    <phys>usb-0000:00:1d.1-1/input0</phys>
    <uniq/>
  </identity>
  <shiftControls>
    <key name="BTN_PINKIE"/>
    <key name="BTN_BASE"/>
  </shiftControls>
  <keys>
    <key name="BTN_TRIGGER">
      <shift fromState="0" toState="0">
        <shift fromState="0" toState="0">
          <action type="simple" repeatDelay="100">
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
    <key name="BTN_TOP">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="0">
          <action type="mouseMove" direction="vertical" a="5" repeatDelay="40"/>
        </shift>
        <shift fromState="1" toState="1">
          <action type="mouseMove" direction="vertical" a="10" repeatDelay="40"/>
        </shift>
      </shift>
    </key>
    <key name="BTN_TOP2">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="0">
          <action type="mouseMove" direction="vertical" a="-5" repeatDelay="40"/>
        </shift>
        <shift fromState="1" toState="1">
          <action type="mouseMove" direction="vertical" a="-10" repeatDelay="40"/>
        </shift>
      </shift>
    </key>
    <key name="BTN_THUMB">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="0">
          <action type="mouseMove" direction="horizontal" a="5" repeatDelay="40"/>
        </shift>
        <shift fromState="1" toState="1">
          <action type="mouseMove" direction="horizontal" a="10" repeatDelay="40"/>
        </shift>
      </shift>
    </key>
    <key name="BTN_THUMB2">
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
