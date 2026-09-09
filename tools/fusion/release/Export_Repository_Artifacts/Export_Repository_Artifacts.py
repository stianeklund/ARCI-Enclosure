"""Export scrubbed, print-ready ARCI artifacts from the active Fusion master.

Run only after ``Fusion_Timeline_Audit.py`` has reported a healthy design.
The script exports named, project-authored components to the checked-in STEP
and 3MF release folders. It intentionally does *not* export the full assembly:
the working master can include vendor and ECAD reference geometry that is not
redistributable.

The script finds the repository relative to this file, so it can be linked
directly from ``tools/fusion/release/Export_Repository_Artifacts`` in Fusion
from any local checkout path.
"""

from pathlib import Path
from contextlib import contextmanager
import re
import runpy
import shutil
import tempfile
import zipfile

import adsk.core
import adsk.fusion


def repository_root():
    """Find the repository without depending on a particular checkout path."""
    script_path = Path(__file__).resolve()
    for candidate in (script_path.parent, *script_path.parents):
        if ((candidate / 'cad').is_dir() and
                (candidate / 'export').is_dir() and
                (candidate / 'README.md').is_file()):
            return candidate
    raise RuntimeError(
        'Could not locate the ARCI repository from the Fusion script path')


REPOSITORY_ROOT = repository_root()
THREEMF_DIRECTORY = REPOSITORY_ROOT / 'export' / '3mf'
STEP_DIRECTORY = REPOSITORY_ROOT / 'cad' / 'step'
AUDIT_SCRIPT = (REPOSITORY_ROOT / 'tools' / 'fusion' / 'release' /
                'Fusion_Timeline_Audit' / 'Fusion_Timeline_Audit.py')

BODY_PARENT_COMPONENT = {
    'SUPPORT_ARM': 'TILT_STAND_SUPPORT_POS_X',
    'FOOT_PAD_NEAR_HINGE': 'TILT_STAND_SUPPORT_POS_X',
    'FOOT_PAD_FAR_FROM_HINGE': 'TILT_STAND_SUPPORT_POS_X',
}

STAND_SIDE_PAIRS = (
    ('TILT_STAND_BRACKET_POS_X', 'TILT_STAND_BRACKET_NEG_X'),
    ('TILT_STAND_SUPPORT_POS_X', 'TILT_STAND_SUPPORT_NEG_X'),
)

# The component name is the contract between the native Fusion master and the
# repository.  3MF exports preserve multi-body front/rear parts (black shell +
# white INLAY_* bodies) for AMS assignment.  The exporter copies only bodies
# directly owned by a named component into a temporary export component.  Do
# not substitute an occurrence: child occurrences can include inspection-only
# knobs, button caps, LEDs, vendor models, and ECAD reference geometry.
PRINT_ARTIFACTS = (
    ('component', 'FRONT_HALF', 'FRONT_HALF.3mf'),
    ('component', 'BACK_HALF', 'BACK_HALF.3mf'),
    ('component', 'KNOB_MULTI', 'KNOB_MULTI.3mf'),
    ('component', 'KNOB_DUAL_OUTER_15', 'KNOB_DUAL_OUTER_15.3mf'),
    ('component', 'KNOB_DUAL_INNER_11', 'KNOB_DUAL_INNER_11.3mf'),
    ('component', 'KNOB_VFO_MAIN', 'KNOB_VFO_CORE.3mf'),
    ('component', 'KNOB_VFO_GRIP', 'KNOB_VFO_GRIP.3mf'),
    ('component', 'DEV_BUTTON_CAP_MASTER_NATIVE', 'BUTTON_CAP.3mf'),
    ('component', 'DISPLAY_CARRIER_WAVESHARE_ARCI', 'DISPLAY_CARRIER_WAVESHARE_ARCI.3mf'),
    # Both stand-side definitions have a matching manufacturing signature.
    # Export the positive-side definitions once; release instructions specify
    # quantity two and the negative-side definitions remain assembly-only.
    ('component', 'TILT_STAND_BRACKET_POS_X', 'STAND_BRACKET.3mf'),
    ('body', 'SUPPORT_ARM', 'TILT_STAND_SUPPORT.3mf'),
    ('body', 'FOOT_PAD_NEAR_HINGE', 'TILT_STAND_FOOT_PAD_NEAR_HINGE.3mf'),
    ('body', 'FOOT_PAD_FAR_FROM_HINGE', 'TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.3mf'),
    ('component', 'HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA', 'HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA.3mf'),
    ('component', 'HUB_RETAINER_UPPER', 'HUB_RETAINER_UPPER.3mf'),
    ('component', 'HUB_RETAINER_LOWER', 'HUB_RETAINER_LOWER.3mf'),
    ('component', 'HUB_REAR_TRAY', 'HUB_REAR_TRAY.3mf'),
)

