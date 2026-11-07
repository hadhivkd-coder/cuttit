---
name: before-after-reel
description: Make a before/after transformation reel (slider wipe, split screen, or flash cut) from two photos or two clips - renovations, fitness, design, haircuts, photo edits, cleaning. Use when the user has a "before" and "after".
---

# Before / After Reel

## Ask first
1. Before and after files. 2. Style: slider wipe (default), split screen, or beat-synced flash cut. 3. Labels/caption text.

## Steps
1. Align the two images: match size, then align with OpenCV ECC (`cv2.findTransformECC`, MOTION_AFFINE) so the wipe doesn't jump. Crop both to 9:16 on the same box.
2. Slider wipe: 1 s hold on "BEFORE", 2.5 s eased wipe with a white 6 px divider and a round handle, 1.5 s hold on "AFTER", then 1 s wipe back halfway (makes people rewatch).
3. Split screen: stack top/bottom with labels; for clips, sync them by length.
4. Flash cut: with music, alternate before/after on each beat for the last 3 s (librosa beat detection).
5. Encode 1080x1920, 30 fps.

## Rules
- Same crop and colour grade on both sides unless the edit itself is the point - say so on screen if the "after" is retouched.
