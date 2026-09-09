# Historical engineering record: ARCI Enclosure Rev3 reconstruction

> **Archive notice:** This document preserves development measurements and decisions from the reconstruction effort. It is not the current release guide or a statement of the current Fusion master state. Names, version numbers, open issues, and next actions below may be historical. Use the supported [Fusion rebuild guide](../development/fusion-rebuild.md), [release workflow](../development/fusion-release-workflow.md), and the root [README](../../README.md) for current instructions.

Last updated: 2026-09-02

## Goal

Reconstruct both halves of the ARCI enclosure in **ARCI Enclosure Rev3** as a clean, native, performant Fusion 360 design while retaining the dimensions, appearance, control layout, connector layout, and mating behavior of the supplied reference files and the legacy `Radio Enclosure Front - Proto v66` design.

Reference files:

- `Front_Half.step`
- `Back.step`
- `Front.dxf`

The finished design must:

- Match the existing front and back enclosure geometry and dimensions.
- Reproduce the original front/back snap fit and intentional preload.
- Use named user parameters for design-driving dimensions.
- Use small, purpose-specific, fully constrained sketches.
- Keep panel geometry, labels, and lip/notch geometry separate.
- Use model features and feature patterns instead of duplicating large amounts of sketch geometry.
- Remain responsive and straightforward to modify downstream.

## Current Fusion Document

- Active master: `ARCI Enclosure Rev3 v1`. It contains identity-positioned `FRONT_HALF` and `BACK_HALF` components rebuilt natively with +X right, +Z up, and no body-level orientation transform.
- Legacy functional comparison source: `Radio Enclosure Front - Proto v66`. Use this document—not Rev2—as the authority when evaluating which original internal features must be retained.
- Historical mechanical checkpoint: `ARCI Enclosure Rev2 v16`. Do not use it as the functional comparison baseline for missing internal features and do not save over it.
- Orientation proof of concept: one unsaved `Untitled` assembly containing Rev2 as a linked occurrence with a rigid 180° Y-axis transform. It validates the required global transform but is **not** the intended final solution.
- Historical print-preparation checkpoint: `ARCI Enclosure Rev2 - AMS Print Prep v1` (saved and clean). It is no longer part of the maintained workflow and does not need to be synchronized with the master.
- Do not intentionally modify the legacy `Radio Enclosure Front - Proto v66` document.

### V3 internal-support update

- Compared the interior directly with `Radio Enclosure Front - Proto v66`; Rev2 was not used as the missing-feature authority.
- Recreated the five rotary/control support collars in `FRONT_HALF` as three small, purpose-specific parametric sketches and three joined model features.
- The standard collar group reproduces the MULTI, TUNE, and two right-side control collars. The AF/RF collar is modeled separately because it has a deeper stepped bore.
- Added named parameters for all collar outside diameters, through diameters, standard/deep collar lengths, AF/RF counterbore diameter, and AF/RF counterbore depth.
- Grouped the new timeline items as `FRONT HALF - CONTROL SUPPORT COLLARS`.
- Solid-volume cross-check: the five measured annular features total `3,526.6759 mm³`, agreeing within approximately `0.026 mm³` with the `3,526.650 mm³` original-material deficit identified by the earlier Boolean comparison.
- The v66 main front body has no rear guide tunnels extending the rectangular pushbutton openings beyond the 3 mm front wall. None were invented in V3.
- Display mounting/support geometry was added later as the Waveshare carrier (audited 2026-09-02).

### Root-level sketch audit

The three root-level sketches are orientation-remediation point sets, not production profiles:

| Sketch | Contents | Assessment |
| --- | ---: | --- |
| `SK_CANONICAL_DATUM_POINTS` | 5 points; 0 curves, text, or profiles | Retain for now as the canonical orientation datum/reference. |
| `SK_TEST_FRONT_BASIS` | 1 point; 0 curves, text, or profiles | Temporary orientation diagnostic; candidate for later cleanup after a dependency check. |
| `SK_TEST_REAR_BASIS` | 1 point; 0 curves, text, or profiles | Temporary orientation diagnostic; candidate for later cleanup after a dependency check. |

These point-only sketches can appear empty in the canvas and do not materially affect Fusion performance. No sketch was deleted during this audit.

## Orientation Standard

- Canonical front inspection is from negative Y toward positive Y, with **+X to the viewer's right** and **+Z upward**. Fusion's named Front view alone is not sufficient evidence because its camera roll can conceal an axis inversion.
- Positive Y runs from the exterior front face toward the rear of the enclosure.
- The panel datum/origin remains centered.
- Design-driving X and Z values are documented in this canonical front coordinate system.
- The current Rev2 source is globally inverted in X and Z: physical top features such as `POWER` and `SHIFT` are at negative Z, while `F1`–`F6` are at positive Z. Most front/rear face sketches use local X = model +X and local Y = model -Z.
- The required source-to-canonical mapping is the rigid transform `(X, Y, Z) -> (-X, Y, -Z)`, equivalent to a 180° rotation about the depth/Y axis.
- A handedness-changing body mirror is prohibited because it can silently invalidate mating geometry and left/right control placement.

## Ground-Up Orientation Remediation Plan

The final correction must be native to the driving sketches and datums. A linked wrapper, imported solid, body move, or end-of-timeline orientation feature is not an acceptable final master.

### Phase 1 — Freeze and measure the baseline

- Preserve Rev2 v16 as the source checkpoint and do not modify the legacy prototype.
- Record all user parameters, shell volumes/faces, bounding boxes, feature health, sketch constraint state, thread metadata, label strings, and inlay body counts.
- Preserve the verified 254 × 130 mm envelope, 5.96 mm overlap, approximately 8.572 mm³ twelve-zone latch preload, and exact prototype corner topology.
- Record semantic orientation checks: `POWER`/`SHIFT` must finish at positive Z, `F1`–`F6` at negative Z, front-left controls at negative X, and front-right controls at positive X.

#### Captured Rev2 v16 baseline

| Item | Baseline |
| --- | ---: |
| User parameters | 131 |
| Timeline items | 100 |
| Native sketches | 32 |
| Features | 60 |
| Root bodies | 123 |
| Fully constrained sketches | 22 / 32 |
| Unhealthy sketches/features | 0 / 0 |
| Front AMS inlay bodies | 105 |
| Back AMS inlay bodies | 16 |
| `FRONT_SHELL` volume | 140,101.421409 mm³ |
| `FRONT_SHELL` faces | 2,079 |
| `BACK_SHELL` volume | 197,136.051275 mm³ |
| `BACK_SHELL` faces | 519 |

- Core front bounds before any presentation transform: X `[-127, 127]`, Y `[0, 30]`, Z `[-65, 65]` mm.
- Core back bounds before presentation transforms: X `[-127, 127]`, Y `[24.04, 54.04]`, Z `[-65, 65]` mm.
- Final timeline items `Move1` and `Move2` each translate selected back geometry +10 mm in Y for separated presentation, producing displayed back bounds Y `[34.04, 64.04]`. They are not part of the mating geometry and must not be reproduced in the corrected master.
- The native source has 26 XZ face sketches using local X = model +X and local Y = model -Z, plus six notch/detent sketches on orthogonal planes, nine custom construction planes, five rectangular patterns, and two mirrors.

#### Canonical unsaved rebuild validation

| Item | Corrected result |
| --- | ---: |
| Timeline items | 18 (including four audited notch-crown fillets) |
| Front sketches / features | 20 / 27 |
| Back sketches / features | 14 / 21 |
| Unhealthy sketches/features | 0 / 0 |
| Front native text / inlay bodies | 31 / 105 |
| Back native text / inlay bodies | 4 / 16 |
| `FRONT_SHELL` volume before crown fillets | 140,192.557173 mm³ |
| `FRONT_SHELL` volume after crown fillets | 140,193.252874 mm³ |
| `BACK_SHELL` volume | 197,136.065508 mm³ |
| Corrected front/back latch interference | 8.411265699 mm³ across the same twelve zones |

