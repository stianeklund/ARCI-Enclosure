# Printing guide

This guide covers the core enclosure parts.
Optional USB-hub parts have separate [installation notes](right-matrix-usb-hub-shim.md).

## Printer requirements

Use a 3D printer with a build area of 256 × 256 mm or more.
The front shell measures 254 mm across its longest side.

Use a 0.4mm nozzle & use Arachne wall generation for the best text inlay results.

## Enclosure print files

Print the quantities shown for one enclosure.

| Part | Quantity | File |
| --- | ---: | --- |
| Front enclosure with label inlays | 1 | [`FRONT_HALF.3mf`](../export/3mf/FRONT_HALF.3mf) |
| Back enclosure with label inlays | 1 | [`BACK_HALF.3mf`](../export/3mf/BACK_HALF.3mf) |

`FRONT_HALF.3mf` contains only `FRONT_SHELL` and its `INLAY_FRONT_*` label
bodies. `BACK_HALF.3mf` contains only `BACK_SHELL` and its `INLAY_BACK_*`
label bodies.

## Knobs & buttons

These are entirely optional but in theory should be printable, please see [`BOM.md`](../BOM.md) for details.
The parts are to some degree reference implementations or approximations meant for fitting.

| Part | Quantity | File |
| --- | ---: | --- |
| MULTI/CH knob | 1 | [`KNOB_MULTI.3mf`](../export/3mf/KNOB_MULTI.3mf) |
| Dual-encoder outer knob | 2 | [`KNOB_DUAL_OUTER_15.3mf`](../export/3mf/KNOB_DUAL_OUTER_15.3mf) |
| Dual-encoder inner knob | 2 | [`KNOB_DUAL_INNER_11.3mf`](../export/3mf/KNOB_DUAL_INNER_11.3mf) |
| VFO knob core | 1 | [`KNOB_VFO_CORE.3mf`](../export/3mf/KNOB_VFO_CORE.3mf) |
| VFO grip sleeve | 1 | [`KNOB_VFO_GRIP.3mf`](../export/3mf/KNOB_VFO_GRIP.3mf) |
| Button cap | 27 | [`BUTTON_CAP.3mf`](../export/3mf/BUTTON_CAP.3mf) |

The two inner/outer knob pairs serve the AF/RF-gain and IF-shift controls as the encoders are dual axis encoders.

## Mounts and stand

| Part | Quantity | File |
| --- | ---: | --- |
| Display carrier / bracket | 1 set | [`DISPLAY_CARRIER_WAVESHARE_ARCI.3mf`](../export/3mf/DISPLAY_CARRIER_WAVESHARE_ARCI.3mf) |
| Stand bracket | 2 | [`STAND_BRACKET.3mf`](../export/3mf/STAND_BRACKET.3mf) |
| Stand support | 2 | [`TILT_STAND_SUPPORT.3mf`](../export/3mf/TILT_STAND_SUPPORT.3mf) |
| Near-hinge foot pad | 2 | [`TILT_STAND_FOOT_PAD_NEAR_HINGE.3mf`](../export/3mf/TILT_STAND_FOOT_PAD_NEAR_HINGE.3mf) |
| Far foot pad | 2 | [`TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.3mf`](../export/3mf/TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.3mf) |

The stand / hinged feet are not a print in place model, you need to the parts separately.

## Materials

I recommend to use PLA, but I'm sure PETG could be used or similar materials.
I also haven't actually tried this but you could probably use TPU for the foot pads and similarly for the VFO encoder "sleeve".

## Part orientation

- Put each stand bracket on its flat mounting face.
- Put each stand support on its foot.
- Orient knobs and caps so their visible faces are upward and their bores do
  not require unsupported bridging.
- Keep the supplied orientation for the other 3MF files.

## Front-panel text

Use Arachne wall generation for the small front-panel text. Check each label in
the slicer preview.

Use a multi-material print for the integrated white text. You can also paint
the recessed text after printing.

The exporter refuses to publish a front or rear 3MF unless it contains both
the black shell and white label-body colours. If a slicer still shows orange,
re-export from Fusion and verify that the imported model has separate shell and
`INLAY_*` bodies before assigning filaments.

See the [tilt-stand instructions](tilt-stand.md) for stand preparation and
assembly.
