jsprog_event_key_012c = function(type, code, value)
   if value ~= 0 then
       local count=0
       while count<20 do        
         jsprog_presskey(34)
         jsprog_releasekey(34)
         jsprog_delay(500)
         count = count+1
       end
   end
end

jsprog_event_key_012a = function(type, code, value)
   if value ~= 0 then
       local count=0
       while count<30 do        
         jsprog_presskey(30)
         jsprog_releasekey(30)
         jsprog_delay(333)
         count = count+1
       end
   end
end
