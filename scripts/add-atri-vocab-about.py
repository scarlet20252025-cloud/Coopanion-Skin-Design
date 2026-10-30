# -*- coding: utf-8 -*-
"""Give every vocab word the `about` field Coopanion requires, then it can load.

The app rejected the pack with:

    形象包没加载: ...\\figures\\atri-v011:vocab.neutral.about 缺失

`readManifest()` validates each word through `readVocab()`, which wants, per word: a `kind` in
{expression, motion}, at least one usable `name`, a finite positive `seconds` (checked below), and an
`about` Names object. The `about` is what the model reads to know what a word *means* - it lands in
the vocabulary table next to the name, e.g. 平静 / 默认的脸, or 招手 / 笑着打招呼.

`about` only needs one language to pass, but the model writes in the app language, so this fills zh
always and en where the phrase is not trivially the same. Ids not listed fall back to a description
built from the word's own name and kind, so a new word can never break the pack again.

Usage:
    .venv/Scripts/python.exe scripts/add-atri-vocab-about.py [pack-dir-name]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK_NAME = sys.argv[1] if len(sys.argv) > 1 else "atri-v011"
PACK = ROOT / "packs" / PACK_NAME

# id -> {"zh":..., "en":...}. Written as what the word *does on this body*, because the model picks
# words to express a feeling and needs to know how each one will look.
ABOUT = {
    # ---- expressions (the face) ----
    "neutral":   {"zh": "默认的脸，没什么特别情绪", "en": "the default face, no particular feeling"},
    "happy":     {"zh": "眼睛弯成笑弧，鼻子形状的嘴张开，开心的样子", "en": "eyes curve into smiling arcs, the mouth opens"},
    "wink":      {"zh": "一只眼闭上、另一只睁开，俏皮地眨眼", "en": "one eye shuts, the other stays open"},
    "love":      {"zh": "眼睛变成爱心，脸上发红，冒小心心", "en": "heart-shaped eyes, blushing, little hearts float up"},
    "shy":       {"zh": "半垂着眼，视线躲开，脸红得明显", "en": "lids lowered, gaze turned away, blushing hard"},
    "surprised": {"zh": "眼睛睁大，头顶冒出感叹号", "en": "eyes go wide, an exclamation mark overhead"},
    "angry":     {"zh": "眉毛压低，头顶冒怒气符号，身子发抖", "en": "brows lowered, an anger mark overhead, body shaking"},
    "sad":       {"zh": "八字眉，眼睛半垂，掉眼泪", "en": "brows slant down, lids lowered, tears fall"},
    "smug":      {"zh": "半眯着眼斜看，嘴角带笑，得意的样子", "en": "a narrowed sidelong look and a smirk"},
    "worried":   {"zh": "八字眉，冒冷汗，替人着急", "en": "brows slant down, a cold sweat"},
    "flustered": {"zh": "眼睛挤成 > <，满脸通红冒汗，手足无措", "en": "eyes squeezed to > <, flushed and sweating"},
    "scared":    {"zh": "眼睛瞪大，冒汗，身子发抖", "en": "eyes wide, sweating, shaking"},
    "excited":   {"zh": "眼睛里闪着星星，期待的样子", "en": "stars sparkle in the eyes"},
    "dizzy":     {"zh": "圈圈眼，头顶转着三颗星，身体摇晃", "en": "spiral eyes, three stars circling overhead, swaying"},
    "confused":  {"zh": "一脸不解，头顶冒问号", "en": "a puzzled face, a question mark overhead"},
    "pout":      {"zh": "嘴嘟起来，脸红，扭头不太高兴", "en": "pouts, blushes and turns away"},
    "determined": {"zh": "眼神压低，一脸认真", "en": "a lowered gaze, a serious face"},
    "sleepy":    {"zh": "半闭着眼打哈欠，犯困", "en": "squints and yawns"},
    "thinking":  {"zh": "眼睛往上看，头顶冒圈，正在想的模样", "en": "looks up, rings rise overhead"},
    "cry":       {"zh": "闭着眼大哭，眼泪流下来", "en": "eyes shut, wailing"},
    # ---- motions (the body) ----
    "stand":  {"zh": "站起来", "en": "stands up"},
    "wave":   {"zh": "抬手挥一挥，笑着打招呼", "en": "raises a hand and waves hello"},
    "walk":   {"zh": "沿屏幕边缘走一段", "en": "walks along the edge"},
    "run":    {"zh": "跑起来，跑到屏幕另一边", "en": "runs to the other side"},
    "jump":   {"zh": "原地跳一下", "en": "jumps on the spot"},
    "hop":    {"zh": "小小蹦一下", "en": "a small hop"},
    "look":   {"zh": "左右张望", "en": "looks left and right"},
    "turn":   {"zh": "转身面向另一边", "en": "turns to face the other way"},
    "nod":    {"zh": "点头，表示同意", "en": "nods in agreement"},
    "shake":  {"zh": "摇头，表示不同意", "en": "shakes its head"},
    "spin":   {"zh": "原地转一圈", "en": "spins around once"},
    "sit":    {"zh": "坐下，可以一直保持", "en": "sits down and stays"},
    "sleep":  {"zh": "坐下打盹，可以一直保持", "en": "dozes off sitting and stays"},
    "bow":    {"zh": "鞠一躬", "en": "bows"},
    "shiver": {"zh": "缩起身子发抖", "en": "huddles up and shivers"},
    "dance":  {"zh": "踩着节拍摇摆，冒音符", "en": "sways to a beat with music notes"},
    "flap":   {"zh": "开心地蹦起来扑腾", "en": "bounces and flaps about happily"},
    "drag":   {"zh": "被拎起来时的手脚乱摆", "en": "limbs flailing while picked up"},
}
# ids that exist on some builds but not others, mapped onto the wording of their sibling above
ALIAS = {"dragged": "drag", "tremble": "shiver", "hop": "hop", "look": "look"}


def fallback(word):
    """A usable about for a word nobody described: its own name plus what kind of thing it is."""
    names = word.get("names") or {}
    zh = next((v[0] for v in names.values() if isinstance(v, list) and v), word.get("id", "?"))
    kind = "表情" if word.get("kind") == "expression" else "动作"
    return {"zh": f"{zh}，{kind}", "en": f"{word.get('id', '?')} ({word.get('kind', '?')})"}


def main():
    if not PACK.is_dir():
        sys.exit(f"pack not found: {PACK}")
    mf = PACK / "figure.json"
    d = json.loads(mf.read_text(encoding="utf-8"))
    vocab = d.get("vocab") or []
    if not vocab:
        sys.exit("no vocab to fill")

    added, kept, fallbacks = 0, 0, []
    for w in vocab:
        wid = w.get("id")
        desc = ABOUT.get(wid) or ABOUT.get(ALIAS.get(wid, ""), None)
        if desc is None:
            desc = fallback(w)
            fallbacks.append(wid)
        cur = w.get("about")
        if isinstance(cur, dict) and any(isinstance(s, str) and s.strip() for s in cur.values()):
            kept += 1
            continue
        w["about"] = desc
        added += 1

    mf.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[vocab] {len(vocab)} words: filled about for {added}, kept {kept} existing")
    if fallbacks:
        print(f"[vocab] generic description used for: {fallbacks}")
    for w in vocab[:3]:
        print(f"  {w['id']:12s} {w['kind']:10s} seconds={w['seconds']}  about={w['about'].get('zh')}")


if __name__ == "__main__":
    main()
