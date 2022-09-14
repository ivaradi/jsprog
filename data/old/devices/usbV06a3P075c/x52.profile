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
    <virtualControl name="POVHat1">
      <virtualState>
        <key name="BTN_DEAD" value="0"/>
        <key name="BTN_TRIGGER_HAPPY1" value="0"/>
        <key name="BTN_TRIGGER_HAPPY2" value="0"/>
        <key name="BTN_TRIGGER_HAPPY3" value="0"/>
      </virtualState>
      <virtualState>
        <key name="BTN_DEAD" value="1"/>
        <key name="BTN_TRIGGER_HAPPY1" value="0"/>
        <key name="BTN_TRIGGER_HAPPY2" value="0"/>
        <key name="BTN_TRIGGER_HAPPY3" value="0"/>
      </virtualState>
      <virtualState>
        <key name="BTN_DEAD" value="1"/>
        <key name="BTN_TRIGGER_HAPPY1" value="1"/>
        <key name="BTN_TRIGGER_HAPPY2" value="0"/>
        <key name="BTN_TRIGGER_HAPPY3" value="0"/>
      </virtualState>
      <virtualState>
        <key name="BTN_DEAD" value="0"/>
        <key name="BTN_TRIGGER_HAPPY1" value="1"/>
        <key name="BTN_TRIGGER_HAPPY2" value="0"/>
        <key name="BTN_TRIGGER_HAPPY3" value="0"/>
      </virtualState>
      <virtualState>
        <key name="BTN_DEAD" value="0"/>
        <key name="BTN_TRIGGER_HAPPY1" value="1"/>
        <key name="BTN_TRIGGER_HAPPY2" value="1"/>
        <key name="BTN_TRIGGER_HAPPY3" value="0"/>
      </virtualState>
      <virtualState>
        <key name="BTN_DEAD" value="0"/>
        <key name="BTN_TRIGGER_HAPPY1" value="0"/>
        <key name="BTN_TRIGGER_HAPPY2" value="1"/>
        <key name="BTN_TRIGGER_HAPPY3" value="0"/>
      </virtualState>
      <virtualState>
        <key name="BTN_DEAD" value="0"/>
        <key name="BTN_TRIGGER_HAPPY1" value="0"/>
        <key name="BTN_TRIGGER_HAPPY2" value="1"/>
        <key name="BTN_TRIGGER_HAPPY3" value="1"/>
      </virtualState>
      <virtualState>
        <key name="BTN_DEAD" value="0"/>
        <key name="BTN_TRIGGER_HAPPY1" value="0"/>
        <key name="BTN_TRIGGER_HAPPY2" value="0"/>
        <key name="BTN_TRIGGER_HAPPY3" value="1"/>
      </virtualState>
      <virtualState>
        <key name="BTN_DEAD" value="1"/>
        <key name="BTN_TRIGGER_HAPPY1" value="0"/>
        <key name="BTN_TRIGGER_HAPPY2" value="0"/>
        <key name="BTN_TRIGGER_HAPPY3" value="1"/>
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
        <!--key name="BTN_BASE4" value="1"/-->
        <virtualControl name="POVHat1" value="1"/>
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
          <action type="advanced" repeatDelay="40">
            <enter>
              <mouseMove direction="horizontal" a="5"/>
            </enter>
          </action>
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
            <action type="script">
              <enter>
                <line>jsprog_presskey(jsprog_KEY_U)</line>
                <line>jsprog_releasekey(jsprog_KEY_U)</line>
              </enter>
              <leave>
                <line>jsprog_presskey(jsprog_KEY_R)</line>
                <line>jsprog_releasekey(jsprog_KEY_R)</line>
              </leave>
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
    <axis name="ABS_MISC">
      <shift fromState="0" toState="0">
        <shift fromState="0" toState="1">
          <valueRange fromValue="4" toValue="12">
            <action type="mouseMove" direction="horizontal" adjust="8" b="1" repeatDelay="10"/>
          </valueRange>
          <valueRange fromValue="0" toValue="3">
            <action type="mouseMove" direction="horizontal" adjust="8" b="1.5" repeatDelay="10"/>
          </valueRange>
          <valueRange fromValue="13" toValue="15">
            <action type="mouseMove" direction="horizontal" adjust="8" b="1.5" repeatDelay="10"/>
          </valueRange>
        </shift>
      </shift>
      <shift fromState="1" toState="1">
        <shift fromState="0" toState="1">
          <action type="mouseMove" direction="horizontal" adjust="8" b="3" repeatDelay="10"/>
        </shift>
      </shift>
    </axis>
    <axis name="ABS_0X029">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="1">
          <action type="mouseMove" direction="vertical" adjust="8" b="1" repeatDelay="10"/>
        </shift>
      </shift>
    </axis>
    <key name="BTN_TRIGGER_HAPPY15">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="1">
          <action type="advanced">
            <enter>
              <keyPress>BTN_LEFT</keyPress>
            </enter>
            <leave>
              <keyRelease>BTN_LEFT</keyRelease>
            </leave>
          </action>
        </shift>
      </shift>
    </key>
    <key name="BTN_TRIGGER_HAPPY17">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="1">
          <action type="mouseMove" direction="wheel" a="2"/>
        </shift>
      </shift>
    </key>
    <key name="BTN_TRIGGER_HAPPY18">
      <shift fromState="0" toState="1">
        <shift fromState="0" toState="1">
          <action type="mouseMove" direction="wheel" a="-2"/>
        </shift>
      </shift>
    </key>
  </controls>
</joystickProfile>