- Both shells retain the exact 254 × 130 mm envelope and canonical bounds: front Y `[0, 30]` mm; back Y `[24.04, 54.04]` mm.
- The back shell differs from the baseline by only `0.014233 mm³`. The front differs by `91.831465 mm³` (`0.0655%`), mainly in simplified front feature construction; no dimensions were intentionally changed.
- The corrected latch interference is `0.161142 mm³` (`1.88%`) below the original 8.572407 mm³ target. The original 45° taper, nominal depths, and R0.4 crown dimensions are retained; do not tune source dimensions merely to force the aggregate Boolean number.
- Fusion standard Front and Back screenshots confirm upright exterior text. Front labels retain `NTCH`, `WIDTH`, and `AF/RF`; rear labels are horizontal, upright, centered on connector X coordinates, and above the openings.
- The 15 pilot cylinders carry one full-length cosmetic ISO M3×0.5 6H thread feature. Helical thread geometry is intentionally not modeled.

### Phase 2 — Establish canonical datums

- Create explicit, named, oriented datum planes for front exterior, rear exterior, top, bottom, left, and right.
- Verify each datum's origin, local X direction, local Y direction, and normal numerically before drawing geometry.
- Front-facing sketches must edit naturally with local right/up corresponding to model +X/+Z. Rear-facing label sketches must edit naturally when viewed from the rear exterior, without corrective text mirroring.
- Keep all enclosure geometry in identity-positioned `FRONT_HALF` and `BACK_HALF` components sharing the same global user parameters.

### Phase 3 — Rebuild the front in canonical coordinates

- Recreate the symmetric outer shell, cavity, lip, relief, and corner treatment from the existing parameter expressions.
- Transform and recreate the display, button, rotary, recess, mounting-boss, pilot-hole, and notch seed sketches using one audited coordinate conversion at the source boundary.
- Recreate pattern and mirror directions explicitly in canonical axes; do not assume a corrected seed automatically fixes a root-axis pattern.
- Recreate the M3×0.5 6H cosmetic thread feature after the pilot-hole geometry is healthy.
- Recreate `SK_LABELS` as upright native text in the corrected front datum, preserving all strings, centers, height parameters, `WIDTH`/`AF / RF` placement, and `NTCH` correction.
- Generate the front deboss and 105 AMS inlay bodies from the corrected native text sketch.

### Phase 4 — Rebuild the back in canonical coordinates

- Recreate the back shell, groove, cavity, connector cutouts, connector recesses, and prototype-matched corner treatment.
- Transform all top/bottom and left/right detent seed positions and verify their extrusion/taper directions in the canonical frame.
- Recreate the four rear labels as upright native text centered on their connector centerlines and above the openings in global +Z.
- Generate the rear deboss and 16 AMS inlay bodies from `SK_BACK_LABELS_NATIVE`.

### Phase 5 — Parametric and geometric validation

- Require every design-driving mechanical sketch to be fully constrained; document intentional non-driving text placement frames separately.
- Confirm zero unhealthy sketches/features and a successful full compute with all timeline items active.
- Exercise width and height parameters away from nominal and restore them, confirming that shells, lip, notches, detents, corner treatment, and labels rebuild predictably.
- Compare the corrected solids against the supplied STEP/DXF references after applying only the documented source alignment.
- Re-run front/back interference analysis and preserve the twelve localized preload zones.
- Confirm front and rear text readability from their respective exterior views, 0.6 mm deboss depth, and exact black/white interface alignment.
- Keep print features grouped and normally suppressed so everyday editing remains responsive.

### Phase 6 — Promotion

- Present the corrected design unsaved for visual inspection with a camera explicitly set to +X right/+Z up.
- Save and promote the corrected document only after explicit approval.
- Archive or discard the linked-wrapper experiment and retire Rev2 only after the corrected master passes every validation gate.

## Reference Geometry Verified

### Overall enclosure

| Item | Value |
| --- | ---: |
| Width | 254 mm |
| Height | 130 mm |
| Front-half depth | 30 mm |
| Outer corner radius | 1.9 mm |
| Back-half start along depth | 24.04 mm |
| Front/back overlap | 5.96 mm |

### Display

Coordinates below are relative to the panel center.

| Item | Value |
| --- | ---: |
| Display center X | -18.5246 mm |
| Display center Z | 11.7106 mm |
| Front opening | 114.42 × 66.38 mm |
| Through aperture | 110.32 × 62.28 mm |
| Bevel depth | 2.05 mm |
| Bevel angle | 45° |

#### Dual-display integration audit (Sunton + Waveshare)

- The rolled-back `Radio Enclosure Front - Proto v68` state was inspected without saving or moving its timeline marker. The original Sunton mechanical model is `5Inch_LCD_Model v1:2`, not the later generic `5" LCD IPS Display v7:1` occurrence.
- Measured Sunton interface: 120.7 × 75.7 mm front glass, 110.0 × 66.0 mm active area, 136.7 × 84.0 mm PCB, four approximately Ø3.1 mm through-holes on a 129.7 × 76.8 mm pitch, and approximately 5.5 mm from the glass face to the PCB mounting plane.
- Measured Waveshare `5-DSI-TOUCH-A` interface and checked it against the Waveshare drawing: 129.0 × 72.8 mm front package with R4 corners, 110.32 × 62.28 mm active area, 5.6 mm front-package depth, and eight M2.5 rear threads. The symmetric outer four are on a 117 × 61 mm pitch; the offset inner four are the 58 × 49 mm Raspberry Pi pattern and should remain available for the Pi rather than being consumed by the enclosure mount.
- The currently linked Waveshare occurrence is only positioned for visual reference. Its front surface is about 10 mm behind the enclosure front, and no Waveshare seating pocket, gasket ledge, retainer, or mounting adapter exists yet.
- The former 121.1 × 76.2 mm through-aperture was the old Sunton glass-clearance opening. It cleared the 120.7 × 75.7 mm Sunton glass by roughly 0.2/0.25 mm per side, but was 3.4 mm taller than the 72.8 mm Waveshare glass and therefore could not neatly frame the Waveshare package.
- A single close-fitting full-glass pass-through cannot serve both displays because the Sunton is narrower/taller while the Waveshare is wider/shorter. The clean master-model solution is two display configurations driven from the same display datum and shell: `SUNTON` retains the original glass clearance and direct four-boss mount; `WAVESHARE` uses an active-area window, rear glass pocket, compliant gasket, and a removable retainer/adapter using the Waveshare outer four M2.5 threads.
- If one physically identical printed front shell must accept either display, use a common approximately 110.7 × 66.4 mm viewing window plus a rear pocket sized for the union envelope (approximately 129.5 × 76.2 mm with printing clearance) and separate Sunton/Waveshare locating-retainer parts. This exposes about 2.1 mm of inactive black glass above and below the Waveshare active area but safely retains both glass envelopes.
- The Waveshare active-area reference is centered at X = -18.5246 mm, Z = 11.7106 mm. `SK_FRONT_DISPLAY_BEVEL` and `SK_FRONT_DISPLAY_APERTURE` are now fully constrained and genuinely driven by the `disp*` parameters; the previous fixed rectangles ignored parameter-table edits. Add separate named parameters for glass envelope, mount pitch, face recess, pocket clearance, gasket compression, and adapter thickness when the mounting pocket and retainer are implemented.

### Button layout

- Button profile: 10 × 5 mm with 0.5 mm corner radius.
- Top row: six buttons, first center `(-62.65, -46.35)`, 18 mm X pitch.
- Left grid: 2 × 4, first center `(-113, 0.66)`, 15 mm X pitch and 12 mm Z pitch.
- Extra left button center: `(-98, 48.66)`.
- Right grid: 3 × 4, first center `(61.5, 3.66)`, 15 mm X pitch and 12 mm Z pitch.

### Circular controls

