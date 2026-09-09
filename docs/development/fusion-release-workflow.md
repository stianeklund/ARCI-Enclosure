# Fusion release workflow

The editable master remains a parametric Fusion document. The public release
directories contain only release-safe artifacts: project-authored print files
in `export/3mf`, isolated neutral exchange files in `cad/step`, and an
explicitly curated project-authored inspection assembly in `cad/assembly` when
one is exported. Reference assets and unsupported maintainer tooling remain
private. Do not check in a full assembly archive: it can contain vendor and
ECAD reference models that are excluded from redistribution.

## Timeline policy

Keep the timeline in this order and collapse each group once it is complete:

1. `DATUMS AND PARAMETERS` — component origins, named planes, global user parameters.
2. `FRONT HALF - MECHANICAL` and `BACK HALF - MECHANICAL` — shell, cavity, mating interface, and panel cutouts.
3. `INTERFACES - CARRIERS AND MOUNTS` — display, hub, and electronics-specific printed parts.
4. `BACK HALF - STAND BOSSES AND PILOTS`, then `STAND PARTS` and `ASSEMBLY - TILT STAND`.
5. `PRINT - ...` — deboss and AMS inlay features. Keep these collapsed and suppress them while editing mechanics if Fusion performance requires it.
6. `REFERENCE - ...` — imported/vendor geometry, hidden and never included in a release export.

One group should cover one responsibility and one contiguous timeline range.
Avoid end-of-timeline `Move` / `Align` features in the release master: fix
orientation in the driving datum or keep presentation moves in a separate
document. The exporter publishes only bodies directly owned by each named
component, not positioned occurrences, child inspection components, or the
full assembly. This keeps controls, LEDs, display models, and vendor/ECAD
references useful in the master without putting them in a printable part or
part-level STEP file.

## Release checklist