# Per-part STEP mirrors the printable-part contract. A STEP named after a
# printable part must contain the same isolated part geometry, never an
# inspection assembly or installed control.
STEP_ARTIFACTS = (
    ('component', 'FRONT_HALF', 'Front_Half.step'),
    ('component', 'BACK_HALF', 'BACK_HALF.step'),
    ('component', 'KNOB_MULTI', 'KNOB_MULTI.step'),
    ('component', 'KNOB_DUAL_OUTER_15', 'KNOB_DUAL_OUTER_15.step'),
    ('component', 'KNOB_DUAL_INNER_11', 'KNOB_DUAL_INNER_11.step'),
    ('component', 'KNOB_VFO_MAIN', 'KNOB_VFO_CORE.step'),
    ('component', 'KNOB_VFO_GRIP', 'KNOB_VFO_GRIP.step'),
    ('component', 'DEV_BUTTON_CAP_MASTER_NATIVE', 'BUTTON_CAP.step'),
    ('component', 'DISPLAY_CARRIER_WAVESHARE_ARCI', 'DISPLAY_CARRIER_WAVESHARE_ARCI.step'),
    ('component', 'TILT_STAND_BRACKET_POS_X', 'STAND_BRACKET.step'),
    ('body', 'SUPPORT_ARM', 'TILT_STAND_SUPPORT.step'),
    ('body', 'FOOT_PAD_NEAR_HINGE', 'TILT_STAND_FOOT_PAD_NEAR_HINGE.step'),
    ('body', 'FOOT_PAD_FAR_FROM_HINGE', 'TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.step'),
    ('component', 'HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA', 'HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA.step'),
    ('component', 'HUB_RETAINER_UPPER', 'HUB_RETAINER_UPPER.step'),
    ('component', 'HUB_RETAINER_LOWER', 'HUB_RETAINER_LOWER.step'),
    ('component', 'HUB_REAR_TRAY', 'HUB_REAR_TRAY.step'),
)

# This independent allowlist makes accidental manifest additions fail closed.
# Only these exact repository paths may be published by this script.
PUBLIC_ARTIFACT_PATHS = frozenset((
    'export/3mf/FRONT_HALF.3mf',
    'export/3mf/BACK_HALF.3mf',
    'export/3mf/KNOB_MULTI.3mf',
    'export/3mf/KNOB_DUAL_OUTER_15.3mf',
    'export/3mf/KNOB_DUAL_INNER_11.3mf',
    'export/3mf/KNOB_VFO_CORE.3mf',
    'export/3mf/KNOB_VFO_GRIP.3mf',
    'export/3mf/BUTTON_CAP.3mf',
    'export/3mf/DISPLAY_CARRIER_WAVESHARE_ARCI.3mf',
    'export/3mf/STAND_BRACKET.3mf',
    'export/3mf/TILT_STAND_SUPPORT.3mf',
    'export/3mf/TILT_STAND_FOOT_PAD_NEAR_HINGE.3mf',
    'export/3mf/TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.3mf',
    'export/3mf/HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA.3mf',
    'export/3mf/HUB_RETAINER_UPPER.3mf',
    'export/3mf/HUB_RETAINER_LOWER.3mf',
    'export/3mf/HUB_REAR_TRAY.3mf',
    'cad/step/Front_Half.step',
    'cad/step/BACK_HALF.step',
    'cad/step/KNOB_MULTI.step',
    'cad/step/KNOB_DUAL_OUTER_15.step',
    'cad/step/KNOB_DUAL_INNER_11.step',
    'cad/step/KNOB_VFO_CORE.step',
    'cad/step/KNOB_VFO_GRIP.step',
    'cad/step/BUTTON_CAP.step',
    'cad/step/DISPLAY_CARRIER_WAVESHARE_ARCI.step',
    'cad/step/STAND_BRACKET.step',
    'cad/step/TILT_STAND_SUPPORT.step',
    'cad/step/TILT_STAND_FOOT_PAD_NEAR_HINGE.step',
    'cad/step/TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.step',
    'cad/step/HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA.step',
    'cad/step/HUB_RETAINER_UPPER.step',
    'cad/step/HUB_RETAINER_LOWER.step',
    'cad/step/HUB_REAR_TRAY.step',
))

