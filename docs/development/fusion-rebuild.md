# Fusion 360 rebuild and script guide

## Before starting

The scripts require Autodesk Fusion 360 and its `adsk` API. The repository's
STEP, 3MF, and F3D files use Git LFS. The maintained tooling is under
`tools/fusion`.

Each script / tool is made as a Fusion script bundle.
Add its folder from Fusion 360,  **Utilities → Add-Ins → Scripts and Add-Ins → Scripts → +**.

## Supported clean rebuild

Run the scripts in `tools/fusion/rebuild/` in this order against the clean
Fusion design. Run one script at a time and inspect the browser/timeline after
each step.

1. `tools/fusion/rebuild/Front_Parametric_Rebuild/`
2. `tools/fusion/rebuild/Front_Internal_Supports_Add/`
3. `tools/fusion/rebuild/Front_Panel_Caps_LED_And_Materials/`
4. `tools/fusion/rebuild/Back_Parametric_Rebuild/`
5. `tools/fusion/rebuild/Multi_Knob_Build/`
6. `tools/fusion/rebuild/Dual_Encoder_Knobs_Build/`
7. `tools/fusion/rebuild/Tilt_Stand_Build/`
8. `tools/fusion/rebuild/Stand_Hardware_Build/`

`Multi_Knob_Build/` is part of the supported sequence even though the
MULTI/CH knob is a small part. It must not be omitted when reproducing the
complete control layout.

The clean rebuild sequence creates the base mechanical model and supported
stand/control parts.

## Optional parts

`tools/fusion/options/Build_Right_Matrix_Hub_Cradle/` builds the supported
optional USB hub cradle. It is not required for the base enclosure.

## Release audit and export scripts

Use the two Fusion scripts under `tools/fusion/release/` only after the model
has been rebuilt or deliberately migrated:

1. Run `tools/fusion/release/Fusion_Timeline_Audit` with the intended design
   open.
2. Review `docs/generated/fusion_timeline_audit.md` and
   `docs/generated/fusion_timeline_audit.json`.
3. Resolve every release-gate failure. A failing or stale report never
   authorizes an export.
4. Run `tools/fusion/release/Export_Repository_Artifacts` only after the audit
   passes. It emits isolated print parts and matching part-level STEP files;
   it does not emit an assembled front panel.
5. When an accessory-design reference is wanted, run
   `tools/fusion/release/Export_Inspection_Assembly` separately. Its STEP is
   an installed, non-printable project-authored inspection assembly.
6. Inspect changed 3MFs in the target slicer and STEP files in a neutral CAD
   viewer before publishing.

The exporter writes only the named public parts. It does not export a full
assembly, positioned occurrence, vendor model, or ECAD reference. Neither
release script saves the Fusion document. Save a reviewed Fusion version only
after the geometry and timeline changes have been explicitly approved.
