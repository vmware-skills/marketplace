# Reproduce the bilingual demos

These Remotion sources generate the English/Chinese README GIFs and narrated introduction videos. The short GIF uses synthetic records and is labeled illustrative. Introduction videos use separate English and Chinese historical capture excerpts. Chinese inventory/health/audit scenes come from the maintainer's Chinese screenshots; the two languages show different sessions, not a paired benchmark. Audit pages retain original table cells and omit the full target column. English shows 14 rows; Chinese selects 15 rows across AIops, Monitor, Harden and Aria. The audit screenshots are assistant-prepared summaries, not raw database views or completeness proofs. Captured names remain version-specific. Original PNGs stay local; sanitized native-resolution excerpts use lossless RGB encoding. Large text is explicitly labeled a readable transcript, not part of the original screenshot. Integer-scaled audit and health excerpts avoid smoothing; the final introduction uses CRF 16 to reduce text compression artifacts. Source pixels cannot recover details absent from the original. No infrastructure API is contacted by rendering. Audio is AI-generated using Edge TTS preset voices (en-US-AriaNeural / zh-CN-XiaoxiaoNeural), not the maintainer's voice.

Use Node.js 22+ and the committed package lock:

```sh
npm ci
npx remotion render src/index.tsx Demo-en ../../assets/demos/demo-en.mp4 --scale=0.5
npx remotion render src/index.tsx Demo-zh ../../assets/demos/demo-zh.mp4 --scale=0.5
npx remotion render src/index.tsx Intro-en ../../assets/demos/vmware-skills-en.mp4 --codec=h264
npx remotion render src/index.tsx Intro-zh ../../assets/demos/vmware-skills-zh.mp4 --codec=h264
```

Frame timing follows measured audio durations in src/scenes.json. Narration scripts and MP3 inputs are included. SRT captions are generated from the same scene timings. Component repositories link to the central assets instead of copying MP4 binaries.

The narrative follows the generic presentation structure: architecture, focused domains, evidence boundaries, workflows and local setup. Current code contracts supersede old slide tool counts, independent-approval claims and unverified compatibility claims. No customer-specific deck, endpoint, credential or live-environment identity is embedded.
