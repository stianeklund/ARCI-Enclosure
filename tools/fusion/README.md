# Fusion 360 maintainer tools

This folder contains Fusion 360 scripts for maintainers of the ARCI enclosure.
End users normally need only the printable files in `export/3mf`, the neutral
CAD files in `cad/step`, and the project documentation.

The repository does not contain the private Fusion master. These scripts
rebuild the published parts and create the public release files.

## Before you run a rebuild

The rebuild scripts change the active Fusion document. Use a new working copy
or save a version before you run them. The scripts do not restore the model if
a later step fails.

Start with a parametric Fusion design whose name starts with `ARCI Enclosure
Rev3`. Create these empty root-level components before you run the first
script:

1. `FRONT_HALF`
2. `BACK_HALF`

The scripts expect this component structure. Do not add a body named
`FRONT_SHELL` before you run the first script.

## Install a script bundle

Every public script is a Fusion bundle: its folder contains a same-named
`.py` file and `.manifest`. In **Utilities → Add-Ins → Scripts and Add-Ins**,
open **Scripts**, click **+**, and select the script folder (not the `.py`
file). Install each required bundle once; it remains available in Fusion's
Scripts list thereafter.

## Supported rebuild sequence

Run the scripts in `rebuild/` in this order:

1. `Front_Parametric_Rebuild/`
2. `Front_Internal_Supports_Add/`
3. `Front_Panel_Caps_LED_And_Materials/`
4. `Back_Parametric_Rebuild/`
5. `Multi_Knob_Build/`
6. `Dual_Encoder_Knobs_Build/`
7. `Tilt_Stand_Build/`
8. `Stand_Hardware_Build/`

Run a complete rebuild in a new working document. Some scripts stop when they
find existing geometry. Other scripts replace their earlier script-owned
components.

`options/Build_Right_Matrix_Hub_Cradle/` creates the optional USB-hub cradle.
It is not required for the base enclosure.

## VFO dimple sizing repair

The VFO main knob belongs to the private master, rather than the supported
clean-rebuild set.  If its circular finger dimple loses its curved floor after
editing `vfoDimpleD`, add and run the `rebuild/VFO_Dimple_Parameterize` script
folder once with the master open.  Thereafter, edit only `vfoDimpleD` for ordinary sizing; the
script derives the dimple depth and floor-round radius so the cup keeps its
original 2 mm flat floor and tangent curved sides.  Use a diameter greater
than `vfoDimpleFloorD`.

## Audit and export

Install each release script separately in Fusion:

1. Open **Utilities → Add-Ins → Scripts and Add-Ins → Scripts → +**.
2. Add `release/Fusion_Timeline_Audit`.
3. Add `release/Export_Repository_Artifacts`.

Before you export, review the repository changes. The exporter replaces the
published 3MF and STEP files when it completes successfully.

1. Run `Fusion_Timeline_Audit` on the active release design.
2. Read the report in `docs/generated/fusion_timeline_audit.md`.
3. Resolve every release-gate failure.
4. Run `Export_Repository_Artifacts`.

The audit creates `docs/generated` if needed. It writes a Markdown and JSON
report there. On failure, it writes an error report in the same directory. The
exporter checks the active design again. It exports only the named public parts
in its manifest to `export/3mf` and `cad/step`.

The exporter does not export a full assembly, vendor reference geometry, or an
ECAD model. Neither release script saves the Fusion document.

## Scope and requirements

This public folder excludes private migration, experimental, quality-assurance,
and development-asset tools. Those tools are not part of the supported rebuild
or release process.

The scripts locate the repository from their own file paths. You can use any
checkout location. They require Fusion 360 and its Autodesk Fusion API
(`adsk`).