| Center X, Z (mm) | Through diameter | Recess diameter |
| --- | ---: | ---: |
| `(-106, -46)` | 15.8 mm | 19 mm |
| `(-106, -22)` | 8.4 mm | 15 mm |
| `(76.519, -33.6)` | 8.85 mm | 16 mm |
| `(113, 2.9983)` | 6.8 mm | 14.6 mm |
| `(113, 39.9983)` | 6.8 mm | 14.6 mm |
| `(-108.9894, 52.1731)` | 3.5 mm | None |

### Mating lip and notches

- Lip outer boundary: 250 × 126 mm.
- Lip inner boundary: 246 × 122 mm.
- Lip ring width: 2 mm.
- Lip begins at depth 24.04 mm.
- Notch taper spans depth 26–28 mm and peaks at 27 mm.
- Twelve notches total: three per edge.
- Top/bottom notch centers X: `-100`, `0.5`, `101` mm.
- Left/right notch centers Z: `-38`, `0`, `38` mm.
- Nominal notch width: 10 mm.
- Top/bottom peak depth: 0.8343 mm.
- Left/right peak depth: 0.7929 mm.

### Back half

| Item | Value |
| --- | ---: |
| Back envelope | 254 × 130 × 30 mm |
| Front-most Y coordinate | 24.04 mm |
| Rear exterior Y coordinate | 54.04 mm |
| Main rear-wall thickness | 4 mm |
| First mating opening | 250 × 126 mm |
| Main cavity opening | 246 × 122 mm |
| Mating-groove depth | 6.10 mm |
| Rear edge radius | 1.9 mm |
| Back snap detents | 12 total, three per wall |
| Detent base | 10 × 2 mm, 45° taper |
| Detent crown | R0.4 mm, 0.8343 mm peak projection |
| Rear label height | 4 mm |
| Rear AMS inlay depth | Shared `labelDepth = 0.6 mm` |

The rear connector interface reproduces the WIFI circular port and counterbore, USB opening and recess, exact DB9 aperture with its two screw holes and inner/outer recesses, COM 0 opening, end circular connector and counterbore, plus the four 6 mm panel holes.

## Fusion Sketch Structure

| Sketch | Purpose | Status |
| --- | --- | --- |
| `SK_PANEL_PROFILE` | Centered outer panel master | Complete; fully constrained |
| `SK_DISPLAY_OPENING` | Front display opening | Complete; fully constrained |
| `SK_DISPLAY_APERTURE` | Smaller through aperture | Complete; fully constrained; normally hidden |
| `SK_BUTTON_MASTERS` | Four seed profiles for later feature patterns | Complete; fully constrained |
| `SK_ROTARY_THROUGH` | Six circular through-cut profiles | Complete; fully constrained |
| `SK_ROTARY_RECESSES` | Five counterbore/recess profiles | Complete; fully constrained |
| `SK_LABELS` | 31 native editable front-panel labels | Complete; native text with parameterized height |
| `SK_LIP_BASE` | Outer and inner mating-lip boundaries | Complete; fully constrained |
| `SK_INNER_CAVITY` | Independent front-thickness and side-wall cavity | Complete; fully constrained |
| `SK_LIP_RELIEF` | Rear perimeter relief that leaves the mating lip | Complete; fully constrained |
| `SK_LIP_NOTCH_TB_BASE` | 10 × 2 mm top/bottom tapered-pocket seed | Complete; fully constrained |
| `SK_LIP_NOTCH_LR_BASE` | 10 × 2 mm left/right tapered-pocket seed | Complete; fully constrained |
| `SK_MOUNT_BOSSES_SHORT` | Eleven short internal mounting-boss profiles | Complete; fully constrained |
| `SK_MOUNT_BOSSES_TALL` | Four tall encoder-board mounting-boss profiles | Complete; fully constrained |
| `SK_MOUNT_PILOTS_STANDARD` | Six linked standard blind M3 pilot profiles | Complete; fully constrained; projected from boss centers |
| `SK_MOUNT_PILOT_POWER` | Linked left-power blind M3 pilot profile | Complete; fully constrained; projected from boss center |
| `SK_MOUNT_PILOTS_FKEY` | Four linked function-key blind M3 pilot profiles | Complete; fully constrained; projected from boss centers |
| `SK_MOUNT_PILOTS_ENCODER` | Four linked encoder-board blind M3 pilot profiles | Complete; fully constrained; projected from boss centers |
| `SK_BACK_OUTER_PROFILE` | Centered back envelope | Complete; fully constrained; driven by `backWidth` and `backHeight` |
| `SK_BACK_GROOVE_OPENING` | First-stage 250 × 126 mm mating opening | Complete; fully constrained; parameter driven |
| `SK_BACK_MAIN_CAVITY` | Main 246 × 122 mm cavity | Complete; fully constrained; parameter driven |
| `SK_BACK_PORTS_THROUGH` | WIFI, USB, DB9, COM 0, end connector, and panel through-holes | Complete; locked connector-reference geometry |
| `SK_BACK_PORT_RECESSES` | WIFI counterbore | Complete; locked connector-reference geometry |
| `SK_BACK_USB_RECESS` | USB exterior relief | Complete; locked connector-reference geometry |
| `SK_BACK_END_CONNECTOR_RECESS` | End-connector counterbore | Complete; locked connector-reference geometry |
| `SK_BACK_DB9_OUTER_RECESS` | DB9 exterior rounded recess | Complete; locked connector-reference geometry |
| `SK_BACK_DB9_INNER_RECESS` | DB9 interior rounded recess | Complete; locked connector-reference geometry |
| `SK_BACK_DETENTS_TOP` | Three top snap-detent bases | Complete; locked verified mating geometry |
| `SK_BACK_DETENTS_BOTTOM` | Three bottom snap-detent bases | Complete; locked verified mating geometry |
| `SK_BACK_DETENTS_RIGHT` | Three right snap-detent bases | Complete; locked verified mating geometry |
| `SK_BACK_DETENTS_LEFT` | Three left snap-detent bases | Complete; locked verified mating geometry |
| `SK_BACK_LABELS_NATIVE` | WIFI, USB, RS232, and COM 0 native rear text | Complete; separate editable text sketch |

The button and notch sketches intentionally contain only master profiles. Repetitions should be model-feature patterns rather than sketch patterns to keep regeneration fast.

## Completed

