
import sys, time
sys.path.insert(0, r"E:\workspace\new\scripts")
from fetch_yahoo import yahoo
for s in ["^GSPC","^IRX"]:
    for attempt in range(3):
        try:
            yahoo(s); break
        except Exception as e:
            print(s,"try",attempt,type(e).__name__,str(e)[:80]); time.sleep(3)
