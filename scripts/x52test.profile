<?xml version="1.0"?>
<jsprogProfile>
  <prologue><![CDATA[
    function handle_pov(horizontal, vertical)
       if horizontal == 0 and vertical == 0 then
           return
       end

       local key = -1
       if horizontal == -1 then
          if vertical == -1 then
             key = jsprog_KEY_KP7
          elseif vertical==0 then
             key = jsprog_KEY_KP4
          else
             key = jsprog_KEY_KP1
          end
       elseif horizontal == 0 then
          if vertical == -1 then
             key = jsprog_KEY_KP8
          elseif vertical == 1 then
             key = jsprog_KEY_KP2
          end
       else
          if vertical == -1 then
             key = jsprog_KEY_KP9
          elseif vertical==0 then
             key = jsprog_KEY_KP6
          else
             key = jsprog_KEY_KP3
          end
       end

       if key ~= -1 then
          jsprog_presskey(key)
          jsprog_releasekey(key)
       end
    end

    function handle_mouse(code, value)
       jsprog_cancelall()
       if value<5 or value>10 then
          while true do
             jsprog_moverel(code, value-8)
             jsprog_delay(20)
          end
       end
    end
  ]]></prologue>
  <key code="0x012c"><![CDATA[
   if value == 0 then
      jsprog_cancelprevious()
   else
      local shiftNeeded = jsprog_iskeypressed(jsprog_BTN_PINKIE)
      while true do
         if shiftNeeded then
            jsprog_presskey(jsprog_KEY_LEFTSHIFT)
         end
         jsprog_presskey(jsprog_KEY_G)
         jsprog_releasekey(jsprog_KEY_G)
         if shiftNeeded then
            jsprog_releasekey(jsprog_KEY_LEFTSHIFT)
         end
         jsprog_delay(500)
      end
   end
  ]]></key>
  <key code="298"><![CDATA[
   if value == 0 then
      jsprog_cancelall()
   else
       local count=0
       while count<30 do
         jsprog_presskey(jsprog_KEY_H)
         jsprog_releasekey(jsprog_KEY_H)
         jsprog_delay(333)
         count = count+1
       end
   end
  ]]></key>
  <key name="BTN_BASE3"><![CDATA[
   if value ~= 0 then
      jsprog_cancelallofkey(0x12a)
   end
  ]]></key>
  <key name="BTN_BASE4"><![CDATA[
   if value ~= 0 then
      jsprog_cancelallofkey(0x12c)
   end
  ]]></key>
  <key name="BTN_TRIGGER"><![CDATA[
   if value ~= 0 then
      jsprog_cancelallofjoystick()
   end
  ]]></key>
  <axis name="ABS_HAT0X">
   handle_pov(value, jsprog_getabs(0x11))
  </axis>
  <axis name="ABS_HAT0Y">
   handle_pov(jsprog_getabs(0x10), value)
  </axis>
  <axis code="0x28">
    handle_mouse(jsprog_REL_X, value)
  </axis>
  <axis code="0x29">
    handle_mouse(jsprog_REL_Y, value)
  </axis>
  <key name="BTN_TRIGGER_HAPPY16">
   if value == 0 then
      jsprog_releasekey(jsprog_BTN_LEFT)
   else
      jsprog_presskey(jsprog_BTN_LEFT)
   end
  </key>
  <key name="BTN_TRIGGER_HAPPY17">
    jsprog_moverel(jsprog_REL_WHEEL, -1)
  </key>
  <key name="BTN_TRIGGER_HAPPY18">
    jsprog_moverel(jsprog_REL_WHEEL, 1)
  </key>
  <epilogue/>
</jsprogProfile>