- Inspected `Front_Half.step`, `Back.step`, and `Front.dxf`.
- Measured the overall panel, display, controls, lip, overlap, and notch layout.
- Added or corrected design-driving user parameters in Rev2.
- Created the separate, fully constrained mechanical master sketches listed above.
- Separated through holes from larger front recesses.
- Separated the mating lip and notch seeds from the front-panel sketches.
- Kept labels in their own dedicated sketch.
- Reconstructed 31 semantic labels as native Fusion text instead of retaining 699 DXF outline splines.
- Created the 254 × 130 × 30 mm `Front_Rebuild` base body.
- Applied the 1.9 mm outer corner fillets as model features.
- Created the inner cavity with independent 3 mm front thickness and 4 mm wall thickness.
- Cut the Waveshare active-area aperture at 110.32 × 62.28 mm and retained the parameter-driven 2.05 mm, 45° bevel, producing a 114.42 × 66.38 mm front opening.
- Created all 27 rounded button openings from four seeds and three rectangular model patterns.
- Created the six circular through-holes in one grouped feature.
- Re-measured and created the five front recesses: 19 mm and 16 mm at 2 mm depth; 15 mm and 14.6 mm at 1.5 mm depth.
- Created the 5.96 mm rear perimeter relief, leaving the verified 250 × 126 mm outer lip boundary.
- Reconstructed all twelve mating notches as 45° tapered pockets with true full-round crowns.
- Patterned three notches per edge and mirrored the two seed families to the opposing edges.
- Validated the generated crown radii against the STEP: approximately 0.400035 mm top/bottom and 0.499984 mm left/right.
- Validated the completed lip against `Back.step` using Fusion interference analysis.
- Original `Front_Half.step`/`Back.step` interference: 8.572407 mm³.
- Rev2/`Back.step` interference: 8.572355 mm³.
- Difference: 0.000052 mm³, confined to the same twelve-notch envelope; this confirms intentional mating preload rather than an accidental collision.
- An earlier orientation review relied on Fusion's named Front view and incorrectly concluded the global axes were corrected. The later model-space audit supersedes that conclusion.
- Confirmed that the required correction is a rigid 180° orientation change about the depth/Y axis, not a geometric mirror.
- Verified the transform in an unsaved linked-occurrence proof of concept: `POWER` and `SHIFT` move to positive Z, `F1`–`F6` to negative Z, and the rear labels become 12.81 mm above their connector centers.
- Added `labelDepth = 0.6 mm` and `labelInlayRecess = 0 mm` manufacturing parameters.
- Calibrated all 31 native front labels against `Radio Enclosure Front - Proto v66`. Although v66 reports a nominal 2.8 mm text height, its evaluated `POWER`, `TUNE`, and `SHIFT` bounds are approximately 14.86 × 2.95, 10.93 × 2.85, and 11.83 × 2.91 mm. Current-engine Arial at `frontLabelHeight = 4 mm` reproduces those bounds closely and is more reliable with a 0.4 mm nozzle.
- Restored the v66 display spacing in `AF / RF`, `A / B`, `BND +`, and `BND –` while retaining the corrected `NTCH` string and every existing semantic label center.
- Added the single grouped `FT_LABEL_DEBOSS_CUT` feature at the end of the master timeline; it remains suppressed during normal mechanical editing.
- Added `FT_AMS_WHITE_TEXT_INLAY` directly after the deboss feature in the mechanical master. It creates 105 named white glyph bodies from the same 31 native `SK_LABELS` text objects and remains suppressed during normal editing.
- Corrected the legacy label content from `INT CH1` to `NTCH` and audited all 31 label strings.
- Corrected `WIDTH` and `AF / RF` to the original right-side stack: `WIDTH` frame center at local sketch `(-113, 27.5983)` mm and `AF / RF` at `(-113, 16.4445)` mm.
- Created an isolated AMS print-preparation design with `BLACK_FRONT` and `WHITE_TEXT_INLAY` components, oriented upright in the named Front view.
- Added parametric `FT_AMS_BLACK_LABEL_CUT` and `FT_AMS_WHITE_TEXT_INLAY` features in print prep; both are driven by the shared `labelDepth`, `labelTextHeight`, and `labelInlayRecess` parameters.
- Generated 105 disconnected white glyph solids from the same 31 native text definitions used for the black cavities.
- Validated AMS material replacement: black volume 136,025.007192 mm³ plus white volume 237.935212 mm³ equals 136,262.942403 mm³, differing from the unlettered master by only 0.00000035 mm³.
- Parameter-change validation passed: changing `labelDepth` from 0.6 to 0.8 mm updated both black and white features without warnings while preserving the same combined solid volume; the value was restored to 0.6 mm.
- Consolidated the final AMS workflow into the mechanical master so enclosure and label changes have one source of truth. The separate print-preparation design is retained only as a historical recovery checkpoint.
- Revalidated the consolidated master with both print features enabled: 106 bodies total, 2,011 faces on `Front_Rebuild`, black volume 136,025.007192 mm³, 105 white bodies totaling 237.935212 mm³, and combined volume 136,262.942403 mm³.
- Suppressed both print features after their initial validation. Before internal mounts were added, the normal editing state was one body with 320 faces and volume 136,262.942403 mm³.
- Organized the two print-only features in the collapsed timeline group `PRINT - AMS LABELS`.
- Renamed all 105 generated inlay bodies semantically by label, character order, and character, for example `INLAY_F1_01_F`, `INLAY_BND_MINUS_04_MINUS`, and `INLAY_AF_SLASH_RF_03_SLASH`. The naming operation does not move or alter the geometry.
- Reconstructed all 15 original internal mounting bosses using the fully constrained short- and tall-boss sketches, with linked pilot sketches separated by blind-hole depth family.
- Added named parameters for the 6.4, 6.5, 7.0, and 7.5 mm boss diameters; 8.2 and 11.04 mm boss heights; 2.529 mm tap-drill diameter; and the four retained blind-hole base thicknesses.
- Reproduced the original lightweight thread specification as one grouped cosmetic thread feature: ISO metric M3×0.5, class 6H, right-handed, full hole length, and not physically modeled.
- Organized the six mounting sketches, six boss/pilot features, and thread feature in `MOUNTING - INTERNAL BOSSES + M3 THREADS` immediately before the print-only group.
- Validated all 15 centers, outside radii, heights, tap-drill radii, and blind-hole depths against `Radio Enclosure Front - Proto v65`: maximum measured deviation 0.000000 mm.
- Validated the net boss material addition: expected 4,678.227021542 mm³ and generated 4,678.227021542 mm³, with 0.000000000 mm³ difference.
- Reconstructed the back as the independently named `BACK_SHELL` body in the same Fusion Part document, avoiding an externally linked print or assembly document.
- Created the fully constrained, parameter-driven outer, groove, and main-cavity sketches. A live rebuild test changed `backWidth` from 254 to 255 mm and back to 254 mm with no feature warnings and the body envelope followed exactly.
- Recreated the two-stage 2 mm/4 mm mating wall, 4 mm rear wall, 1.9 mm outer/rear fillets, and the complete rear connector interface from `Back.step`.
- Recreated all twelve rear snap detents from four small seed sketches using 45° tapered extrusions and R0.4 crowns, then joined only those tool bodies to `BACK_SHELL` so the front body cannot be accidentally merged.
- Validated the new native front/back interference at 8.571944823 mm³ across 12 latch zones. The original STEP pair measures 8.572407877 mm³, a difference of only 0.000463054 mm³ (0.0054%).
- Added native 4 mm rear labels (`WIFI`, `USB`, `RS232`, and `COM 0`) in the separate `SK_BACK_LABELS_NATIVE` sketch.
- Implemented the rear labels with the same AMS workflow as the front: `FT_BACK_LABEL_DEBOSS_CUT` and `FT_BACK_AMS_WHITE_TEXT_INLAY`, sharing `labelDepth` and `labelInlayRecess`.
- Generated and semantically named 16 aligned rear inlay bodies (`INLAY_BACK_*`) and applied the validated `ABS (White)` front-inlay appearance.
- Validated the rear material interface at both 0.6 and 0.8 mm label depth. Black plus white combined volume remained exactly 197,171.517950408 mm³, and the parameter was restored to 0.6 mm.
- Organized the back mechanics and print-only features in the collapsed timeline groups `BACK HALF - PARAMETRIC REBUILD` and `PRINT - AMS BACK LABELS`.
- Preserved the reusable native rebuild script at `Back_Parametric_Rebuild.py` in the project workspace.
- Compared the exposed perimeter treatment directly against `Radio Enclosure Front - Proto v66`. The prototype uses matching R1.9 mm edge fillets on the front exterior at Y=0 and the back exterior at Y=54.04; Rev2 previously had the back fillet but left the front perimeter sharp.
- Replaced the sequential outer-corner and exposed-face fillets with one eight-edge setback feature per half: `FT_FRONT_COMBINED_SETBACK_FILLET` and `FT_BACK_COMBINED_SETBACK_FILLET`. Each combines the four depth-parallel corners with the four exposed-face perimeter edges, matching the construction order used by prototype `Fillet1` and `Fillet2`.
- Set both combined features to `isRollingBallCorner = false` and drove them from the shared `outerCornerR = 1.9 mm`; `backCornerRadius` is linked to `outerCornerR` so the halves cannot drift apart.
- Verified exact prototype corner topology on both halves: setback NURBS patch extents 3.799713078 × 3.799713078 × 3.799713078 mm and area 22.851383850 mm². The adjoining R1.9 cylindrical runs also match the prototype bounding extents and face areas.
- Linked `backWidth = caseWidth`, `backHeight = caseHeight`, and derived the 250/246 mm back openings from those shared dimensions. A regeneration test changed `caseWidth` from 254 to 255 mm: both bodies became exactly 255 mm wide, both setback patches remained numerically unchanged and healthy, and no feature reported a warning. `caseWidth` was restored to 254 mm.

