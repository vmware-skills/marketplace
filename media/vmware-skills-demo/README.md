# Reproduce the bilingual demos

These Remotion sources generate the English/Chinese README GIFs and narrated introduction videos. The short demo and investigation scene use synthetic records and are continuously labeled as illustrative. No infrastructure API is contacted by rendering. Audio is AI-generated using Edge TTS preset voices (en-US-AriaNeural / zh-CN-XiaoxiaoNeural), not the maintainer's voice.

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
