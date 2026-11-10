import sys,json,collections
sys.path.insert(0,"scripts/check/h5")
from h5_rows import load_rows
rows=load_rows()
L=["provision:ed6be7ba-2807-11f1-b919-d73281fdb594","provision:5003ac4e-eb7e-11f0-a0a3-c9aae40c2eb7","provision:dfeea17c-e16c-11f0-ab71-f3424eab00a5","provision:ce3f81c0-2d53-11f1-8e98-9d68213c7640"]
for l in L:
    print(l,[ (r[0],r[1][-12:],r[3],r[4],r[5],r[6][-14:]) for r in rows if r[2]==l])