# These names must survive a multipart 3MF export. The shell has its assigned
# black print appearance and every inlay body retains its separate white-print
# appearance; the 3MF therefore remains usable for AMS assignment instead of
# becoming a single orange/default-colour mesh.
MULTIPART_3MF_REQUIREMENTS = {
    'FRONT_HALF.3mf': ('FRONT_SHELL', 'INLAY_FRONT_'),
    'BACK_HALF.3mf': ('BACK_SHELL', 'INLAY_BACK_'),
}


def collection_items(collection):
    """Use Fusion's documented collection API instead of Python iteration."""
    return [collection.item(index) for index in range(collection.count)]


def validate_manifest():
    """Validate exact paths, target kinds, extensions, and uniqueness."""
    paths = []
    for kind, _, filename in PRINT_ARTIFACTS:
        if kind not in ('component', 'body') or Path(filename).suffix.lower() != '.3mf':
            raise RuntimeError('Invalid 3MF manifest entry: %s' % filename)
        paths.append((Path('export') / '3mf' / filename).as_posix())
    for kind, _, filename in STEP_ARTIFACTS:
        if kind not in ('component', 'body') or Path(filename).suffix.lower() != '.step':
            raise RuntimeError('Invalid STEP manifest entry: %s' % filename)
        paths.append((Path('cad') / 'step' / filename).as_posix())
    if len(paths) != len(set(paths)):
        raise RuntimeError('Public artifact manifest contains duplicate paths.')
    if frozenset(paths) != PUBLIC_ARTIFACT_PATHS:
        raise RuntimeError('Public artifact manifest does not match the exact allowlist.')


def native_component_definitions(design, required_names):
    """Resolve one native occurrence-backed definition for every exact name."""
    components = collection_items(design.allComponents)
    occurrences = collection_items(design.rootComponent.allOccurrences)
    resolved = {}
    missing = []
    ambiguous = []
    referenced_collisions = []
    for name in sorted(required_names):
        candidates = [component for component in components if component.name == name]
        native = []
        referenced = []
        for component in candidates:
            component_occurrences = [
                occurrence for occurrence in occurrences
                if occurrence.component == component
            ]
            if any(occurrence.isReferencedComponent
                   for occurrence in component_occurrences):
                referenced.append(component)
            if any(not occurrence.isReferencedComponent
                   for occurrence in component_occurrences):
                native.append(component)
        if referenced:
            referenced_collisions.append(name)
        if not native:
            missing.append(name)
        elif len(native) != 1:
            ambiguous.append(name)
        else:
            resolved[name] = native[0]
    if referenced_collisions:
        raise RuntimeError('Referenced components collide with release names: %s' %
                           ', '.join(referenced_collisions))
    if missing:
        raise RuntimeError('Required native release components are missing: %s' %
                           ', '.join(missing))
    if ambiguous:
        raise RuntimeError('Duplicate native release component definitions: %s' %
                           ', '.join(ambiguous))
    return resolved


def component_definitions(design):
    required_components, _ = required_names()
    return native_component_definitions(design, required_components)