## Functional Parity Status

Rev3 now contains native front and back enclosure halves with the original snap-fit behavior. Against the main front body in `Radio Enclosure Front - Proto v66`, the previously missing non-display support geometry has been accounted for by the five recreated rotary/control collars. Display mounting/support hardware remains deliberately deferred.

### Reconstructed and validated

- Overall enclosure envelope, wall depth, front thickness, and external corner radii.
- Display opening and bevel.
- Button openings, circular control holes, and front recesses.
- Mating lip, all twelve notches, and the original front/back preload behavior.
- Front-view geometry and handedness match the source after applying the audited rigid transform, but the native Rev2 sketch/global-axis orientation remains to be rebuilt.
- All 31 label strings and placements as separate, editable native sketch text.
- All 15 internal component-mounting bosses, blind pilot holes, and original M3×0.5 6H thread metadata.
- Five rear rotary/control support collars, including the stepped AF/RF collar, as parameter-driven joined features.
- Clean parametric organization using small constrained sketches and model-feature patterns.
- Complete native back shell, rear connector openings/recesses, rear edge treatment, and twelve-detent mating system.
- Rear labels using the same black-deboss/white-AMS-inlay manufacturing interface as the front.
- Rear legends read upright in the normal exterior rear view and are centered on the `WIFI`, `USB`, `RS232`, and `COM 0` connector centerlines. They remain above the openings so attached cables are less likely to obscure them.

### Not yet functionally reproduced

- Internal display mounting/support features: the Waveshare carrier, glass pocket and enclosure posts now exist and are audited (see the 2026-09-02 carrier section); constrained-sketch cleanup of the script-generated feet/knob sketches is still open.
- Any supports belonging to separate legacy components rather than the v66 main front body will be evaluated when those components are brought into V3.

The v66 main front body was checked for the previously suspected button-guide tunnels, local ribs, and pads. The rectangular button apertures terminate at the front wall and no additional main-body guide tunnels were found, so V3 intentionally does not add speculative geometry.

### Label manufacturing workflow

- The enclosure is printed in PLA on a Bambu Lab A1 with AMS Lite; the white lettering is produced during the print rather than filled manually afterward.
- The legacy main front body has 105 planar glyph-floor faces at 0.5 mm behind the outer front surface, confirming a 0.5 mm deboss depth.
- The legacy Fusion document also contains dozens of permanently active white glyph bodies. These materially contribute to its browser and regeneration complexity.
- Rev2 keeps the same manufacturing capability in the mechanical master using two normally suppressed, adjacent parametric features: `FT_LABEL_DEBOSS_CUT` and `FT_AMS_WHITE_TEXT_INLAY`.
- Both features are generated from the same native `SK_LABELS` text and use `frontLabelHeight = 4.0 mm`, `labelDepth = 0.6 mm`, and `labelInlayRecess = 0 mm`. The deboss and inlay therefore retain one aligned text source without document synchronization.
- Normal editing workflow: keep both print features suppressed. With the internal bosses present, this leaves one body with 380 faces and avoids the everyday cost of the 105 glyph bodies.
- The collapsed `PRINT - AMS LABELS` timeline group contains both features. Expand it only when editing or preparing an AMS export.
- The rear uses the equivalent adjacent features in `PRINT - AMS BACK LABELS`, with 16 `INLAY_BACK_*` bodies. Both front and back share `labelDepth` and `labelInlayRecess`. Rear orientation and centering are defined in `SK_BACK_LABELS_NATIVE`; the deboss and inlay features consume that same sketch without corrective downstream moves.
- AMS export workflow: enable the applicable front/back print groups, export each black enclosure body with its aligned `INLAY_*` bodies as multipart 3MF, assign black and white AMS filaments in Bambu Studio, then suppress the print groups again for normal editing.
- The saved `ARCI Enclosure Rev2 - AMS Print Prep v1` document is historical only. It may be kept, archived, or closed without affecting the maintained Rev2 design.

### V3/V4 front-label match to prototype v66

- The front sketch `SK_FRONT_LABELS_NATIVE` uses native Arial Bold text. The 28 general labels are driven by `frontLabelHeight = 4 mm`; the four compact dual-encoder legends use `encoderLegendHeight = 3 mm`. Prototype v66 was verified to use `TextStyleBold`; regular Arial was the cause of V3's thin strokes.
- The current Fusion text engine produces smaller evaluated glyphs than the legacy v66 engine at the same nominal height. A 4 mm V3 height was therefore chosen from measured geometry, not from the legacy 2.8 mm nominal value.
- Calibrated current-engine bold bounds are: `POWER` 14.798828 x 2.960938 mm, `TUNE` 10.603515 x 2.912109 mm, and `SHIFT` 11.328125 x 2.962891 mm. The respective v66 references are 14.856507 x 2.949279 mm, 10.930696 x 2.847749 mm, and 11.829717 x 2.910702 mm.
- Legacy spacing was restored in `AF / RF`, `A / B`, `BND +`, and `BND ` plus U+2013 EN DASH. The en dash is constructed from its Unicode code point in the rebuild/update scripts to prevent transport encoding corruption.
- Before the dual-encoder legend revision, the bold rebuild retained 106 front bodies (`FRONT_SHELL` plus 105 inlay bodies); the remapped sixth `AF / RF` contour used the same `ABS (White)` appearance as the other inlays.
- In the active `ARCI Enclosure Rev3 v12`, the 27 rectangular-button labels remain 0.40 mm above the v66-matched placement. `buttonLabelOffset` is 5.15 mm, and the measured land between the evaluated text outline and each 10 x 5 mm opening is 1.168-1.219 mm.
- The VFO through-hole, 16 mm front recess, primary support collar, and collar counterbore are now driven from `vfoCenterX = rightButtonMatrixCenterX` and `vfoCenterZ = -33.6 mm`. All six concentric VFO circle definitions solve at X = 76.500 mm, exactly on the center column of the 3 x 4 right button matrix; the former 0.019 mm discrepancy has been removed.
- An interim V12 layout used single-line `SHIFT`—⊙—`WIDTH` and `AF`—⊙—`RF` legends with 0.6 mm leaders. It only fit at 3 mm text (≈0.45 mm stems, one 0.4 mm extrusion line) and `WIDTH` ended 0.710 mm before the right edge fillet; the enclosure cannot grow because 254 mm already fills the 256 mm Bambu Lab A1 bed.

### V12 dual-encoder legend decision (2026-09-02, A1 / 0.4 mm nozzle)

- Two graphic variants were evaluated in the live model and rejected on appearance: the single-line concentric symbol with leaders (above) and a two-row dot/ring legend (`● SHIFT / ○ WIDTH`, `● AF / ○ RF`, 4 mm words left-aligned after a symbol column). Neither reads well at panel scale, and the symbol geometry (0.6 mm leaders, 0.7–0.85 mm ring strokes) is the least robust feature on a 0.4 mm nozzle.
- Final layout: the original v66 word-only stack, all 4 mm Arial Bold centered on `encoderLegendCenterX = rightDualEncoderCenterX` (113 mm): `SHIFT` at `encoderUpperLegendZ = 50.998977` above the upper encoder, `WIDTH` at `encoderWidthLegendZ = 27.598299` below it, and `AF / RF` at `encoderLowerLegendZ = 16.444501` above the lower encoder. `encoderLegendHeight = frontLabelHeight`.
- Measured extents: `SHIFT` X 107.34–118.66 / Z 49.52–52.48; `WIDTH` X 106.61–119.39 / Z 26.17–29.03; `AF / RF` X 106.09–119.91 / Z 14.96–17.92. Widest word ends 5.2 mm before the right edge fillet; `WIDTH` sits 3.7 mm below the upper recess; `AF / RF` leaves 4.7 mm of land above the lower recess.
- The separate `AF`/`RF` texts and their `FT_FRONT_DUAL_ENCODER_RF_DEBOSS/_INLAY` features were removed and the single `AF / RF` text restored, so `SK_FRONT_LABELS_NATIVE` again holds 31 texts consumed by the standard front deboss/inlay features. All `SK_FRONT_DUAL_ENCODER_SYMBOL_*` sketches and `FT_FRONT_DUAL_ENCODER_*` features are deleted.
- The active front has 106 valid bodies and no unhealthy features. The edits are intentionally left unsaved for visual approval. `Front_Parametric_Rebuild.py` matches this layout; the orphaned `encoderSymbol*`, `encoderUpperSymbolX`, `encoderLowerSymbolX`, `encoderLegendRowPitch`, and `encoderSymbolTextGap` parameters may be deleted from the document.
- A1 print note: at 254 mm the front must be sliced with skirt and brim disabled; the labels print face-down as 3 × 0.2 mm layers, so first-layer squish slightly fattens white strokes—one more reason to keep every label at the 2.9 mm cap height rather than smaller.

