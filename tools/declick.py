"""Remove 1-3 ms clicks (the spikes at the start of voice clips in the finished mixes made before
src/audio.py faded clip edges) from a video's soundtrack (spikes far above the local level), bridging each with a
smooth curve between the clean samples around it; the picture is copied untouched.
    python tools/declick.py IN.mp4 OUT.mp4

Check with tools/review_part.py afterwards (its click detector should report none)."""
import subprocess, sys
import numpy as np
src, dst = sys.argv[1], sys.argv[2]
SR = 48000
raw = subprocess.run(["ffmpeg","-nostdin","-v","error","-i",src,"-vn","-ac","2","-ar",str(SR),"-f","f32le","-"],capture_output=True,check=True).stdout
y = np.frombuffer(raw, np.float32).reshape(-1,2).astype(np.float64).copy()
a = np.abs(y).max(axis=1)
hop = int(0.001*SR)
pk = np.array([a[i:i+hop].max() for i in range(0, len(a)-hop, hop)])
lvl = np.array([np.median(pk[max(0,i-20):i+20]) for i in range(len(pk))])
fixed = []
i = 0
while i < len(pk):
    if pk[i] > 0.5 and pk[i] > 8*lvl[i]:
        # the click: from the first ms over 4x the local level to the last one, in this 6 ms window
        j0 = i
        while j0 > 0 and pk[j0-1] > 4*lvl[i]: j0 -= 1
        j1 = i
        while j1 < min(len(pk)-1, i+6) and pk[j1+1] > 4*lvl[i]: j1 += 1
        s0, s1 = max(1,(j0)*hop - int(0.0005*SR)), min(len(y)-2, (j1+1)*hop + int(0.0005*SR))
        for c in range(2):
            # a raised-cosine bridge from the sample before to the sample after, scaled to the local level
            u = np.linspace(0, 1, s1 - s0)
            y[s0:s1, c] = y[s0-1, c]*(1-u) + y[s1, c]*u
        fixed.append((s0/SR, s1/SR, float(pk[i])))
        i = j1 + 3
    else:
        i += 1
for s0, s1, p in fixed: print(f"fixed {s0:.4f}-{s1:.4f} s (peak {p:.2f})")
p = subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",src,"-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                    "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart",
                    dst], input=y.astype(np.float32).tobytes())
p.check_returncode()
print(len(fixed), "clicks removed ->", dst)
