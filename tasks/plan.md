# Implementation Plan: Chuck face voice sync

## Overview
Make the Chuck face visibly react to the actual TTS waveform, not merely display a `SPEAKING` label. Keep thinking visually distinct but still; only a fresh waveform may animate the mouth.

## Architecture decisions
- The existing signal bus remains authoritative: `/state` supplies state, envelope, and waveform data.
- Mouth aperture will derive from the current normalized waveform samples, with a small floor while speaking so it does not read as frozen between phonemes.
- Thinking must not use the speech-motion path. It may retain the existing amber indicator/ring state only.
- Correct the server-side envelope calculation for normalized `[-1, 1]` waveform data, then restart the running Python server so its loaded code matches the checked-out source.

## Tasks

### Task 1: Add waveform-driven mouth animation
- [ ] Calculate a smoothed mouth-open value from the live waveform.
- [ ] Apply it only in `speaking`; use the base mood path in all other states.
- [ ] Preserve blink and manual preview moods.

Acceptance criteria:
- [ ] A changing live waveform changes the mouth opening on screen.
- [ ] `thinking` does not move the mouth.
- [ ] A silent or stale waveform does not animate as speech.

### Task 2: Verify the live bridge
- [ ] Confirm `/state` reports a non-negligible envelope for normalized samples.
- [ ] Restart the visualizer server to run the corrected source.
- [ ] Capture the face in Chrome while the real bus reports speech.

Acceptance criteria:
- [ ] The browser labels the bus `LIVE` and shows `SPEAKING` only when the bus publishes a fresh waveform.
- [ ] The visible mouth/waveform react during speech.

## Risks
- The existing uncommitted Chuck styling changes belong to the current worktree and must remain intact.
- Browser screenshots are a point-in-time check; the `/state` samples and mouth transform provide the repeatable evidence.