### Front-label printability audit and letter spacing (2026-09-02, A1 / 0.4 mm nozzle)

- Audit of the 31 labels before the change: cap height 2.86–2.96 mm, `I` stems 0.58 mm, smallest counters 0.66 mm (`B`, `4`) / 0.73 mm (`R`), 1.17–1.22 mm land between text and every 10 × 5 mm button opening, ≥3.5 mm between words in a row, 0.6 mm = three 0.2 mm layers of inlay. All acceptable for a 0.4 mm nozzle.
- The one failing feature was the black wall *between letters*: true minimum outline-to-outline gaps of 0.09 mm (`X–V`, `V–T` in `XVTR`), 0.17 mm (`T–T` in `ATT`) and 0.27–0.32 mm (`SHIFT`, `WIDTH`, `XIT`, `RIT`, `POWER`, `PWR`, `AF / RF`, `PRE`). Below one 0.42 mm line the slicer cannot lay black between the letters, so they print fused.
- Fix: character spacing. The legacy `createInput` texts expose no spacing, so all 31 labels were recreated as multi-line texts (`createInput2` + `setAsMultiLine`, center/middle alignment) with `frontLabelSpacingPct = 18`. In the multi-line engine `height` is the true cap height, so `frontLabelHeight` is now **2.9 mm** (the same evaluated cap as before; the old 4 mm nominal belonged to the legacy engine). `encoderLegendHeight = frontLabelHeight` still.
- Result: stems 0.59 mm, counters ≥0.67 mm, smallest letter gap **0.44 mm** (`XVTR`), median 0.90 mm; land to button 1.12–1.21 mm; tightest word gap 2.98 mm (`TUNE`|`PROC`). Widths grew ~0.34 mm per gap (e.g. `POWER` 14.80 → 16.38 mm, `WIDTH` 12.79 → 14.35 mm, still 4.9 mm clear of the right edge fillet). All label centers were preserved.
- `FT_FRONT_LABEL_DEBOSS_CUT` and `FT_FRONT_AMS_WHITE_TEXT_INLAY` were recreated from the new texts with identical expressions; they now sit at the end of the timeline rather than inside the `PRINT - AMS FRONT LABELS` group (which still holds the sketch). 106 bodies, no unhealthy features, 105 inlay bodies renamed `INLAY_FRONT_<label>_<nn>_<char>` with the `PLA (White)` appearance.
- API notes for future scripting: `SketchText` proxies from `add()` go stale after further sketch edits (re-read `sk.sketchTexts` before building extrude inputs); the MCP wraps each script in one transaction that rolls back on exception; creating the two label extrudes in the same transaction as the text deletion/creation fails with "Some input argument is invalid"—run text creation, cut, inlay, and legacy deletion as separate calls.
- Follow-up: spacing raised to **22 %** for extra margin on the `X–V`/`V–T` pairs, and the power LED hole was made parametric (`ledHoleX = -112 mm`, `ledHoleZ = 52.1731 mm`, diameter `auxHoleD`) and moved 3.0 mm left from its original PCB-coaxial position (−108.9894) so the wider `POWER` word keeps clear land. The LED does not need to be coaxial with the PCB part. `SK_FRONT_ROTARY_THROUGH` remains fully constrained.
- Unsaved, pending visual approval.

### V4 rear-label typography match to prototype v66

- Prototype v66's `RS232 Back` sketch was verified to use 4 mm `Artifakt Element Extra Bold` with `TextStyleBold`. V4 previously used Arial Regular because the rebuild script assigned a non-functional `isBold` attribute.
- `SK_BACK_LABELS_NATIVE` now uses the verified v66 font and native bold style for `WIFI`, `USB`, `RS232`, and `COM 0`; the four existing connector-centered label positions and orientation were preserved exactly.
- Fusion's current text engine retains the same approximately 2.86-2.96 mm evaluated cap height but produces narrower character advances than the legacy v66 text engine. Word size was intentionally not increased because this change addresses stroke weight while preserving the established connector-centered layout.
- Both rear print features regenerated successfully and remain enabled. Final audit found 17 rear bodies (`BACK_SHELL` plus 16 semantically named `INLAY_BACK_*` bodies), 16 `ABS (White)` appearances, no generic or temporary body names, and no invalid bodies.
- `Back_Parametric_Rebuild.py` now creates the v66 rear typography natively and searches the full design for the validated front white-inlay appearance.

### Button labels driven by `buttonLabelOffset` (2026-09-02)

- Slicer preview showed the label cavities' wall loops fusing with the button-opening loops: only 1.12–1.21 mm of land, while two wall pairs need ≈1.7 mm. The 27 button labels were therefore raised and, at the same time, made parametric.
- Each button label's 30 × 6 mm multi-line text box is now dimensioned from the sketch origin: top corner `<btnZ> + buttonLabelOffset + 3 mm`, bottom corner `<btnZ> + buttonLabelOffset − 3 mm`, and X `<btnX> + 15 mm` (magnitudes, since sketch x = −X and y = −Z). 81 dimensions in `SK_FRONT_LABELS_NATIVE`; the four encoder legends and `MULTI` remain free. Pinning both corners is required — with only the top corner pinned the solver stretches the box and the middle-aligned text moves by half the intended amount.
- `buttonLabelOffset` changed 5.15 → **5.9 mm** from the Parameters dialog. Measured: label centers 5.88–5.91 mm above their buttons, land below 1.90–1.95 mm, gap above to the next row's button ≥2.10 mm. `Front_Parametric_Rebuild.py` (`anchor_button_labels`, `BUTTON_CENTERS`) reproduces the anchoring.

### VFO main dial knob (2026-09-02)