def named_bodies(definitions, names):
    """Resolve each print body inside its explicit owning component."""
    resolved = {}
    for name in names:
        parent_name = BODY_PARENT_COMPONENT.get(name)
        if parent_name is None:
            raise RuntimeError('Print body has no owning-component contract: %s' % name)
        parent = definitions.get(parent_name)
        if parent is None:
            raise RuntimeError('Print-body parent component is missing: %s' % parent_name)
        matches = [body for body in collection_items(parent.bRepBodies)
                   if body.name == name]
        if not matches:
            continue
        if len(matches) > 1:
            raise RuntimeError('Duplicate print body in %s: %s' % (parent_name, name))
        resolved[name] = matches[0]
    return resolved


def close_enough(left, right, relative_tolerance=1e-5, absolute_tolerance=1e-8):
    return abs(left - right) <= max(
        absolute_tolerance,
        relative_tolerance * max(abs(left), abs(right)),
    )


def body_signature(body):
    bounds = body.boundingBox
    extents = (
        bounds.maxPoint.x - bounds.minPoint.x,
        bounds.maxPoint.y - bounds.minPoint.y,
        bounds.maxPoint.z - bounds.minPoint.z,
    )
    return (body.faces.count, body.edges.count, body.volume,
            body.physicalProperties.area, extents)


def validate_stand_side_equivalence_signature(design):
    """Reject handed stand geometry using independent topology/size evidence."""
    required = {name for pair in STAND_SIDE_PAIRS for name in pair}
    definitions = native_component_definitions(design, required)

    for positive_name, negative_name in STAND_SIDE_PAIRS:
        positive_bodies = collection_items(definitions[positive_name].bRepBodies)
        negative_bodies = collection_items(definitions[negative_name].bRepBodies)
        if (len({body.name for body in positive_bodies}) != len(positive_bodies) or
                len({body.name for body in negative_bodies}) != len(negative_bodies)):
            raise RuntimeError('Stand-side definitions contain duplicate body names.')
        positive = {body.name: body for body in positive_bodies}
        negative = {body.name: body for body in negative_bodies}
        if set(positive) != set(negative):
            raise RuntimeError(
                'Stand sides have different body sets: %s versus %s' %
                (positive_name, negative_name)
            )
        for body_name in sorted(positive):
            left = body_signature(positive[body_name])
            right = body_signature(negative[body_name])
            exact_match = left[:2] == right[:2]
            numeric_match = all(close_enough(a, b) for a, b in zip(
                (left[2], left[3], *left[4]),
                (right[2], right[3], *right[4]),
            ))
            if not exact_match or not numeric_match:
                raise RuntimeError(
                    'Stand sides differ for body %s; export handed parts '
                    'instead of the canonical positive-side definition.' % body_name
                )


def required_names():
    artifacts = PRINT_ARTIFACTS + STEP_ARTIFACTS
    components = {name for kind, name, _ in artifacts if kind == 'component'}
    bodies = {name for kind, name, _ in artifacts if kind == 'body'}
    return components, bodies


def validate_shell_and_inlay_appearances(definitions):
    """Require the black-shell / white-inlay material contract before export."""
    contracts = (
        ('FRONT_HALF', 'FRONT_SHELL', 'INLAY_FRONT_'),
        ('BACK_HALF', 'BACK_SHELL', 'INLAY_BACK_'),
    )
    for component_name, shell_name, inlay_prefix in contracts:
        component = definitions[component_name]
        component_bodies = collection_items(component.bRepBodies)
        shell = next((body for body in component_bodies if body.name == shell_name), None)
        inlays = [body for body in component_bodies
                  if body.name.startswith(inlay_prefix)]
        if shell is None or not inlays:
            raise RuntimeError('%s must directly own %s and %s* bodies.' %
                               (component_name, shell_name, inlay_prefix))
        shell_appearance = shell.appearance
        if not shell_appearance or 'black' not in shell_appearance.name.lower():
            raise RuntimeError('%s must use a black body appearance before export.' %
                               shell_name)
        non_white = [body.name for body in inlays
                     if (not body.appearance or
                         'white' not in body.appearance.name.lower())]
        if non_white:
            raise RuntimeError('%s bodies must use a white appearance: %s' %
                               (inlay_prefix, ', '.join(sorted(non_white))))


