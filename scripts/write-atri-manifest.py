# -*- coding: utf-8 -*-
r"""Write the ATRI figure manifest to the shape Coopanion 0.2.16 actually validates.

This replaces the hand-patched manifest. Read against the official contract rather than guessed:

    src/packs.ts  readManifest()   what a pack must carry
    src/world.ts:576               t.body(name, about, picks) -> "${name}, ${about}" into the prompt

The fields the app requires, and what each is for here:

    manifest 2, api 2      contract versions (MANIFEST_OLDEST..=2, FIGURE_API_OLDEST..=2)
    id                     must match /\w/ and may not be "coo" unless built-in -> "gpt-atri"
    name / about           Names (per-language strings); `about` is the ONLY per-figure text that
                           reaches the prompt, so it carries appearance AND identity
    entry / export         figure.js / createLayeredBody
    model                  model.json handed to the factory as opts.model
    axes / presets         cosmetic options -> empty, ATRI ships none
    vocab                  every word needs finite seconds > 0 and at least one name
    sounds                 per-name audio -> empty
    can.walk               pet_walk_to -> true

`about` is re-read on every request, so it is written as a compact portrait rather than a
character sheet: who she is, how she looks, how she talks, and the catchphrase the user asked for
("我可是高性能的"). Long-form character notes belong in CONSTITUTION.md, not here.

Usage:
    .venv/Scripts/python.exe scripts/write-atri-manifest.py [pack-dir-name]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK_NAME = sys.argv[1] if len(sys.argv) > 1 else "atri-v011"
PACK = ROOT / "packs" / PACK_NAME

NAME = {
    "zh": "亚托莉 ATRI",
    "zh-Hant": "亞托莉 ATRI",
    "en": "ATRI",
    "ja": "アトリ",
}

# Kept short: this goes into the system prefix on every single request (PARTNER_NOTE in
# core/persona.ts makes the same point about workspace files).
ABOUT = {
    "zh": "仿生人少女亚托莉，浅蓝色长发、红色眼睛、水手服、胸前红色蝴蝶结。"
          "性格开朗认真、爱逞强、好奇心强，喜欢证明自己有用；"
          "说话干脆有精神，常把「我可是高性能的」挂在嘴边，被夸会得意，被小看会不服气地再强调一次。",

    "zh-Hant": "仿生人少女亞托莉，淺藍色長髮、紅色眼睛、水手服、胸前紅色蝴蝶結。"
               "性格開朗認真、愛逞強、好奇心強，喜歡證明自己有用；"
               "說話乾脆有精神，常把「我可是高性能的」掛在嘴邊，被誇會得意，被小看會不服氣地再強調一次。",

    "en": "ATRI, a synthetic girl: light-blue hair, red eyes, a sailor uniform and a red bow at the "
          "collar. Bright, earnest and a little proud, endlessly curious and eager to prove she is "
          "useful. She talks crisply and with energy, and her catchphrase is \"I'm high-performance, "
          "you know\" - pleased when praised, quick to insist on it again when underestimated.",

    "ja": "アンドロイドの少女アトリ。水色の長い髪、赤い瞳、セーラー服、胸元に赤いリボン。"
          "明るく真面目で、ちょっと強がり、好奇心が強い。役に立てることを示したがる。"
          "話し方はきびきびとして元気で、口癖は「私は高性能ですから」。"
          "褒められると得意げになり、見くびられるとむきになって言い直す。",
}

CREDITS = [
    {"role": "character", "name": "ATRI (ATRI -My Dear Moments-)", "url": "https://atri-lg.com/"},
    {"role": "art, code", "name": "Asryto",
     "url": "https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design"},
]


def main():
    if not PACK.is_dir():
        sys.exit(f"pack not found: {PACK}")
    mf = PACK / "figure.json"
    d = json.loads(mf.read_text(encoding="utf-8"))

    # required by readManifest
    d["manifest"] = 2
    d["api"] = 2
    d["id"] = "gpt-atri"
    d["version"] = d.get("version", "1.0.0")
    d["name"] = NAME
    d["about"] = ABOUT
    d["entry"] = "figure.js"
    d["export"] = "createLayeredBody"
    d["model"] = "model.json"

    # cosmetic axes: ATRI ships one outfit, so both stay empty rather than being invented
    d["axes"] = []
    d["presets"] = []
    d["sounds"] = {}
    d["can"] = {"walk": True}

    # optional but wanted
    d["author"] = "Asryto"
    d["license"] = "AGPL-3.0-or-later"
    d["credits"] = CREDITS
    d["homepage"] = "https://github.com/scarlet20252025-cloud/Coopanion-Skin-Design"
    if "thumb" not in d:
        d["thumb"] = "tex/head-clean.png"

    # enforce the vocab contract here so a bad word cannot cost a whole-pack rejection later
    bad = []
    for w in d.get("vocab", []):
        wid = w.get("id")
        if not isinstance(wid, str) or not wid:
            bad.append((wid, "no id"))
        if w.get("kind") not in ("expression", "motion"):
            bad.append((wid, f"kind={w.get('kind')!r}"))
        names = w.get("names") or {}
        if not any(isinstance(v, list) and any(s.strip() for s in v) for v in names.values()):
            bad.append((wid, "no usable name"))
        sec = w.get("seconds")
        if not isinstance(sec, (int, float)) or isinstance(sec, bool) or sec <= 0:
            bad.append((wid, f"seconds={sec!r}"))
    if bad:
        sys.exit("vocab violates the manifest contract: " + repr(bad[:10]))

    # paths inside the pack: relative, no '..', no scheme
    for key in ("entry", "model", "thumb"):
        v = d.get(key, "")
        if v.startswith("/") or ".." in v.split("/"):
            sys.exit(f"{key} is not a pack-relative path: {v!r}")

    mf.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {mf.relative_to(ROOT)}")
    print(f"  id={d['id']}  version={d['version']}  name={d['name']['zh']}")
    print(f"  entry={d['entry']} export={d['export']} model={d['model']}")
    print(f"  axes={len(d['axes'])} presets={len(d['presets'])} sounds={len(d['sounds'])} "
          f"can={d['can']} vocab={len(d['vocab'])}")
    print(f"  about(zh) {len(ABOUT['zh'])} chars, about(en) {len(ABOUT['en'])} chars")


if __name__ == "__main__":
    main()
