jsprog_event_key_012c = function(type, code, value)
   if value ~= 0 then
      local shiftNeeded = jsprog_iskeypressed(jsprog_BTN_PINKIE)
      local count=0
      while count<20 do        
         if shiftNeeded then
            jsprog_presskey(jsprog_KEY_LEFTSHIFT)
         end
         jsprog_presskey(jsprog_KEY_G)
         jsprog_releasekey(jsprog_KEY_G)
         if shiftNeeded then
            jsprog_releasekey(jsprog_KEY_LEFTSHIFT)
         end
         jsprog_delay(500)
         count = count+1
      end
   end
end

jsprog_event_key_012a = function(type, code, value)
   if value ~= 0 then
       local count=0
       while count<30 do        
         jsprog_presskey(jsprog_KEY_H)
         jsprog_releasekey(jsprog_KEY_H)
         jsprog_delay(333)
         count = count+1
       end
   end
end
