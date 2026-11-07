"""Episode 9's old-look half (the briefing, the recap, the theory, the start of
the upgrade), written into episodes/ep09_before_finale.json: actors, clips,
fx, shots, the holo and comment overlays, and the spans the new-look renderer
draws (skip_render). Run it again after changing the staging:

    python story/ep09_stage.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.join(HERE, "..", "episodes", "ep09_before_finale.json")

# the trio in a row in Episode 2's clearing, facing the camera (-y)
S = (5.0, 5.0, 0.0)
P = (6.2, 4.85, 2.55)
N = (7.4, 5.0, 0.0)
HEAD_S, HEAD_N = 1.75, 1.92


def shot(name, a, b, cam0, cam1, look, lens, look1=None, shake=0.0):
    s = {"name": name, "from": a, "to": b, "lens": lens,
         "path": [[a, list(cam0)], [b, list(cam1)]], "look": [[a, list(look)]]}
    if look1:
        s["look"].append([b, list(look1)])
    if shake:
        s["shake"] = shake
    return s


def wide(name, a, b):
    """The trio low in frame, Patch's screen above them (the holo overlay)."""
    return shot(name, a, b, (6.2, -2.6, 0.55), (6.2, -2.2, 0.6), (6.2, 5.0, 3.55), 22)


def wide_plain(name, a, b):
    return shot(name, a, b, (6.2, -1.2, 1.5), (6.2, -0.7, 1.5), (6.2, 5.0, 1.55), 24)


def close(name, who, a, b, push=0.18):
    if who == "steve":
        x, y, z = S[0], S[1], HEAD_S
        return shot(name, a, b, (x + 0.3, y - 2.4, z - 0.02), (x + 0.3, y - 2.4 + push, z - 0.02), (x, y, z - 0.18), 40)
    if who == "noob":
        x, y, z = N[0], N[1], HEAD_N
        return shot(name, a, b, (x - 0.3, y - 2.5, z - 0.05), (x - 0.3, y - 2.5 + push, z - 0.05), (x, y, z - 0.2), 40)
    x, y, z = P
    return shot(name, a, b, (x + 0.2, y - 2.6, z + 0.02), (x + 0.2, y - 2.6 + push, z + 0.02), (x, y, z - 0.12), 40)


def two(name, a, b):
    """Noob and Steve together (Patch over them)."""
    return shot(name, a, b, (6.2, -0.7, 1.6), (6.2, -0.45, 1.6), (6.2, 5.0, 1.65), 30)


