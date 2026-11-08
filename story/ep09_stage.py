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
    ep["skip_render"] = [[0, "rewind"], ["patch_upgrade.end", "end.end+1"]]

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
    U = up
    for who in ("steve", "noob"):
        c(who, "look", "holo_on", "noob_falling", head=U)
    # Episode 0
    c("noob", "expr", "r0", "noob_falling.end", face="scared")
    c("steve", "look", "steve_beginning", "steve_beginning.end+0.2", head=turn_to_noob)
    # Episode 1: the eye
    for who in ("steve", "noob"):
        c(who, "look", "r1", "patch_eye.end", head=U)
    c("noob", "expr", "noob_ep1", "noob_ep1.end", face="happy")
    c("noob", "raise_arm", "noob_ep1", "noob_ep1+1.2", arm="arm_r", angle=1.3, out=-0.1, ease=0.15)
    c("steve", "expr", "steve_sky", "patch_eye.end", face="surprised")
    c("noob", "expr", "patch_eye", "patch_unknown.end", face="scared")
    c("patch", "glitch_eye", "patch_eye+0.6", "patch_eye+1.1")
    c("noob", "look", "patch_unknown", "patch_unknown.end", head=[-0.15, 0, -0.45])
    c("patch", "face", "patch_unknown", "patch_unknown+0.3", yaw=0.35)
    # Episode 2: the plan, the button, the thing that waved
    for who in ("steve", "noob"):
        c(who, "look", "r2", "steve_watching", head=U)
    c("steve", "raise_arm", "steve_plan+1.4", "steve_plan.end", arm="arm_r", angle=0.9, out=-0.2, ease=0.2)
    c("noob", "expr", "noob_button", "noob_button.end", face="surprised")
    c("noob", "raise_arm", "noob_button", "noob_button.end", arm="arm_l", angle=1.6, out=0.3, ease=0.12)
    c("steve", "expr", "steve_three", "steve_three.end", face="unimpressed")
    c("noob", "expr", "patch_waved+1.0", "patch_waved.end", face="scared")
    c("steve", "look", "steve_watching", "steve_watching.end", head=[0.05, 0, 0.1])
    c("steve", "expr", "steve_watching", "steve_watching.end", face="surprised")
    # Episode 3
    c("noob", "look", "r3", "noob_dragon.end", head=U)
    c("noob", "expr", "noob_dragon", "noob_dragon.end", face="happy")
    c("steve", "look", "r3", "steve_you", head=U)
    c("steve", "look", "steve_you", "steve_you.end", head=turn_to_noob)
    c("steve", "raise_arm", "steve_you", "steve_you.end", arm="arm_r", angle=1.45, out=-0.35, ease=0.2)
    c("noob", "look", "steve_you", "steve_you.end+0.2", head=[0.2, 0, 0.1])
    # Episode 4: the block
    for who in ("steve", "noob"):
        c(who, "look", "r4", "noob_touched", head=U)
    c("noob", "expr", "noob_block", "noob_block.end", face="happy")
    c("steve", "expr", "steve_exist", "steve_exist.end", face="unimpressed")
    c("noob", "expr", "noob_touched", "noob_touched.end", face="happy")
    c("steve", "look", "noob_touched", "patch_arrived", head=turn_to_noob)
    c("noob", "raise_arm", "noob_touched", "noob_touched.end", arm="arm_l", angle=2.4, out=0.2, ease=0.15)
    for who in ("steve", "noob"):
        c(who, "look", "patch_arrived", "patch_arrived.end", head=U)
    c("patch", "face", "patch_arrived", "patch_arrived+0.3", yaw=0.35)
    c("steve", "look", "steve_weirder", "steve_weirder.end", head=[0, 0, 0.3])
    c("steve", "expr", "steve_weirder", "steve_weirder.end", face="unimpressed")
    c("patch", "face", "patch_improvement", "patch_improvement+0.3", yaw=0.0)
    # Episode 5: creative mode made it worse
    for who in ("steve", "noob"):
        c(who, "look", "r5", "noob_close", head=U)
    c("noob", "cheer", "noob_creative", "noob_creative+0.7")
    c("noob", "expr", "noob_creative", "noob_close.end", face="happy")
    c("steve", "expr", "steve_list", "steve_list.end", face="unimpressed")
    c("noob", "raise_arm", "noob_close", "noob_close.end", arm="arm_r", angle=1.2, out=-0.3, ease=0.12)
    for who in ("steve", "noob"):
        c(who, "look", "patch_belong", "noob_duck", head=U)
    c("noob", "expr", "patch_worse", "noob_duck.end", face="scared")
    c("steve", "expr", "patch_worse", "noob_duck.end", face="surprised")
    c("noob", "look", "noob_duck", "noob_duck.end", head=[0.3, 0, 0])
    # Episode 6: Null on the screen: silence, then fear
    for who in ("steve", "noob"):
        c(who, "look", "r6", "steve_nobody", head=U)
    c("noob", "expr", "r6+0.6", "steve_nobody.end", face="scared")
    c("steve", "expr", "r6+0.8", "steve_nobody", face="surprised")
    c("steve", "look", "steve_nobody", "steve_nobody.end", head=turn_to_noob)
    c("patch", "glitch_eye", "r6+0.4", "r6+1.0")
    # Episode 7: it starts to make sense; the questions get bigger
    for who in ("steve", "noob"):
        c(who, "look", "r7", "patch_behind.end", head=U)
    c("noob", "expr", "patch_behind+1.5", "patch_behind.end", face="scared")
    c("steve", "look", "steve_sense", "steve_sense.end", head=[-0.1, 0, 0.2])
    c("noob", "look", "noob_bigger", "noob_bigger.end", head=turn_to_steve)
    c("noob", "expr", "noob_bigger", "noob_bigger.end", face="scared")
    for who in ("steve", "noob"):
        c(who, "look", "steve_howmany", "patch_counting", head=U)
    c("steve", "expr", "steve_howmany", "patch_counting.end", face="surprised")
    c("patch", "glitch_eye", "patch_counting+0.2", "patch_counting+0.6")
    # Episode 8: Steve dodges
    for who in ("steve", "noob"):
        c(who, "look", "r8", "noob_you", head=U)
    c("noob", "look", "noob_you", "noob_you+1.2", head=[0, 0, -0.62])         # turns slowly to Steve
    c("noob", "face", "noob_you", "noob_you+1.4", yaw=-0.75)
    c("noob", "raise_arm", "noob_you+1.6", "noob_you.end+0.2", arm="arm_r", angle=1.45, out=-0.4, ease=0.2)
    c("steve", "expr", "noob_you+1.0", "steve_next.end", face="surprised")
    c("steve", "look", "steve_next", "steve_next.end", head=[-0.15, 0, 0.35])   # ...to Patch, not the Noob
    c("noob", "expr", "noob_dontnext", "noob_dontnext.end", face="surprised")
    c("noob", "raise_arm", "noob_dontnext", "noob_dontnext.end", arm="arm_r", angle=1.45, out=-0.4, ease=0.1)
    c("noob", "face", "patch_lastslide", "patch_lastslide+0.4", yaw=0.0)
    c("patch", "face", "patch_lastslide", "patch_lastslide+0.3", yaw=0.0)
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
    # the recap: per episode, Patch's screen (a wide shot) while a line tells what
    # happened, close-ups for the jokes. ("holo", from, to, [(at, clip)]),
    # (who, from, to) for a close-up, ("two", from, to) for Noob and Steve.
    E = "assets/clips/ep09/"
    recap = [
        (0, [("holo", "holo_on", "steve_beginning", [("holo_on", "recap_ep0")]),
             ("steve", "steve_beginning", "r1")]),
        (1, [("holo", "r1", "patch_unknown", [("r1", "e1_tree"), ("steve_sky", "e1_sky")]),
             ("patch", "patch_unknown", "r2")]),
        (2, [("holo", "r2", "noob_button", [("r2", "e2_eye"), ("steve_plan+1.6", "e2_steps")]),
             ("noob", "noob_button", "steve_three"),
             ("holo", "steve_three", "steve_watching", [("steve_three", "e2_button"), ("steve_three+0.9", "e2_zombies"),
                                                         ("patch_waved", "e2_waved")]),
             ("steve", "steve_watching", "r3")]),
        (3, [("holo", "r3", "steve_you", [("r3", "recap_ep3")]), ("steve", "steve_you", "r4")]),
        (4, [("holo", "r4", "noob_touched", [("r4", "e4_dragon"), ("noob_block+1.3", "e4_block")]),
             ("noob", "noob_touched", "patch_arrived"),
             ("holo", "patch_arrived", "steve_weirder", [("patch_arrived", "e4_patch")]),
             ("steve", "steve_weirder", "patch_improvement"), ("patch", "patch_improvement", "r5")]),
        (5, [("holo", "r5", "noob_close", [("r5", "e5_build"), ("steve_list", "e5_statue"),
                                            ("steve_list+1.7", "e5_door")]),
             ("noob", "noob_close", "patch_belong"),
             ("holo", "patch_belong", "noob_duck", [("patch_belong", "e5_duck"), ("patch_belong+2.2", "e5_delete"),
                                                    ("patch_worse", "e5_chunk")]),
             ("noob", "noob_duck", "r6")]),
        (6, [("holo", "r6", "noob_dontlike", [("r6", "recap_ep6")]),
             ("noob", "noob_dontlike", "steve_nobody"), ("steve", "steve_nobody", "r7")]),
        (7, [("holo", "r7", "steve_sense", [("r7", "e7_bodies"), ("patch_behind+2.4", "e7_drift")]),
             ("two", "steve_sense", "steve_howmany"),
             ("holo", "steve_howmany", "patch_counting", [("steve_howmany", "e7_times")]),
             ("patch", "patch_counting", "r8")]),
        (8, [("holo", "r8", "steve_next", [("r8", "e8_portal")]),
             ("steve", "steve_next", "noob_dontnext"), ("noob", "noob_dontnext", "patch_lastslide")]),
    ]
    holos = []
    for k, segs in recap:
        for i, seg in enumerate(segs):
            if seg[0] == "holo":
                _, a, b, cl = seg
                sh.append(wide(f"holo{k}_{i}", a, b))
                # a vertical screen: the episode whole, as it was published, above Patch
                holos.append({"type": "holo", "from": a, "to": b, "label": f"ARCHIVE · EP {k}",
                              "w": 468, "h": 832, "y": 225,
                              "clips": [{"at": at, "video": E + v + ".mp4", "offset": 0.0} for at, v in cl]})
            elif seg[0] == "two":
                sh.append(two(f"two{k}_{i}", seg[1], seg[2]))
            else:
                sh.append(close(f"ep{k}_{seg[0]}{i}", seg[0], seg[1], seg[2]))
    sh.append(close("theories", "patch", "patch_lastslide", "card"))
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
