"""Mouth shapes (the faceplate's m_* values): the 2D-animation lip-sync set
X..H (Preston Blair / Rhubarb letters) and named expressions."""

MOUTHS = {
 "X rest": {},
 "A  M B P": {
  "m_arch": 0.0,
  "m_w": 1.7
 },
 "B  K S T EE": {
  "m_o": 0.3,
  "m_w": 1.8,
  "m_up": 0.8,
  "m_r": 0.5,
  "m_tu": 1,
  "m_tl": 0.6
 },
 "C  EH": {
  "m_o": 0.8,
  "m_w": 1.8,
  "m_up": 0.9,
  "m_r": 0.7,
  "m_vee": 0.3,
  "m_tu": 1,
  "m_tg": 0.6
 },
 "D  AA": {
  "m_o": 1.05,
  "m_w": 1.9,
  "m_up": 0.88,
  "m_r": 0.75,
  "m_vee": 0.3,
  "m_tu": 1,
  "m_tg": 0.7
 },
 "E  AO ER": {
  "m_o": 0.8,
  "m_w": 1.3,
  "m_up": 0.85,
  "m_r": 1.0,
  "m_vee": 0.35,
  "m_tg": 0.4
 },
 "F  OO W": {
  "m_o": 0.38,
  "m_w": 0.75,
  "m_up": 0.7,
  "m_r": 1.0
 },
 "G  F V": {
  "m_o": 0.25,
  "m_w": 1.8,
  "m_up": 0.8,
  "m_r": 0.3,
  "m_tu": 1
 },
 "H  L": {
  "m_o": 0.65,
  "m_w": 1.7,
  "m_up": 0.88,
  "m_r": 0.7,
  "m_vee": 0.3,
  "m_tu": 1,
  "m_tg": 1.0
 },
 "surprised O": {
  "m_o": 0.85,
  "m_w": 1.25,
  "m_up": 0.92,
  "m_r": 1.0,
  "m_vee": 0.38,
  "m_arch": 0.0,
  "m_tu": 0.6
 },
 "shout": {
  "m_o": 0.85,
  "m_w": 1.75,
  "m_up": 0.92,
  "m_r": 0.9,
  "m_vee": 0.3,
  "m_arch": 0.05,
  "m_tu": 0.8
 },
 "grimace": {
  "m_o": 0.6,
  "m_w": 2.2,
  "m_up": 0.88,
  "m_r": 0.8,
  "m_vee": 0.25,
  "m_arch": 0.08,
  "m_tilt": 0.1,
  "m_tu": 1
 },
 "clenched teeth": {
  "m_o": 0.22,
  "m_w": 1.9,
  "m_up": 0.75,
  "m_r": 0.4,
  "m_arch": 0.12,
  "m_tu": 1,
  "m_tl": 1
 },
 "frown line": {
  "m_o": 0.06,
  "m_w": 1.9,
  "m_arch": 0.2
 },
 "smile": {
  "m_arch": -0.2,
  "m_w": 2.0
 },
 "open smile": {
  "m_o": 0.55,
  "m_arch": -0.25,
  "m_up": 0.2,
  "m_r": 0.6,
  "m_w": 2.1,
  "m_tu": 1
 },
 "smirk": {
  "m_arch": -0.06,
  "m_tilt": 0.14,
  "m_w": 1.8
 },
 "sad": {
  "m_arch": 0.26,
  "m_w": 1.6
 },
 "tongue (talking)": {
  "m_o": 0.6,
  "m_w": 1.7,
  "m_up": 0.85,
  "m_r": 0.7,
  "m_vee": 0.3,
  "m_tu": 1,
  "m_tg": 1.0
 }
}

VISEME = {k.split()[0]: v for k, v in MOUTHS.items() if len(k.split()[0]) == 1}