def build():
    ep = json.load(open(EP))
    ep["sets"] = [{"kind": "forest_valley", "origin": [0, 0, 0]}]
    ep["actors"] = {
        "steve": {"rig": "steve", "faces": "moments", "at": list(S), "yaw": 0.0},
        "noob": {"rig": "noob", "faces": "moments", "at": list(N), "yaw": 0.0},
        "patch": {"rig": "patch", "s": 1.4, "at": list(P), "yaw": 0.0},
    }
    ep["fx"] = [{"kind": "sky", "below": "sky", "sun_dir": [0.3, 0.75, -0.6], "keys": [[0, 6.5, 2.0]]}]
    # the new-look renderer (src/lookdev/ep09_new.py) draws the hook and everything after the upgrade starts
    ep["skip_render"] = [[0, "rewind"], ["patch_upgrade.end", "end+0.4"]]

    turn_to_noob, turn_to_steve = [0, 0, 0.55], [0, 0, -0.55]
    up = [-0.32, 0, 0]                                    # looking up at Patch's screen
    clips = []

    def c(who, do, a, b, **kw):
        clips.append(dict({"who": who, "do": do, "from": a, "to": b}, **kw))

    # briefing: Noob waves at the new people; Steve sighs; Patch turns on
    c("noob", "wave", "noob_hi", "noob_hi+1.4", arm="arm_r")
    c("noob", "expr", "noob_hi", "noob_hi.end", face="happy")
    c("noob", "look", "noob_same", "noob_same.end+0.3", head=[0.15, 0, 0.05])
    c("steve", "look", "steve_eight", "steve_eight+1.6", head=[0.12, 0, 0])
    c("steve", "look", "steve_eight+1.6", "steve_eight.end", head=turn_to_noob)
    c("steve", "expr", "noob_same", "steve_eight+1.5", face="unimpressed")
    c("patch", "face", "patch_archive", "patch_archive+0.4", yaw=0.0)
    c("patch", "scan", "holo_on-0.4", "holo_off")
    # the recap: everyone watches the screen; reactions turn to each other
    for who in ("steve", "noob"):
        c(who, "look", "holo_on", "noob_falling", head=up)
    c("noob", "expr", "r0", "noob_falling.end", face="scared")
    c("steve", "look", "steve_beginning", "steve_beginning.end+0.2", head=turn_to_noob)
    c("noob", "look", "noob_deep", "noob_deep.end", head=[0.0, 0, -0.45])
    c("noob", "expr", "noob_deep+1.4", "noob_deep.end", face="surprised")
    c("steve", "look", "r1", "steve_tree.end", head=up)
    c("noob", "look", "r1", "noob_respect", head=up)
    c("noob", "expr", "noob_respect", "noob_respect.end", face="happy")
    c("noob", "pose", "noob_respect", "noob_respect.end", parts={"arm_r": [-0.4, 0, 0.6], "arm_l": [-0.4, 0, -0.6]})
    c("steve", "look", "r2", "noob_record", head=up)
    c("steve", "expr", "steve_plan", "noob_record.end", face="unimpressed")
    c("noob", "look", "noob_record", "noob_record.end", head=turn_to_steve)
    c("noob", "expr", "noob_record", "noob_record.end", face="happy")
    c("noob", "look", "r3", "noob_dragon.end", head=up)
    c("noob", "expr", "noob_dragon", "noob_dragon.end", face="happy")
    c("steve", "look", "steve_you", "steve_you.end", head=turn_to_noob)
    c("steve", "raise_arm", "steve_you", "steve_you.end", arm="arm_r", angle=1.45, out=-0.35, ease=0.2)
    c("noob", "look", "steve_you", "steve_you.end+0.2", head=[0.2, 0, 0.1])
    for who in ("steve", "noob"):
        c(who, "look", "r4", "patch_arrived.end", head=up)
    c("patch", "face", "patch_arrived", "patch_arrived+0.3", yaw=0.35)
    c("steve", "look", "steve_weirder", "steve_weirder.end", head=[0, 0, 0.3])
    c("steve", "expr", "steve_weirder", "steve_weirder.end", face="unimpressed")
    c("patch", "face", "patch_improvement", "patch_improvement+0.3", yaw=0.0)
    c("noob", "look", "r5", "r6", head=up)
    c("noob", "cheer", "noob_creative", "noob_creative+0.6")
    c("noob", "expr", "noob_creative", "noob_creative.end", face="happy")
    c("steve", "look", "r5", "r6", head=up)
    # Null on the screen: silence, then fear
    for who in ("steve", "noob"):
        c(who, "look", "r6", "steve_nobody", head=up)
    c("noob", "expr", "r6+0.6", "steve_nobody.end", face="scared")
    c("steve", "expr", "r6+0.8", "steve_nobody", face="surprised")
    c("steve", "look", "steve_nobody", "steve_nobody.end", head=turn_to_noob)
    c("patch", "glitch_eye", "r6+0.4", "r6+1.0")
    for who in ("steve", "noob"):
        c(who, "look", "r7", "patch_behind.end", head=up)
    c("noob", "expr", "noob_alot", "noob_alot.end", face="happy")
    c("noob", "raise_arm", "noob_alot", "noob_alot.end", arm="arm_l", angle=2.6, out=0.2, ease=0.18)
    for who in ("steve", "noob"):
        c(who, "look", "r8", "noob_you", head=up)
    c("noob", "look", "noob_you", "noob_you+1.2", head=[0, 0, -0.62])         # turns slowly to Steve
    c("noob", "face", "noob_you", "noob_you+1.4", yaw=-0.75)
    c("noob", "expr", "noob_you+0.5", "noob_you.end", face="unimpressed" if False else "neutral")
    c("noob", "raise_arm", "noob_you+1.6", "noob_you.end+0.2", arm="arm_r", angle=1.45, out=-0.4, ease=0.2)
    c("steve", "expr", "noob_you+1.0", "steve_next.end", face="surprised")
    c("steve", "look", "steve_next", "steve_next.end", head=[0.1, 0, 0.0])
    c("noob", "face", "steve_next", "steve_next+0.4", yaw=0.0)
    # the theory
    c("patch", "face", "patch_theories", "patch_theories+0.3", yaw=0.0)
    for who in ("steve", "noob"):
        c(who, "look", "card", "noob_oneofus.end", head=up)
    c("noob", "look", "look", "noob_itsyou.end", head=[0, 0, -0.62])
    c("noob", "face", "look", "look+0.5", yaw=-0.6)
    c("noob", "expr", "noob_itsyou", "noob_itsyou.end", face="unimpressed" if False else "surprised")
    c("steve", "look", "look+0.2", "steve_dying.end", head=turn_to_noob)
    c("steve", "expr", "noob_itsyou+1.0", "steve_dying.end", face="unimpressed")
    c("noob", "face", "steve_dying.end", "noob_which", yaw=0.0)
    c("noob", "look", "noob_which", "stare.end", head=[0, 0, 0.5])               # Noob asks Patch
    c("steve", "look", "noob_which", "stare.end", head=[0, 0, 0.35])
    c("patch", "face", "noob_which", "noob_which+0.3", yaw=-0.5)
    c("patch", "face", "stare", "stare+1.2", yaw=0.0)                              # ...and slowly to camera
    # the budget, and the upgrade begins
    c("noob", "expr", "noob_what", "noob_what.end", face="surprised")
    c("noob", "look", "noob_what", "noob_what.end", head=[0, 0, 0.45])
    c("patch", "scan", "patch_upgrade+0.4", "end")
    c("steve", "expr", "patch_upgrade", "end", face="surprised")
    c("noob", "expr", "patch_upgrade", "end", face="scared")
    ep["clips"] = clips

    sh = []
    sh.append(wide_plain("brief", "brief", "noob_hi+1.7"))
    sh.append(close("noob_hi", "noob", "noob_hi+1.7", "steve_eight"))
    sh.append(close("steve_eight", "steve", "steve_eight", "patch_archive"))
    sh.append(close("patch_archive", "patch", "patch_archive", "holo_on"))
    blocks = [  # (recap beat, first reaction line it shares the screen with, then close-ups)
        ("r0", "steve_beginning", [("steve", "steve_beginning"), ("noob", "noob_deep")], "r1"),
        ("r1", "noob_respect", [("noob", "noob_respect")], "r2"),
        ("r2", "noob_record", [("noob", "noob_record")], "r3"),
        ("r3", "steve_you", [("steve", "steve_you")], "r4"),
        ("r4", "steve_weirder", [("steve", "steve_weirder"), ("patch", "patch_improvement")], "r5"),
        ("r5", "noob_creative+2.2", [("noob", "noob_creative+2.2")], "r6"),
        ("r6", "noob_dontlike+1.6", [("noob", "noob_dontlike+1.6"), ("steve", "steve_nobody")], "r7"),
        ("r7", "patch_behind+3.0", [("patch", "patch_behind+3.0"), ("noob", "noob_alot")], "r8"),
        ("r8", "noob_you", [("noob", "noob_you"), ("steve", "steve_next")], "holo_off"),
    ]
    holos = []
    for k, (r, cut, closes, nxt) in enumerate(blocks):
        a = "holo_on" if r == "r0" else r
        sh.append(wide(f"holo_{r}", a, cut))
        for i, (who, start) in enumerate(closes):
            end = closes[i + 1][1] if i + 1 < len(closes) else nxt
            sh.append(close(f"{r}_{who}{i}", who, start, end))
        holos.append({"type": "holo", "video": f"assets/clips/ep09/recap_ep{k}.mp4", "from": a,
                      "to": f"{a}+4.0" if r != "r0" else "r0+4.0", "offset": 0.0 if r != "r0" else 0.0,
                      "label": f"ARCHIVE · EP {k}"})
    holos[0]["offset"] = 0.0
    sh.append(close("theories", "patch", "holo_off", "card"))
    sh.append(wide("card", "card", "look"))
    sh.append(two("itsyou", "look", "steve_dying"))
    sh.append(close("dying", "steve", "steve_dying", "noob_which"))
    sh.append(close("which", "noob", "noob_which", "stare"))
    sh.append(close("stare", "patch", "stare", "patch_budget", push=0.45))
    sh.append(wide_plain("budget", "patch_budget", "noob_what"))
    sh.append(close("what", "noob", "noob_what", "patch_upgrade"))
    sh.append(close("upgrade", "patch", "patch_upgrade", "patch_upgrade+1.5"))
    sh.append(wide_plain("upgrade_wide", "patch_upgrade+1.5", "patch_upgrade.end"))
    ep["shots"] = sh

    ov = [o for o in ep["overlays"] if o["type"] not in ("holo", "comment")]
    ov += holos
    ov.append({"type": "comment", "from": "card", "to": "look", "handle": "@youssefakram7493",
               "text": "Theory: ...one of them shouldn't be in a world...",
               "highlight": "one of them shouldn't be in a world",
               "hl_start": "noob_oneofus", "hl_dur": 2.2, "avatar_color": [0, 137, 123], "initial": "Y", "y": 560})
    ov = [o for o in ov if o["type"] not in ("rewind", "flash")]
    ov.append({"type": "rewind", "from": "rewind", "to": "brief", "src_from": 0.0, "src_to": "rewind"})
    ov.append({"type": "flash", "from": "brief", "to": "brief+0.3", "strength": 0.6})
    ov.append({"type": "flash", "from": "patch_upgrade.end", "to": "patch_upgrade.end+0.45"})
    ep["overlays"] = ov
    json.dump(ep, open(EP, "w"), indent=1, ensure_ascii=False)
    print(len(clips), "clips,", len(sh), "shots,", len(holos), "holo screens")


if __name__ == "__main__":
    build()