- New component `KNOB_VFO_MAIN` in the master, modeled on the Yaesu FT-710 main dial and driven by `vfo*` parameters. It sits on the Copal RMS20-250-201-1 encoder at `vfoCenterX/Z` (Ø6 mm D-shaft, 4.5 mm across the flat facing +X, shaft tip 14.5 mm in front of the panel, Ø9 bushing protruding 2 mm).
- Geometry: `vfoKnobD = 44 mm`, `vfoKnobL = 21 mm`, 1 mm panel gap (`vfoKnobGap`). **Diamond knurl** (the first straight-groove version was rejected): the 96-tooth star profile `SK_VFO_KNURL_PROFILE` (`vfoKnurlTeeth`, 1.44 mm pitch, `vfoKnurlDepth = 0.5 mm`) is **swept along the axis with a twist** of +27.1° (`FT_VFO_KNURL_RH`) and −27.1° (`FT_VFO_KNURL_LH`), and the two bodies are intersected (`FT_VFO_KNURL_DIAMOND`). The twist follows from `vfoKnurlHelixDeg = 30°` over the 18 mm skirt, so the pyramids form with three features instead of a 192-instance helical pattern. A ruled loft between rotated star sections was tried first and does not work: Fusion matches each tooth to its nearest counterpart, so a 7.2-tooth twist collapsed to a 0.75° residual and the ridges stayed axial. Then a 3 mm smooth bezel band with a 1.5 mm chamfer; Ø36 × 0.4 mm face recess; Ø9 finger cup 3.5 mm deep at 12.5 mm radius with a rounded floor; Ø10.5 × 2.5 mm bushing counterbore; D-profile shaft bore Ø6.15 × 14 mm (flat offset 1.55 mm); Ø2.5 M3 grub-screw pilot at 9 mm behind the back face, entering on the flat side. 5,772 faces (the diamond facets dominate); keep the component normally hidden or suppressed while editing the enclosure.
- API note: `Sketch.modelToSketchSpace` on an offset construction plane returns an out-of-plane z for points not on that plane; zero it before creating curves, or the geometry silently becomes 3D sketch geometry at the model point (which made the first loft attempt fail as "coplanar sections").
- Nearest panel feature to the Ø44 envelope is the `CLR` button at 36 mm from the axis, so the knob has ≥14 mm clearance everywhere.
- **Two-part construction** (requested 2026-09-02): the knurled band is a separate rubber sleeve. `FT_VFO_GRIP_TUBE` (annulus Ø48 / Ø`vfoKnobD − 2·vfoGripWall` = Ø39, from 2 mm to 19 mm behind the panel) is intersected with the knurled knob (`FT_VFO_GRIP_FROM_KNURL`, tool kept) to give `KNOB_VFO_GRIP`, and that sleeve is then cut from the knob (`FT_VFO_CORE_MINUS_GRIP`, tool kept) to give `KNOB_VFO_CORE` with a Ø39 seat. The sleeve is captured between the core's `vfoGripBackLip = 1 mm` rear lip and the bezel; `vfoGripWall = 2.5 mm`. The sleeve body lives in child component `KNOB_VFO_GRIP`.
- Materials: core ABS Plastic / `PLA (Black)` with the bezel chamfer `Aluminum - Satin`; sleeve `Rubber, Black` / `Rubber - Soft`. Print the core back-down in ABS/PLA and the sleeve standing in TPU 95A (stretches ~13 % over the rear lip during assembly). 305 faces, healthy.
- Unsaved, pending visual approval.

### Waveshare display carrier audit and corrections (2026-09-02)

Audited `DISPLAY_CARRIER_WAVESHARE_ARCI` (four corner brackets), the rear glass pocket, the front aperture and the ARCI PCB placement in `ARCI Enclosure Rev3 v19`. The Waveshare 5-DSI-TOUCH-A drawing (129 × 72.8 R4 outline, 110.32 × 62.28 centred active area, 5.6 mm front package, 5.0 mm M2.5 female standoffs on 117 × 61 and 58 × 49 pitches) matches the linked `Waveshare_5_DSI_TOUCH_A v3` reference: glass front to standoff face = 10.62 mm.

Findings and fixes (all parameter-driven, unsaved):

- **ARCI standoffs were on the wrong holes.** `arciMountSpacingX/Z = 133.8 × 80.8` came from the PCB's R1.6 corner-radius arc centres; the real Ø3.2 mounting holes (full circle edges) are on **130.0 × 77.0 mm** (3.5 mm in from each edge, centre unchanged at `-17.74, 11.44`). Every standoff was 1.9 mm off in both X and Z. Parameters corrected; the tabs, standoffs and holes followed.
- **Carrier hole for the display was a 2.2 mm "pilot".** The display has female M2.5 standoffs, so `waveshareMountHoleDia` is now a **2.8 mm clearance** hole (M2.5 screw from the rear through the bracket).
- **Glass pocket was the old Sunton union envelope** (137.62 × 84.93, centred on the Sunton/ARCI centre), leaving the Waveshare glass 3.6–6.3 mm of float. It is now `SK_DISPLAY_WAVESHARE_GLASS_POCKET` / `FT_DISPLAY_WAVESHARE_GLASS_POCKET`: `waveshareGlassW/H + 2 × waveshareGlassFit (0.30)` = **129.6 × 73.4 mm centred on the Waveshare centre**, so the pocket locates the glass. The four Ø8 enclosure posts now sit fully on the 3 mm wall (previously their bases and pilot bottoms hung over the recess).
- **Aperture reveal.** The bevel bottom (2.05 deep) was 0.05 mm below the 2.0 mm pocket floor and only 0.05 mm per side larger than the active area. Now `dispBevelDepth = frontThickness − dispRecessDepth` (2.0) and `dispApertureW/H = waveshareActive + 2 × dispApertureReveal (0.50)` = 111.32 × 63.28 mm; front opening 115.32 × 67.28 mm. About 0.5 mm of black glass border shows per side so print and position tolerance cannot clip pixels.
- `carrierTabMargin` 3 → **4 mm** so the Ø8 standoffs no longer overhang the 2 mm plates and the Ø3.4 post holes keep a 2.3 mm wall.
- `arciPcbFrontY` now derives from the carrier stack (`carrierFrontY + carrierThickness + arciStandoffHeight` = 17.95 mm; was a stale 17.99).
- The separately imported root-level `ARCI v6:1` was at Y 35 and 1.9 / 1.1 mm off in X / Z; it was translated so its PCB front face sits on the standoffs and its holes coincide with them (verified from hole-circle centres at `(-82.74, -27.06)`, `(47.26, -27.06)`, `(47.26, 49.94)`, `(-82.74, 49.94)`).
- Stack (Y): pocket floor 2.0 → glass 2.01–7.63 → standoffs to 12.62 → 0.3 mm contact pads 12.65–12.95 → bracket 12.95–14.95 → Ø8 standoffs to 17.95 → ARCI PCB 17.95–19.42. Front-side IDC header pins reach Y 16.55, 1.6 mm clear of the bracket plates. Posts: Ø8 from Y 3 to 12.85 (0.1 mm gap), Ø2.7 blind M3 pilot to Y 3 → use M3×8–10 screws.
- Boolean intersection check shell / brackets / display bodies / ARCI PCB / ARCI front-side parts: **0 mm³ in every pair**. Timeline healthy.
- Front-shell volume after the pocket change: 149,548.6 mm³ (2,144 faces before the feet bosses).

### Tilt stand (2026-09-02, replaces the paddle feet)

- The first fold-down paddle feet were removed (components and the four bottom-wall bosses) after the full-assembly review: with a 54 mm deep, 130 mm tall box the centre of gravity passes over the rear edge at about 22° of tilt, so a front-only foot cannot be stable, and the 11.5 mm stow height left the rear unsupported.
- Replacement is a parametric rebuild of the user's `Tilt Feet ARCI v41` (Maestro-style stand: flat desk pad, radio pivots on a hinge carried by a bracket screwed to the rear panel), with the seven review items applied:
  1. `STAND_PAD` knuckle (Ø14 barrel, 12.8 wide) sits between two 4 mm `STAND_BRACKET` ears (clevis, double shear) instead of side-by-side knuckles. 24 castellation teeth (15° steps, `standTeeth`) on both knuckle faces and both ear faces lock the angle positively; the two sides always match.
  2. Pivot is 13 mm behind the rear panel (`standPivotBehind`) at Z −61 (`standPivotZ`), so tilting only lifts the enclosure; nothing swings into the pad. Pad top is 1 mm below the ear swing circle.
  3. Bracket plate bottom rests on the pad top at 0° and is the flat stop.
  4. Mount is 2 × M3 into Ø8 × 5 bosses inside the rear wall (`FT_STAND_BOSSES`, `FT_STAND_PILOTS`) at X ±109, Z −50 / −38, chosen to clear the end connector (X 102–112, Z −28 to −18) and the COM 0 legend. Countersunk 3.4 mm holes replace the 6 mm holes.
  5. Ø5.4 bore for a DIN 931 M5 × 30 partially threaded bolt; the 14 mm plain shank spans the rotating knuckle. The 8.2 AF × 3.5 hex-head pocket captures the head, with a DIN 125 washer and DIN 985 nyloc nut on the other side.
  6. Pad 30 × 100 × 6 mm with full-round ends, 60 mm in front of the pivot and 40 mm behind (`standPadRearReach`), two Ø28 × 3 stick-on rubber discs in 0.5 mm seats (modelled as `STAND_RUBBER_*` reference bodies). Ride height 12.5 mm at 0°.
  7. Stability: at 35° the centre of gravity is about 2 mm behind the pivot and at 45° about 15 mm, both inside the 40 mm rear reach; at 0° it is 40 mm in front, inside the 60 mm front reach.
