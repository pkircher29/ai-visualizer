# Final C.H.U.C.K. Face — Implementation Plan

## Goal
Build a production-ready, state-reactive visualizer face that feels like Chuck: Paul's curious, candid, warm workshop collaborator. Supplied concepts are inspiration, not mandatory requirements.

## Acceptance criteria
- [ ] Preserve every prior prototype.
- [ ] Add a new `faces/chuck/` face rather than overwriting Yardmind.
- [ ] Use a stable, hand-authored face rig; no generative frame morphing.
- [ ] Animate idle, listening, thinking, speaking, and alert states from the real visualizer bus.
- [ ] Support preview overrides for the broader expression vocabulary.
- [ ] Keep the face mature, friendly, inquisitive, and capable of respectful disagreement.
- [ ] Use only truthful live labels; no fabricated metrics or fake work status.
- [ ] Keep thinking sound disabled.
- [ ] Verify JavaScript syntax, HTTP serving, asset loading, and real browser rendering.
- [ ] Make the new face the configured default only after verification.

## Build sequence
1. Freeze the chosen visual identity in `DESIGN.md`.
2. Copy the selected workshop character artwork into the face's local assets.
3. Implement the stable face overlay and expression grammar.
4. Add restrained workshop motion: state color, signal ring, sparks, modules, waveform, and ticker.
5. Wire AV state and voice envelope.
6. Render and visually inspect every primary state.
7. Correct alignment, expression, and readability defects.
8. Set the verified face as default.
