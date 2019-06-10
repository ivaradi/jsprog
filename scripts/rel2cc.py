#!/usr/bin/env python3

rel = {}
maxValue = -1

with open("rel", "rt") as f:
    line = f.readline()
    while line:
        line = line.strip();
        if line:
            words = line.split()
            name = words[0]
            value = words[1]
            try:
                value = int(value[2:], 16) if value.startswith("0x") \
                        else int(value)
                maxValue = max(maxValue, value)
                rel[value] = name
            except:
                pass
        line = f.readline()

for value in range(0, maxValue+1):
    if (value%8)==0:
        print("    // %d (0x%03x)" % (value, value))
    if value in rel:
        print("    \"%s\"," % (rel[value],))
    else:
        print("    \"ABS_0X%03X\"," % (value,))