- Left side is an identical translated copy, so the shared definition keeps both sides dimensionally synchronized. Zero Boolean overlap between bracket, pad and both shells. Script: `Tilt_Stand_Build.py`.
- Assembly ownership was cleaned up in `ARCI Enclosure Rev3 - CLEANUP v29`: `TILT_STAND_ASSEMBLY` is the sole top-level stand occurrence and contains two instances of the reusable `STAND_HINGE` definition. Each hinge owns `STAND_BRACKET`, `STAND_PAD`, one M5 fastener set, and two M3 bracket screws. `BACK_HALF` owns only the four integral mounting bosses and blind pilots. Timeline groups are collapsed and split by responsibility: `BACK HALF - STAND BOSSES AND PILOTS`, `STAND PARTS - BRACKET AND PAD`, `STAND HARDWARE - COMPONENT DEFINITIONS`, and `ASSEMBLY - TILT STAND`. Migration script: `Tilt_Stand_Assembly_Refactor.py`.
- Print the pad flat, the bracket on its mounting face; ream the Ø5.4 bores. Sketches are script-generated (unconstrained); dimensions live in the `stand*` parameters.

### Dual-concentric encoder knobs (2026-09-02)

- The two right-side encoders are Alps **EC11EBB24C03** dual-shaft parts: Ø7 bushing to Y −0.33, Ø6 hollow outer shaft to Y −8.0 with a 2 mm slot 4.5 mm deep across its end, Ø3.5 inner D-shaft (flat 0.71 from the axis, 7 mm long) to Y −18.5.
- Legacy `Knurled Knob (Bottom)` / `Knurled Knob Top` occurrences (14,507 and 20,112 faces each) are hidden, not deleted.
- Rebuilt to the supplier drawing of the real concentric pair (second image supplied 2026-09-02):
  - `KNOB_DUAL_OUTER_15`: Ø15 × 13.5 (2 mm C0.5 skirt, 9.5 mm knurl, 2 mm Ø14 top band with C1), **Ø10.2 × 4.5 top recess** (C1 → Ø12) that receives the inner knob's neck, Ø8 × 2 bushing relief underneath, Ø6.2 bore 8 deep (drawing 7; our shaft protrudes 7.4), two 1.7 × 4 drive-key stubs in the shaft slot, Ø4.2 web hole for the inner shaft, radial grub-screw pilot 4.5 above the underside (drawing M2 ⌀3.8; modeled as Ø2.5 for an M3 in PLA). 0.6 mm above the panel. 4,440 faces.
  - `KNOB_DUAL_INNER_11`: Ø6.5 × 4.5 neck nesting in the recess (0.3 mm axial clearance each way), Ø11 × 9.5 knurl body with C0.5, 1.5 mm Ø10 top band with C0.5 (→ Ø9 face), Ø3.6 bore 10 deep from the neck end (round for 2.2 mm, then D with the flat at 0.8), grub-screw pilot 6.5 above the neck end. 3,239 faces.
- Knurl is parametric: one 90° V groove (`knobOuterKnurlDepth` 0.3 / `knobInnerKnurlDepth` 0.28) is **swept along the axis with a twist** `knob*KnurlTwist = knurlH · tan(knobKnurlHelixDeg) / R` (30° helix → 41.9° / 57.1°) and circular-patterned **`knobOuterKnurlN = 60` / `knobInnerKnurlN = 44`** times (0.79 mm pitch, matching the fine knurl of the real parts); both hands give the diamond. Change the tooth count, helix angle or band height in the Parameters dialog and both hands regenerate. The V-groove profile itself is sketch geometry (depth is not a live parameter). A sweep along a fitted-spline helix fails intermittently with `ASM_SWEEP_ILLEGAL_SURFACE`; the twist sweep on the bare cylinder is reliable, so all internal features are cut afterwards, and the pattern axis is a construction axis from the cylinder face (a bare face reference failed validation).
- Appearance `Paint - Enamel Glossy (Black)` (no anodized-black entry in the library). Second pair placed at Z +37 for the upper encoder. Zero overlap against both encoder bodies, the shell and each other.
- Script: `Dual_Encoder_Knobs_Build.py` (deletes and rebuilds the `KNOB_DUAL_*` components). Because the first pair was deleted in the same unsaved session, the rebuilt components currently carry a `(1)` suffix (`KNOB_DUAL_OUTER_15 (1)`); Fusion keeps the deleted names reserved until the document is saved, so rename them after saving.
- Unsaved, pending visual approval.

### Quantitative solid comparison

After rigidly aligning `Front_Half.step` to the Rev2 coordinate system:

| Measurement | Value |
| --- | ---: |
| Rev2 solid volume | 140,941.169 mm³ |
| Original solid volume | 143,632.418 mm³ |
| Shared/overlapping material | 140,105.768 mm³ |
| Rev2 material outside the original | 835.401 mm³ |
| Original material absent from Rev2 | 3,526.650 mm³ |
| Rev2 material matching the original | 99.407% |
| Original material covered by Rev2 | 97.545% |

The updated values add the independently verified 4,678.227022 mm³ boss reconstruction to the prior Boolean comparison. The remaining `3,526.650 mm³` is accounted for by the five measured control collars, whose analytical annular volume is `3,526.6759 mm³`. The approximately `0.026 mm³` difference is within the tolerance of the STEP/Boolean measurement workflow. The older `835.401 mm³` Rev2-only figure is not being used as authority for V3 feature selection; functional comparison is against `Radio Enclosure Front - Proto v66`.

## Remaining Work

### 1. Review and promote the completed orientation remediation

- Inspect the active unsaved canonical document from the standard Front and Back views.
- Save it as the new master only after explicit approval; keep the linked assembly as a disposable transform reference.

### 2. Complete remaining reference geometry

- Reconstruct the display supports when the display phase resumes; the user explicitly deferred this work.
- Evaluate support geometry belonging to separate v66 components only when those components are intentionally migrated into V3.
- Keep repeated internal geometry grouped by subsystem and build it from constrained seed sketches plus model-feature patterns.
- Confirm whether any additional front-face detail is missing outside the measured panel controls during final component integration.
- Perform a final parameter and constraint audit; `SK_LABELS` placement frames are intentionally non-driving.

### 3. Complete final validation

- Compare overall extents and important faces against `Front_Half.step`.
- Section-check the native front and back together after any future mating-parameter edit.
- Preserve the verified 5.96 mm assembled overlap and 8.572 mm³ twelve-zone latch preload.
- Check display, button, rotary-control, and label positions against `Front.dxf`.
- Inspect for unintended interference, gaps, duplicate profiles, and unconstrained geometry.
- Record any deliberate clearance adjustment separately from source dimensions.

## Definition of Done

The reconstruction is complete only when:

- All required native sketches and labels are present and organized.
- Every design-driving sketch is fully constrained.
- Repeated geometry is implemented with model-feature patterns.
- The front body regenerates without warnings or broken references.
- Critical dimensions match the supplied STEP and DXF references.
- The front lip/notches and native back detents retain the verified original interference in a section check.
- Required internal component mounts and support geometry are present and verified against the reference.
- Labels are represented in the exported/manufactured solid with an explicitly chosen process and depth.
- Editing a primary parameter produces a predictable rebuild.
- A final saved Fusion version has been explicitly confirmed by the user.

## Next Action

Inspect the unsaved `ARCI Enclosure Rev3 v19` changes (corrected carrier standoff pattern, Waveshare-sized glass pocket, 0.5 mm aperture reveal, relocated ARCI board, tilt feet, dual-encoder knobs) and save a new version if approved. Print one carrier bracket and one foot module first to confirm the M2.5 clearance, the M3 pilots and the hinge tooth engagement in PLA.
