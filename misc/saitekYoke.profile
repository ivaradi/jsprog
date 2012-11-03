<?xml version="1.0"?>
<jsprogProfile>
  <prologue><![CDATA[
    button_C1=0x126
    button_C2=0x127

    c1Keys = {}
    c1Keys[3] = jsprog_KEY_KP0
    c1Keys[7] = jsprog_KEY_KP1
    c1Keys[5] = jsprog_KEY_KP2
    c1Keys[1] = jsprog_KEY_KP3

    c2Keys = {}
    c2Keys[3] = jsprog_KEY_KP4
    c2Keys[7] = jsprog_KEY_KP5
    c2Keys[5] = jsprog_KEY_KP6
    c2Keys[1] = jsprog_KEY_KP7

    pvKeys = {}
    pvKeys [0] = jsprog_KEY_F7
    pvKeys [1] = jsprog_KEY_F6
    pvKeys [2] = jsprog_KEY_F5
    pvKeys [3] = jsprog_KEY_F8
    pvKeys [4] = jsprog_KEY_F8
    pvKeys [5] = jsprog_KEY_F4
    pvKeys [6] = jsprog_KEY_F1
    pvKeys [7] = jsprog_KEY_F2
    pvKeys [8] = jsprog_KEY_F3

    function handle_pov(horizontal, vertical)
       local c1Pressed = jsprog_iskeypressed(button_C1)
       local c2Pressed = jsprog_iskeypressed(button_C2)

       local value = (horizontal+1)*3 + (vertical+1)

       if c1Pressed or c2Pressed then
           local key = nil
           if c1Pressed then
               key = c1Keys[value]
           elseif c2Pressed then
               key = c2Keys[value]
           end

           if key then
              jsprog_presskey(key)
              jsprog_releasekey(key)
           end
       else
           local key = pvKeys[value]
           if key then
              jsprog_presskey(jsprog_KEY_LEFTCTRL)
              jsprog_presskey(jsprog_KEY_LEFTSHIFT)
              jsprog_presskey(key)
              jsprog_releasekey(key)
              jsprog_releasekey(jsprog_KEY_LEFTSHIFT)
              jsprog_releasekey(jsprog_KEY_LEFTCTRL)
           end
       end
    end
  ]]></prologue>
  <axis name="ABS_HAT0X">
   handle_pov(value, jsprog_getabs(0x11))
  </axis>
  <axis name="ABS_HAT0Y">
   handle_pov(jsprog_getabs(0x10), value)
  </axis>
  <epilogue/>
</jsprogProfile>