def release_checks(design, definitions):
    """Fail before writing when the master cannot produce a safe release."""
    audit = runpy.run_path(str(AUDIT_SCRIPT))
    gate_result = audit['evaluate'](design)
    failure = audit['gate_error'](gate_result)
    if failure:
        raise RuntimeError(failure)

    required_components, required_bodies = required_names()
    bodies = named_bodies(definitions, required_bodies)
    missing_bodies = sorted(required_bodies - set(bodies))
    if missing_bodies:
        raise RuntimeError('Required release bodies are missing: %s' %
                           ', '.join(missing_bodies))
    # ``evaluate`` above already rejects unhealthy active-master components.
    # Do not rescan every definition here: linked-document health is inventory
    # evidence only and those definitions are never export targets.
    if design.timeline.markerPosition != design.timeline.count:
        raise RuntimeError('Move the timeline marker to the end before export.')
    validate_shell_and_inlay_appearances(definitions)
    validate_stand_side_equivalence_signature(design)
    return bodies


def export_3mf(manager, component, destination):
    """Export a direct-body-only component as native 3MF."""
    options = manager.createC3MFExportOptions(component, str(destination))
    if not manager.execute(options):
        raise RuntimeError('Fusion failed to export 3MF: %s' % destination.name)


def export_step(manager, component, destination):
    options = manager.createSTEPExportOptions(str(destination), component)
    if not manager.execute(options):
        raise RuntimeError('Fusion failed to export STEP: %s' % destination.name)


@contextmanager
def direct_body_export_component(design, source_component):
    """Yield a temporary component containing only ``source_component`` bodies.

    Fusion component export is recursive: exporting ``FRONT_HALF`` also exports
    every nested occurrence. The master deliberately keeps controls and
    reference models beneath the enclosure for inspection, so exporting the
    source component directly leaks those non-part bodies into both the 3MF and
    STEP artifacts. A temporary identity occurrence is a small, explicit
    export assembly that has no child occurrences and therefore cannot leak
    those models. It preserves each direct body's name and appearance, which
    keeps the multipart AMS shell/inlay contract intact.

    This temporary occurrence is always deleted and the script never saves the
    master document.
    """
    source_bodies = collection_items(source_component.bRepBodies)
    if not source_bodies:
        raise RuntimeError('Release component has no directly owned bodies: %s' %
                           source_component.name)

    root = design.rootComponent
    occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    export_component = occurrence.component
    export_component.name = '__ARCI_DIRECT_BODY_EXPORT__'
    try:
        for source_body in source_bodies:
            # ``copyToComponent(occurrence)`` copies into the occurrence's
            # *parent*, which would pollute the root and leave this component
            # empty. A Copy/Paste feature is explicitly owned by the temporary
            # component and works in a parametric design.
            existing_count = export_component.bRepBodies.count
            copied_feature = export_component.features.copyPasteBodies.add(source_body)
            if copied_feature is None or export_component.bRepBodies.count != existing_count + 1:
                raise RuntimeError('Could not copy %s from %s for export.' %
                                   (source_body.name, source_component.name))
            copied_body = export_component.bRepBodies.item(existing_count)
            copied_body.name = source_body.name
            if source_body.appearance:
                copied_body.appearance = source_body.appearance
        yield export_component
    finally:
        if occurrence and occurrence.isValid:
            occurrence.deleteMe()


