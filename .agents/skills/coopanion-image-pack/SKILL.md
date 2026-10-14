---
name: coopanion-image-pack
description: Create, modify, debug, validate, package or document Coopanion API 2 desktop companion image packs, using this repository's master-based source registration and animation workflow. Use for Coopanion image packs rather than ChatGPT Pets or Cubism exports.
---

# Coopanion image pack

Start at repository `AGENTS.md`, then [engineering quick start](../../../engineering/README.md) and [current-project.json](../../../engineering/current-project.json). Run `python engineering/tools/project.py doctor` and `check`. Read only the guide for the task; do not load all history.

- New character / source edit: [pipeline](../../../engineering/guides/pipeline.md), [parts and registration](../../../engineering/guides/parts-and-registration.md).
- Expression / motion / pose: [animation](../../../engineering/guides/animation-and-expression.md).
- Visible seam / wrong proportions: `project.py inspect <part>` and `case <id>`; inspect complete character and source ownership before changing masks.
- QA / native installation / release: [validation](../../../engineering/guides/validation-and-release.md).
- Promo video: [promo](../../../engineering/guides/promo.md), after the image pack baseline is fixed.

Current case coordinates belong to GPT Dragon's locked 1254px master. New characters need their own contract. Preserve uniform registration, semantic alpha, matching transform parents, and action-specific depth; a whole-image underpaint or old silhouette is not a universal repair. Ear/arm/hair depth, skirt/leg depth and ahoge scalp cleanup are separate problems.

Use existing official kit states and actual pack assets; don't recreate host movement or copy whale pixels. Keep continuous bangs until matching independent source art exists. Register and save local image edits, masks, prompt and input/output hashes.

Before declaring success, provide full-character and defect crops, light/dark backgrounds, both directions and relevant transitions. Machine checks, sampled visual review, user acceptance and native-host checks are different outcomes. Stop repeating a repair method after two demonstrated failures and diagnose the source again.

A task may authorize only editing. Installation, external upload, publication and old-pack cleanup depend on the user's actual scope. New trials can use `project.py candidate`, which writes to scratch and preserves production.
