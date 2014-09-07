<?xml version="1.0"?>
<jsprogProfile>
  <prologue><![CDATA[
    running=false
    lower=false
  ]]></prologue>
  <axis name="ABS_X">
    if value &lt; 85 then
      if not lower or not running then
         lower=true
         running=true
         jsprog_cancelall()
         while true do
           jsprog_presskey(jsprog_KEY_L)
           jsprog_releasekey(jsprog_KEY_L)
           jsprog_delay(25)
         end
      end
   elseif value &gt; 160 then
      if lower or not running then
         lower=false
         running=true
         jsprog_cancelall()
         while true do
           jsprog_presskey(jsprog_KEY_U)
           jsprog_releasekey(jsprog_KEY_U)
           jsprog_delay(25)
         end
      end
    else
      if running then
        running=false
        jsprog_cancelall()
      end
    end
  </axis>
  <epilogue/>
</jsprogProfile>