def validate_staged_exports(staged):
    """Reject missing, empty, corrupt, or incorrectly typed staged output."""
    problems = []
    for source, _, relative in staged:
        if not source.is_file() or source.stat().st_size == 0:
            problems.append('%s (missing or empty)' % relative)
            continue
        if source.suffix.lower() == '.3mf':
            try:
                with zipfile.ZipFile(source) as archive:
                    corrupt = archive.testzip()
                    names = archive.namelist()
                    model_names = [name for name in names
                                   if name.lower().endswith('.model')]
                    model_xml = b''.join(archive.read(name) for name in model_names)
                if corrupt or not any(name.lower().endswith('.model') for name in names):
                    problems.append('%s (invalid 3MF package)' % relative)
                    continue
                required_names = MULTIPART_3MF_REQUIREMENTS.get(source.name)
                if required_names:
                    exported_names = set(re.findall(
                        rb'<object\s+[^>]*\bname="([^"]+)"', model_xml))
                    missing_names = []
                    for required_name in required_names:
                        encoded = required_name.encode('utf-8')
                        if required_name.endswith('_'):
                            if not any(name.startswith(encoded) for name in exported_names):
                                missing_names.append(required_name + '*')
                        elif encoded not in exported_names:
                            missing_names.append(required_name)
                    if missing_names:
                        problems.append('%s (missing multipart bodies: %s)' %
                                        (relative, ', '.join(missing_names)))
                    colours = [match.decode('ascii') for match in re.findall(
                        rb'#[0-9A-Fa-f]{8}', model_xml)]
                    rgb = [tuple(int(colour[index:index + 2], 16)
                                 for index in (1, 3, 5))
                           for colour in colours]
                    has_black = any(max(colour) <= 50 for colour in rgb)
                    has_white = any(min(colour) >= 220 for colour in rgb)
                    if not has_black or not has_white:
                        problems.append('%s (missing black-shell or white-inlay colour)' %
                                        relative)
            except zipfile.BadZipFile:
                problems.append('%s (invalid 3MF ZIP container)' % relative)
        elif source.suffix.lower() == '.step':
            with source.open('rb') as stream:
                header = stream.read(256)
            if b'ISO-10303-21' not in header:
                problems.append('%s (invalid STEP header)' % relative)
    if problems:
        raise RuntimeError('Staged artifact validation failed: %s' %
                           '; '.join(problems))


def promote_staged_exports(staged, backup_directory):
    """Promote a complete export set, restoring prior files if promotion fails."""
    backups = {}
    promoted = []
    try:
        for source, destination, relative in staged:
            destination.parent.mkdir(parents=True, exist_ok=True)
            backup = backup_directory / relative
            if destination.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup)
                backups[relative] = backup
            source.replace(destination)
            promoted.append((destination, relative))
    except Exception as original_error:
        rollback_errors = []
        for destination, relative in reversed(promoted):
            try:
                backup = backups.get(relative)
                if backup is not None and backup.exists():
                    backup.replace(destination)
                elif destination.exists():
                    destination.unlink()
            except Exception as rollback_error:
                rollback_errors.append('%s: %s' % (relative, rollback_error))
        if rollback_errors:
            raise RuntimeError(
                'Artifact promotion failed (%s); rollback also failed for %s' %
                (original_error, '; '.join(rollback_errors))
            ) from original_error
        raise


def run(_context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError('Open the parametric Fusion release design first.')
    if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise RuntimeError('The release design must use parametric history.')

    validate_manifest()
    definitions = component_definitions(design)
    bodies = release_checks(design, definitions)
    manager = design.exportManager
    written = []
    with tempfile.TemporaryDirectory(
            prefix='.tmp-fusion-export-', dir=str(REPOSITORY_ROOT)) as temporary:
        staging_root = Path(temporary) / 'staged'
        backup_root = Path(temporary) / 'backup'
        staged = []
        for kind, name, filename in PRINT_ARTIFACTS:
            destination = THREEMF_DIRECTORY / filename
            relative = destination.relative_to(REPOSITORY_ROOT).as_posix()
            source = staging_root / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            if kind == 'component':
                with direct_body_export_component(design, definitions[name]) as export_component:
                    export_3mf(manager, export_component, source)
            else:
                export_3mf(manager, bodies[name], source)
            staged.append((source, destination, relative))
            written.append(relative)
        for kind, name, filename in STEP_ARTIFACTS:
            destination = STEP_DIRECTORY / filename
            relative = destination.relative_to(REPOSITORY_ROOT).as_posix()
            source = staging_root / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            if kind == 'component':
                with direct_body_export_component(design, definitions[name]) as export_component:
                    export_step(manager, export_component, source)
            else:
                export_step(manager, bodies[name], source)
            staged.append((source, destination, relative))
            written.append(relative)

        validate_staged_exports(staged)

        promote_staged_exports(staged, backup_root)

    message = 'Exported %d release artifacts:\n%s' % (
        len(written), '\n'.join(written))
    print(message)
    app.userInterface.messageBox(message, 'ARCI release export complete')


def stop(_context):
    pass