1. Open the intended parametric master and move the timeline marker to the end.
2. In **Utilities → Add-Ins → Scripts and Add-Ins**, select the **Scripts** tab. Click the `+` button and choose **Script or add-in from device**, then select `tools/fusion/release/Fusion_Timeline_Audit`. Fusion remembers this link, so this is a one-time step. Click **Run** for `Fusion_Timeline_Audit`.
3. Read both `docs/generated/fusion_timeline_audit.md` and `docs/generated/fusion_timeline_audit.json`. These are ignored local working reports: JSON is the automation contract and Markdown is the review record. Attach the passing reports to a release or CI record when evidence must be retained; do not commit a failing or machine-specific snapshot.
4. Resolve every gate failure. The 42 named active-master release-driving sketches are evaluated per entity role, not solely by Fusion's sketch aggregate flag. This includes `ACTIVE_ROOT / SK_DISPLAY_RECESS`, `FRONT_HALF / SK_FRONT_ROTARY_RECESSES_DEEP`, and `FRONT_HALF / SK_FRONT_ROTARY_THROUGH`, which directly drive `FRONT_SHELL`. `PARAMETRIC_DRIVING` is the preferred standard: every release curve participates in driving dimensions/geometric constraints or is a reference/projected/linked curve driven upstream. Offset-constraint outputs are recognized where Fusion exposes their entities. If Fusion's aggregate solver reports fully constrained and there are no true orphans, the audit accepts `PARAMETRIC_DRIVING` with an explicit aggregate-fallback marker when per-entity API mapping is opaque. Independent points that participate in those driving relations are permitted parametric datum helpers. `LOCKED_LEGACY` passes only when every release curve is explicitly fixed and there are no independent/unconnected non-reference sketch points; it is stable but remains a visible technical-debt warning, not the preferred editable standard. `HYBRID_DRIVING_LOCKED` also passes when every curve is covered by the union of explicit fixes and driving dimensions/geometric constraints; it is likewise technical debt and should be converted to fully parametric driving when practical. `ORPHAN_ENTITY` and `FREE_DRIVING` fail. Curve-owned endpoints, centers, spline handles, origins, and reference points do not count as orphan points.
5. The only active-master `REFERENCE_EXCEPTION` pairs are `ACTIVE_ROOT / SK_CANONICAL_DATUM_POINTS`, `LEFT_BUTTON_MATRIX_HARNESS / SK_LEFT_MATRIX_RIBBON_PATH`, and `8PIN_PANEL_CONNECTOR_REFERENCE / SK_GX16_8PIN_CORRECTED_FRONT_PROFILE`; their rationales and evidence are emitted in the audit. `ACTIVE_ROOT` means Fusion's actual `design.rootComponent`, never its mutable document/version display name. Any additional active-master sketch with an orphan/free role fails as **unclassified** until it receives an exact policy decision.
6. Linked-document sketches—including TL3301, EC11E, PEC11R, RMS20, Waveshare, and any other externally referenced document—are reported with occurrence provenance, visibility, aggregate state, and entity-role evidence but are outside the active-master constraint gate. Hide visible linked occurrences for a focused review when practical; this is advisory-only because the exporter writes exact named project-owned component/body targets and never exports full assemblies or occurrences. Confirm the timeline marker is at the end, every timeline group is collapsed, and no release-relevant active-master component contains a `Move` or `Align` feature.
7. Link `tools/fusion/release/Export_Repository_Artifacts` using the same `+` button. Click **Run** only after the audit passes. The exporter repeats the same in-memory gate immediately before writing, so a stale clean report cannot authorize an overwrite.
8. The per-part exporter may write only its allowlisted public contract: 17 named 3MF files under `export/3mf` and 17 matching per-part STEP files under `cad/step`. Component artifacts contain only that component's directly owned bodies, so a `FRONT_HALF` export contains the shell and its `INLAY_*` bodies but not nested knobs, caps, LEDs, display models, vendor models, or ECAD references. This applies identically to 3MF and STEP. The shell must carry a black appearance and every `INLAY_*` body a white appearance; staged 3MF validation rejects missing shell/inlay bodies or black/white colours. The two stand sides must pass the exporter's topology-and-size equivalence signature before the positive-side bracket/support definitions can serve as their canonical manufacturing source; otherwise the exporter requires handed artifacts. `WIFI6_REAR_HOLDER` is not part of this contract unless it is deliberately restored to the master, documented, and audited.
9. Use `tools/fusion/release/Export_Inspection_Assembly` only when a positioned, non-printable STEP is wanted for a carry case or other accessory. It exports all project-authored native bodies in their installed positions to `cad/assembly/ARCI_ENCLOSURE_INSPECTION.step` and deliberately excludes linked supplier components. It is a separate contract from the per-part exports; never send it to a slicer.
10. Open each changed 3MF in the target slicer; validate part count, orientation, and the black-shell / white-`INLAY_*` body assignment. Open the changed per-part STEP files and, when generated, the inspection STEP in a neutral CAD viewer as a final geometry check.
11. Review `git diff --stat` and commit only the generated public artifacts and related documentation. Do not add vendor, ECAD, temporary inspection, or ignored Fusion archive files.

The exporter generates and validates the complete set in an ignored,
same-filesystem staging directory before it touches public paths. It backs up
existing artifacts during promotion and attempts a full rollback if promotion
fails, preventing an ordinary mid-export failure from leaving a partial set.

The scripts intentionally fail if a named release component/body is missing or
duplicate; if the timeline is rolled back; or if the shared quality gate finds
active-master unhealthy features, unresolved/stale policy, required
`ORPHAN_ENTITY`/`FREE_DRIVING` roles, unclassified active-master orphan/free
sketches, expanded groups, or release-relevant active-master Move/Align
features. `LOCKED_LEGACY` and
`HYBRID_DRIVING_LOCKED` pass with visible technical-debt warnings.
Linked-document findings and visibility remain visible as audit advisories but
do not block the active-master release gate. That turns a silent stale or
incomplete export into an actionable release failure.
