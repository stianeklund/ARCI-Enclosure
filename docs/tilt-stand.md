# Tilt stand

The stand is a pair of identical hinged supports mounted to the rear shell.
Each side uses one bracket, one support, two rubber foot pads, two M3 mounting
screws, and one M5 hinge fastener set.

## Print and prepare

Print two of each rigid part in PLA or PETG:

- [`STAND_BRACKET.3mf`](../export/3mf/STAND_BRACKET.3mf)
- [`TILT_STAND_SUPPORT.3mf`](../export/3mf/TILT_STAND_SUPPORT.3mf)

Print two of each foot pad in TPU, or replace them with suitable stick-on
rubber pads:

- [`TILT_STAND_FOOT_PAD_NEAR_HINGE.3mf`](../export/3mf/TILT_STAND_FOOT_PAD_NEAR_HINGE.3mf)
- [`TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.3mf`](../export/3mf/TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.3mf)

Print the bracket on its flat mounting face and the support on its foot. Ream
the hinge bores gently to 5.4 mm after printing if needed; the parts should
rotate freely before the hinge is tightened.

## Hardware per side

- 2 × M3 × 12 countersunk screws
- 1 × M5 × 30 hex bolt
- 1 × M5 washer
- 1 × M5 nyloc nut

## Assembly

1. Attach a bracket to each pair of rear-shell pilots with the two M3 screws.
2. Place the support between the bracket ears and align the serrated hinge
   faces at the desired angle.
3. Install the M5 bolt, washer, and nyloc nut. Tighten only enough to engage
   the hinge teeth securely; the support must still be adjustable.
4. Fit one near-hinge and one far foot pad to each support.

The rear shell carries the mounting bosses; neither shell requires extra
fasteners at its snap-fit joint. STEP references are available as
[`STAND_BRACKET.step`](../cad/step/STAND_BRACKET.step),
[`TILT_STAND_SUPPORT.step`](../cad/step/TILT_STAND_SUPPORT.step), and the two
separate foot-pad STEP files. This mirrors the print files: the support and
each pad are independently addressable parts, not a combined assembly export.
