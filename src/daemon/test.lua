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


