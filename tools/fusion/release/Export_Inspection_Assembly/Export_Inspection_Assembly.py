"""Export a non-printable, project-authored ARCI inspection assembly.

The normal repository exporter writes one printable part at a time. This
companion script instead copies every *native* body occurrence in its installed
assembly position into a temporary component and exports that component as
``cad/assembly/ARCI_ENCLOSURE_INSPECTION.step``. It therefore contains the
enclosure, knobs, button caps, stand, display replica, and project-authored
mechanical/electronics fit geometry for case and accessory design.

Linked-document occurrences are deliberately excluded. This prevents a full
assembly export from redistributing supplier CAD by accident; model a native
fit envelope or replica when that geometry is needed for inspection.

The temporary component is deleted in all cases and this script never saves the
open Fusion document.
"""

from pathlib import Path
import runpy
import tempfile

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
    raise RuntimeError('Could not locate the ARCI repository from the Fusion script path')


REPOSITORY_ROOT = repository_root()
DESTINATION = (REPOSITORY_ROOT / 'cad' / 'assembly' /
               'ARCI_ENCLOSURE_INSPECTION.step')
AUDIT_SCRIPT = (REPOSITORY_ROOT / 'tools' / 'fusion' / 'release' /
                'Fusion_Timeline_Audit' / 'Fusion_Timeline_Audit.py')


def collection_items(collection):
    return [collection.item(index) for index in range(collection.count)]


def native_assembly_bodies(design):
    """Return direct body proxies for every project-authored occurrence.

    ``Occurrence.bRepBodies`` provides bodies in their assembly context. Copying
    those proxies into an identity temporary component retains their installed
    positions, including repeated button-cap instances.
    """
    bodies = []
    excluded = []
    for occurrence in collection_items(design.rootComponent.allOccurrences):
        if occurrence.isReferencedComponent:
            excluded.append(occurrence.fullPathName)
            continue
        for body in collection_items(occurrence.bRepBodies):
            bodies.append((occurrence.fullPathName, body))
    if not bodies:
        raise RuntimeError('No project-authored bodies are available for inspection export.')
    return bodies, sorted(excluded)


def copy_assembly_to_component(design, source_bodies):
    """Create a temporary, flattened component from positioned body proxies."""
    root = design.rootComponent
    occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    component = occurrence.component
    component.name = '__ARCI_INSPECTION_EXPORT__'
    try:
        for path, source_body in source_bodies:
            count = component.bRepBodies.count
            feature = component.features.copyPasteBodies.add(source_body)
            if feature is None or component.bRepBodies.count != count + 1:
                raise RuntimeError('Could not copy %s from %s.' %
                                   (source_body.name, path))
            copied_body = component.bRepBodies.item(count)
            copied_body.name = source_body.name
            if source_body.appearance:
                copied_body.appearance = source_body.appearance
        return occurrence, component
    except Exception:
        if occurrence.isValid:
            occurrence.deleteMe()
        raise


def validate_step(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError('Inspection STEP was not written: %s' % path)
    with path.open('rb') as stream:
        if b'ISO-10303-21' not in stream.read(256):
            raise RuntimeError('Inspection STEP has no ISO-10303-21 header: %s' % path)


def run(_context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError('Open the parametric Fusion release design first.')
    if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise RuntimeError('The inspection design must use parametric history.')

    audit = runpy.run_path(str(AUDIT_SCRIPT))
    result = audit['evaluate'](design)
    failure = audit['gate_error'](result)
    if failure:
        raise RuntimeError(failure)

    source_bodies, excluded = native_assembly_bodies(design)
    temporary_occurrence = None
    with tempfile.TemporaryDirectory(prefix='.tmp-fusion-inspection-',
                                      dir=str(REPOSITORY_ROOT)) as temporary:
        staged = Path(temporary) / DESTINATION.name
        try:
            temporary_occurrence, component = copy_assembly_to_component(
                design, source_bodies)
            options = design.exportManager.createSTEPExportOptions(str(staged), component)
            if not design.exportManager.execute(options):
                raise RuntimeError('Fusion failed to export inspection STEP.')
        finally:
            if temporary_occurrence and temporary_occurrence.isValid:
                temporary_occurrence.deleteMe()
        validate_step(staged)
        DESTINATION.parent.mkdir(parents=True, exist_ok=True)
        staged.replace(DESTINATION)

    message = ('Exported project-authored inspection assembly:\n%s\n\n'
               'Included %d positioned bodies.' % (DESTINATION.relative_to(REPOSITORY_ROOT),
                                                     len(source_bodies)))
    if excluded:
        message += ('\n\nExcluded %d linked occurrence(s):\n%s' %
                    (len(excluded), '\n'.join(excluded)))
    print(message)
    app.userInterface.messageBox(message, 'ARCI inspection assembly export complete')


def stop(_context):
    pass
