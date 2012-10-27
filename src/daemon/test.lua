jsprog_event_key_012c = function(type, code, value)
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
end

jsprog_event_key_012a = function(type, code, value)
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
end

jsprog_event_key_0128 = function(type, code, value)
   if value ~= 0 then
      jsprog_cancelallofkey(0x12a)
   end
end

jsprog_event_key_0129 = function(type, code, value)
   if value ~= 0 then
      jsprog_cancelallofkey(0x12c)
   end
end

jsprog_event_key_0120 = function(type, code, value)
   if value ~= 0 then
      jsprog_cancelallofjoystick()
   end
end

handle_pov = function(horizontal, vertical)
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

jsprog_event_abs_0010 = function(type, code, value)
   handle_pov(value, jsprog_getabs(0x11))
end

jsprog_event_abs_0011 = function(type, code, value)
   handle_pov(jsprog_getabs(0x10), value)
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

function jsprog_event_abs_0028(type, code, value)
   handle_mouse(jsprog_REL_X, value)
end

function jsprog_event_abs_0029(type, code, value)
   handle_mouse(jsprog_REL_Y, value)
end
