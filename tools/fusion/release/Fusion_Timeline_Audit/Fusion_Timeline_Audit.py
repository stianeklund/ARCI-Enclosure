"""Audit the active Fusion design against ARCI's public-release quality gate.

This read-only Fusion script writes Markdown and JSON reports to
``docs/generated``. The export script imports the same gate and refuses to
overwrite public artifacts when the design does not pass.
"""

from pathlib import Path
import json
import traceback

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
REPORT_PATH = REPOSITORY_ROOT / 'docs' / 'generated' / 'fusion_timeline_audit.md'
JSON_REPORT_PATH = REPOSITORY_ROOT / 'docs' / 'generated' / 'fusion_timeline_audit.json'
ERROR_PATH = REPOSITORY_ROOT / 'docs' / 'generated' / 'fusion_timeline_audit.error.txt'
PRINT_MARKERS = ('PRINT', 'AMS', 'INLAY', 'DEBOSS')
TRANSFORM_PREFIXES = ('MOVE_', 'ALIGN_')
TEXT_SKETCH_MARKERS = ('LABEL', 'TEXT', 'INLAY')
ACTIVE_ROOT = '__ARCI_ACTIVE_ROOT__'

# The exact 42 active-master, release-driving sketch baseline. A renamed or
# missing policy target is a gate failure, so no scoped sketch can silently
# fall out of review. Additional active-master unconstrained non-text sketches
# are also blocking until they receive an explicit policy decision.
REQUIRED_FULLY_CONSTRAINED = frozenset((
    (ACTIVE_ROOT, 'SK_DISPLAY_RECESS'),
    ('LED_POWER_GREEN', 'SK_LED_POWER_PROFILE'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNOB_OUTER_BODY'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNURL_PATH_OUTER_RH'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNURL_V_OUTER_RH'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNURL_PATH_OUTER_LH'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNURL_V_OUTER_LH'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNOB_OUTER_TOP_BAND'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNOB_OUTER_RECESS'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNOB_OUTER_RELIEF'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNOB_OUTER_BORE'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNOB_OUTER_PASS'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNOB_OUTER_KEY'),
    ('KNOB_DUAL_OUTER_15', 'SK_KNOB_OUTER_SETSCREW'),
    ('KNOB_DUAL_INNER_11', 'SK_KNOB_INNER_BODY'),
    ('KNOB_DUAL_INNER_11', 'SK_KNURL_PATH_INNER_RH'),
    ('KNOB_DUAL_INNER_11', 'SK_KNURL_V_INNER_RH'),
    ('KNOB_DUAL_INNER_11', 'SK_KNURL_PATH_INNER_LH'),
    ('KNOB_DUAL_INNER_11', 'SK_KNURL_V_INNER_LH'),
    ('KNOB_DUAL_INNER_11', 'SK_KNOB_INNER_NECK'),
    ('KNOB_DUAL_INNER_11', 'SK_KNOB_INNER_TOP_BAND'),
    ('KNOB_DUAL_INNER_11', 'SK_KNOB_INNER_BORE_ROUND'),
    ('KNOB_DUAL_INNER_11', 'SK_KNOB_INNER_BORE_D'),
    ('KNOB_DUAL_INNER_11', 'SK_KNOB_INNER_SETSCREW'),
    ('KNOB_VFO_MAIN', 'SK_VFO_KNURL_PROFILE'),
    ('KNOB_VFO_MAIN', 'SK_VFO_KNURL_PATH'),
    ('KNOB_VFO_MAIN', 'SK_VFO_KNOB_SHAFT_BORE'),
    ('FRONT_HALF', 'SK_FRONT_BUTTON_CUTOUTS'),
    ('FRONT_HALF', 'SK_FRONT_LIP_NOTCHES_TOP'),
    ('FRONT_HALF', 'SK_FRONT_LIP_NOTCHES_BOTTOM'),
    ('FRONT_HALF', 'SK_FRONT_LIP_NOTCHES_RIGHT'),
    ('FRONT_HALF', 'SK_FRONT_LIP_NOTCHES_LEFT'),
    ('FRONT_HALF', 'SK_DISPLAY_WAVESHARE_GLASS_POCKET'),
    ('FRONT_HALF', 'SK_FRONT_ROTARY_RECESSES_DEEP'),
    ('FRONT_HALF', 'SK_FRONT_ROTARY_THROUGH'),
    ('BACK_HALF', 'SK_BACK_PORTS_THROUGH'),
    ('BACK_HALF', 'SK_BACK_DB9_OUTER_RECESS'),
    ('BACK_HALF', 'SK_BACK_DB9_INNER_RECESS'),
    ('BACK_HALF', 'SK_BACK_DETENTS_TOP'),
    ('BACK_HALF', 'SK_BACK_DETENTS_BOTTOM'),
    ('BACK_HALF', 'SK_STAND_BOSSES'),
    ('BACK_HALF', 'SK_STAND_PILOTS'),
))

# Active-master exceptions must be exact pairs with a rationale. Linked-document
# geometry is inventoried separately and cannot become an active-master waiver.
INTENTIONAL_FREE_SKETCHES = {
    (ACTIVE_ROOT, 'SK_CANONICAL_DATUM_POINTS'):
        'Canonical active-root datum-point scaffold; it is a non-driving reference aid.',
    ('LEFT_BUTTON_MATRIX_HARNESS', 'SK_LEFT_MATRIX_RIBBON_PATH'):
        'Reference harness route retained for assembly visualization; it is not a released part.',
    ('8PIN_PANEL_CONNECTOR_REFERENCE', 'SK_GX16_8PIN_CORRECTED_FRONT_PROFILE'):
        'Neutral connector fit envelope retained as a non-driving reference.',
}

RELEASE_COMPONENTS = frozenset((
    'FRONT_HALF', 'BACK_HALF', 'DISPLAY_CARRIER_WAVESHARE_ARCI',
    'TILT_STAND_BRACKET_POS_X', 'TILT_STAND_BRACKET_NEG_X',
    'TILT_STAND_SUPPORT_POS_X', 'TILT_STAND_SUPPORT_NEG_X',
    'KNOB_MULTI', 'KNOB_DUAL_OUTER_15', 'KNOB_DUAL_INNER_11',
    'KNOB_VFO_MAIN', 'KNOB_VFO_GRIP', 'DEV_BUTTON_CAP_MASTER_NATIVE',
    # Retain the clean-rebuild names so transforms cannot escape review while
    # the historical master is migrated to the canonical POS/NEG structure.
    'STAND_BRACKET', 'STAND_PAD',
    'HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA', 'HUB_RETAINER_UPPER',
    'HUB_RETAINER_LOWER', 'HUB_REAR_TRAY',
))
RELEASE_RELEVANT_COMPONENTS = RELEASE_COMPONENTS | frozenset(
    component for component, _ in REQUIRED_FULLY_CONSTRAINED)


def component_definitions(design):
    """Return Fusion's authoritative component-definition collection.

    Do not deduplicate ``root.allOccurrences`` with ``entityToken``: linked or
    native components can expose empty/non-unique tokens, which hides sketches
    from the audit. ``design.allComponents`` is Fusion's definition-level
    collection and therefore avoids repeated occurrences without that loss.
    """
    components = [design.allComponents.item(index)
                  for index in range(design.allComponents.count)]
    root = design.rootComponent
    # Root identity, rather than its mutable visible name, decides whether it
    # is already present. This keeps root-only policy entries unambiguous.
    if not any(component == root for component in components):
        components.insert(0, root)
    return components


def feature_health(component):
    unhealthy = []
    for feature in component.features:
        try:
            healthy = (feature.healthState ==
                       adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState)
        except AttributeError:
            continue
        if not healthy:
            unhealthy.append(feature.name)
    return unhealthy


def timeline_groups(design):
    """Return valid groups, ignoring Fusion's stale deleted-group wrappers.

    Some Fusion builds leave an invalid ``TimelineGroup`` proxy in the
    collection after grouped timeline items are deleted or regenerated. Asking
    that proxy for ``index`` throws ``InternalValidationError: res >= 0`` even
    though every live group remains readable. The proxy has no timeline object
    to audit, so skipping it is equivalent to ignoring an already-deleted
    group; the valid groups still enforce the collapsed-group release policy.
    """
    groups = []
    collection = design.timeline.timelineGroups
    for position in range(collection.count):
        group = collection.item(position)
        try:
            groups.append((group.index, group.name, group.count, group.isCollapsed))
        except RuntimeError:
            continue
    return sorted(groups, key=lambda item: (item[0] < 0, item[0], item[1]))


def is_text_sketch(name):
    return any(marker in (name or '').upper() for marker in TEXT_SKETCH_MARKERS)


def policy_key(root_component, component, sketch_name):
    """Return a stable policy key; the active root never uses its display name."""
    if component == root_component:
        return (ACTIVE_ROOT, sketch_name)
    return (component.name, sketch_name)


def display_policy_key(key):
    component, sketch = key
    return ('ACTIVE_ROOT' if component == ACTIVE_ROOT else component) + ' / ' + sketch


def transform_items(component_records):
    """Separate blocking transforms from recorded reference-only transforms."""
    relevant, reference = [], []
    for record in component_records:
        component = record['component']
        for feature in component.features:
            name = feature.name or ''
            try:
                is_move = feature.objectType.endswith('MoveFeature')
            except AttributeError:
                is_move = False
            if is_move or name.upper().startswith(TRANSFORM_PREFIXES):
                item = '%s / %s' % (component.name, name)
                (relevant if (not record['linked_document'] and
                              component.name in RELEASE_RELEVANT_COMPONENTS)
                 else reference).append(item)
    return sorted(relevant), sorted(reference)


def component_provenance(design, components):
    """Classify component definitions by active-master or linked-doc ownership."""
    occurrences = list(design.rootComponent.allOccurrences)
    records = []
    for component in components:
        paths = []
        for occurrence in occurrences:
            if occurrence.component != component:
                continue
            try:
                visible = occurrence.isLightBulbOn
            except AttributeError:
                visible = None
            paths.append({'path': occurrence.fullPathName,
                          'referenced': occurrence.isReferencedComponent,
                          'visible': visible})
        records.append({
            'component': component,
            'linked_document': bool(paths) and all(item['referenced']
                                                    for item in paths),
            'occurrences': sorted(paths, key=lambda item: item['path']),
        })
    return records


def external_reference_records(component_records):
    """Flatten linked-document provenance for the Markdown/JSON inventory."""
    records = []
    for component_record in component_records:
        if not component_record['linked_document']:
            continue
        for occurrence in component_record['occurrences']:
            records.append({
                'component': component_record['component'].name,
                'path': occurrence['path'],
                'visible': occurrence['visible'],
            })
    return sorted(records, key=lambda item: (item['component'], item['path']))


def collection_items(collection):
    """Read a Fusion collection without assuming it implements iteration."""
    if collection is None:
        return []
    try:
        return [collection.item(index) for index in range(collection.count)]
    except (AttributeError, TypeError):
        try:
            return list(collection)
        except TypeError:
            return []


def same_entity(left, right):
    """Compare Fusion entities without relying on potentially empty tokens."""
    try:
        return left == right
    except (AttributeError, TypeError):
        return False


def sketch_curves(sketch):
    """Return the release curves in a sketch, including construction curves."""
    curves = collection_items(getattr(sketch, 'sketchCurves', None))
    if curves:
        return curves
    # Older Fusion APIs expose typed subcollections but not an aggregate count.
    typed = getattr(sketch, 'sketchCurves', None)
    curves = []
    for name in ('sketchLines', 'sketchArcs', 'sketchCircles', 'sketchEllipses',
                 'sketchFittedSplines', 'sketchControlPointSplines',
                 'sketchConicCurves'):
        curves.extend(collection_items(getattr(typed, name, None)))
    return curves


def curve_owned_points(curves):
    """Return endpoints, centers, and spline points owned by a curve."""
    points = []
    for curve in curves:
        for name in ('startSketchPoint', 'endSketchPoint', 'centerSketchPoint'):
            point = getattr(curve, name, None)
            if point is not None:
                points.append(point)
        for name in ('fitPoints', 'controlPoints'):
            points.extend(collection_items(getattr(curve, name, None)))
    return points


RELATION_ENTITY_ATTRIBUTES = (
    'entity', 'entityOne', 'entityTwo', 'entityThree', 'point', 'pointOne',
    'pointTwo', 'line', 'lineOne', 'lineTwo', 'curve', 'curveOne', 'curveTwo',
    'circle', 'arc', 'entities', 'inputEntities', 'outputEntities',
    'offsetInputEntities', 'offsetOutputEntities', 'offsetResultEntities',
    'resultEntities',
)


def relation_entities(relation):
    """Return known Fusion dimension/constraint entity references."""
    entities = []
    for name in RELATION_ENTITY_ATTRIBUTES:
        value = getattr(relation, name, None)
        if value is None:
            continue
        items = collection_items(value)
        entities.extend(items if items else [value])
    return entities


def is_driving_relation(relation):
    """Reference dimensions are evidence only; geometric constraints drive."""
    return getattr(relation, 'isDriving', True) is not False


def entity_has_driving_relation(entity, relations):
    return any(same_entity(entity, candidate)
               for relation in relations if is_driving_relation(relation)
               for candidate in relation_entities(relation))


def is_reference_backed_curve(curve):
    """Identify projected/reference/linked curves that Fusion drives upstream."""
    return any(getattr(curve, name, False)
               for name in ('isReference', 'isProjected', 'isLinked'))


def is_offset_constraint(relation):
    """Recognize OffsetConstraint without depending on a single API subtype."""
    object_type = getattr(relation, 'objectType', '') or ''
    return 'OffsetConstraint' in object_type or 'offset' in object_type.lower()


def independent_point_roles(sketch, curves, relations):
    """Separate constrained datum helpers from genuinely orphaned points."""
    owned = curve_owned_points(curves)
    origin = getattr(sketch, 'originPoint', None)
    orphans, helpers = [], []
    for point in collection_items(getattr(sketch, 'sketchPoints', None)):
        if origin is not None and same_entity(point, origin):
            continue
        if getattr(point, 'isReference', False):
            continue
        if any(same_entity(point, child) for child in owned):
            continue
        connected = collection_items(getattr(point, 'connectedEntities', None))
        if connected:
            continue
        if entity_has_driving_relation(point, relations):
            helpers.append(point)
        else:
            orphans.append(point)
    return orphans, helpers


def sketch_entity_role(sketch, reference_exception=False):
    """Classify a sketch by curve/entity role, not its aggregate solver flag.

    ``isFullyConstrained`` remains evidence only. Fusion can report it false
    for child handles/endpoints even when every release curve is explicitly
    fixed, so it must never alone fail a locked legacy sketch.
    """
    curves = sketch_curves(sketch)
    fixed_curves = [curve for curve in curves
                    if getattr(curve, 'isFixed', False)]
    dimensions = collection_items(getattr(sketch, 'sketchDimensions', None))
    constraints = collection_items(getattr(sketch, 'geometricConstraints', None))
    relations = dimensions + constraints
    orphans, helper_points = independent_point_roles(sketch, curves, relations)
    driven_curves = [
        curve for curve in curves
        if entity_has_driving_relation(curve, relations) or any(
            entity_has_driving_relation(point, relations)
            for point in curve_owned_points([curve]))
    ]
    reference_curves = [curve for curve in curves if is_reference_backed_curve(curve)]
    offset_related_curves = [
        curve for curve in curves
        if any(is_offset_constraint(relation) and any(
            same_entity(curve, candidate) for candidate in relation_entities(relation))
            for relation in relations)
    ]
    covered_curves = [curve for curve in curves
                      if getattr(curve, 'isFixed', False) or
                      any(same_entity(curve, driven) for driven in driven_curves) or
                      any(same_entity(curve, reference) for reference in reference_curves)]
    aggregate = getattr(sketch, 'isFullyConstrained', None)
    evidence = {
        'sketch_aggregate_fully_constrained': aggregate,
        'release_curve_count': len(curves),
        'fixed_release_curve_count': len(fixed_curves),
        'nonfixed_release_curve_count': len(curves) - len(fixed_curves),
        'dimension_or_geometric_driven_curve_count': len(driven_curves),
        'reference_backed_release_curve_count': len(reference_curves),
        'offset_constraint_related_release_curve_count': len(offset_related_curves),
        'accepted_coverage_release_curve_count': len(covered_curves),
        'aggregate_solver_fallback_used': False,
        'construction_curve_count': sum(
            1 for curve in curves if getattr(curve, 'isConstruction', False)),
        'dimension_count': len(dimensions),
        'geometric_constraint_count': len(constraints),
        'independent_unconnected_point_count': len(orphans),
        'independent_parametric_driving_helper_point_count': len(helper_points),
    }
    if reference_exception:
        role = 'REFERENCE_EXCEPTION'
        detail = 'Exact active-master reference exception.'
    elif orphans:
        role = 'ORPHAN_ENTITY'
        detail = 'Independent, unconnected sketch point(s) require review.'
    elif curves and len(fixed_curves) == len(curves):
        role = 'LOCKED_LEGACY'
        detail = ('All release curves are explicitly fixed. Stable, but replace '
                  'with parametric driving constraints when practical.')
    elif (curves and fixed_curves and len(covered_curves) == len(curves)):
        role = 'HYBRID_DRIVING_LOCKED'
        detail = ('Every release curve is covered by an explicit fix or a driving '
                  'dimension/geometric constraint. Stable, but technical debt.')
    elif (curves and not fixed_curves and len(covered_curves) == len(curves)):
        role = 'PARAMETRIC_DRIVING'
        detail = ('All release curves have accepted dimension/geometric or '
                  'reference-backed driving coverage.')
    elif curves and not fixed_curves and aggregate is True:
        role = 'PARAMETRIC_DRIVING'
        evidence['aggregate_solver_fallback_used'] = True
        detail = ('Fusion\'s aggregate solver proves all degrees of freedom even '
                  'though individual constraint-entity mapping is opaque.')
    else:
        role = 'FREE_DRIVING'
        detail = ('Release curves are not proven fully driven by dimensions/geometric '
                  'constraints.')
    return {'classification': role, 'detail': detail, 'evidence': evidence}


def evaluate(design):
    """Return JSON-serializable gate facts. This does not modify Fusion."""
    components = component_definitions(design)
    component_records = component_provenance(design, components)
    actual_sketches = set()
    policy_matches = {key: 0 for key in REQUIRED_FULLY_CONSTRAINED}
    unhealthy, linked_unhealthy, role_failures, unclassified, approved = [], [], [], [], []
    linked_sketches = []
    required_classifications = []
    for component_record in component_records:
        component = component_record['component']
        component_unhealthy = ['%s / %s' % (component.name, name)
                               for name in feature_health(component)]
        if component_record['linked_document']:
            linked_unhealthy.extend(component_unhealthy)
        else:
            unhealthy.extend(component_unhealthy)
        for sketch in component.sketches:
            if component_record['linked_document']:
                role = sketch_entity_role(sketch)
                linked_sketches.append({
                    'component': component.name,
                    'sketch': sketch.name,
                    'classification': role['classification'],
                    'detail': role['detail'],
                    'evidence': role['evidence'],
                    'occurrences': component_record['occurrences'],
                })
                continue
            key = policy_key(design.rootComponent, component, sketch.name)
            actual_sketches.add(key)
            role = sketch_entity_role(
                sketch, reference_exception=key in INTENTIONAL_FREE_SKETCHES)
            classification = {
                'component': ('ACTIVE_ROOT' if key[0] == ACTIVE_ROOT else component.name),
                'sketch': sketch.name,
                'classification': role['classification'],
                'detail': role['detail'],
                'evidence': role['evidence'],
            }
            if key in REQUIRED_FULLY_CONSTRAINED:
                policy_matches[key] += 1
                required_classifications.append(classification)
                if role['classification'] not in ('PARAMETRIC_DRIVING',
                                                  'LOCKED_LEGACY',
                                                  'HYBRID_DRIVING_LOCKED'):
                    role_failures.append(display_policy_key(key))
            elif key in INTENTIONAL_FREE_SKETCHES:
                classification['reason'] = INTENTIONAL_FREE_SKETCHES[key]
                approved.append(classification)
            elif (not is_text_sketch(sketch.name) and
                  role['classification'] in ('ORPHAN_ENTITY', 'FREE_DRIVING')):
                unclassified.append(display_policy_key(key))

    stale_required = sorted(display_policy_key(key)
                            for key, count in policy_matches.items() if count == 0)
    ambiguous_required = sorted(display_policy_key(key)
                               for key, count in policy_matches.items() if count > 1)
    stale_exemptions = sorted(display_policy_key(key)
                              for key in set(INTENTIONAL_FREE_SKETCHES) - actual_sketches)
    declared_exemptions = [
        {'component': ('ACTIVE_ROOT' if component == ACTIVE_ROOT else component),
         'sketch': sketch, 'reason': reason}
        for (component, sketch), reason in sorted(INTENTIONAL_FREE_SKETCHES.items())
    ]
    relevant_moves, reference_moves = transform_items(component_records)
    groups = timeline_groups(design)
    ungrouped = sorted(design.timeline.item(index).name
                       for index in range(design.timeline.count)
                       if not design.timeline.item(index).isGroup)
    references = external_reference_records(component_records)
    visible_references = [item for item in references if item['visible'] is True]
    advisories = []
    if visible_references:
        advisories.append({
            'code': 'visible_linked_document_occurrences',
            'message': ('Linked-document occurrences are visible. Hide them for a '
                        'focused review, but they are not release-export targets.'),
            'count': len(visible_references),
        })
    checks = {
        'timeline_marker_at_end': design.timeline.markerPosition == design.timeline.count,
        'timeline_has_groups': bool(groups),
        'all_groups_collapsed': all(group[3] for group in groups),
        'no_unhealthy_features': not unhealthy,
        'all_required_sketches_present': not stale_required,
        'required_sketch_policy_is_unambiguous': not ambiguous_required,
        'all_required_sketch_roles_accepted': not role_failures,
        'no_unclassified_unconstrained_sketches': not unclassified,
        'no_stale_exemption_policy_entries': not stale_exemptions,
        'no_release_relevant_move_align_features': not relevant_moves,
    }
    violations = sorted(name for name, passed in checks.items() if not passed)
    return {
        'schema_version': 1,
        'release_gate_clean': not violations,
        'violations': violations,
        'advisories': advisories,
        'checks': checks,
        'summary': {
            'timeline_objects': design.timeline.count,
            'timeline_groups': len(groups),
            'collapsed_timeline_groups': sum(1 for group in groups if group[3]),
            'ungrouped_top_level_items': len(ungrouped),
            'component_definitions': len(components),
            'unhealthy_features': len(unhealthy),
            'linked_document_unhealthy_features': len(linked_unhealthy),
            'active_master_required_role_governed_sketches': len(REQUIRED_FULLY_CONSTRAINED),
            'required_sketch_role_failures': len(role_failures),
            'locked_legacy_required_sketches': sum(
                1 for item in required_classifications
                if item['classification'] == 'LOCKED_LEGACY'),
            'hybrid_driving_locked_required_sketches': sum(
                1 for item in required_classifications
                if item['classification'] == 'HYBRID_DRIVING_LOCKED'),
            'ambiguous_required_policy_entries': len(ambiguous_required),
            'unclassified_unconstrained_sketches': len(unclassified),
            'approved_reference_exceptions': len(approved),
            'release_relevant_move_align_features': len(relevant_moves),
            'external_reference_occurrences': len(references),
            'visible_external_reference_occurrences': len(visible_references),
            'linked_document_component_definitions': sum(
                1 for record in component_records if record['linked_document']),
            'linked_document_sketches': len(linked_sketches),
            'linked_document_unaccepted_sketches': sum(
                1 for sketch in linked_sketches
                if sketch['classification'] in ('ORPHAN_ENTITY', 'FREE_DRIVING')),
        },
        'timeline': {
            'marker_position': design.timeline.markerPosition,
            'count': design.timeline.count,
            'ungrouped_top_level_items': ungrouped,
            'groups': [
                {'index': index, 'name': name, 'count': count,
                 'collapsed': collapsed,
                 'classification': ('print-only' if any(marker in name.upper()
                                                       for marker in PRINT_MARKERS)
                                    else 'mechanical / assembly')}
                for index, name, count, collapsed in groups
            ],
        },
        'findings': {
            'unhealthy_features': sorted(unhealthy),
            'linked_document_unhealthy_features': sorted(linked_unhealthy),
            'required_sketch_role_failures': sorted(role_failures),
            'required_sketch_classifications': sorted(
                required_classifications,
                key=lambda item: (item['component'], item['sketch'])),
            'unclassified_unconstrained_sketches': sorted(unclassified),
            'stale_required_policy_entries': stale_required,
            'ambiguous_required_policy_entries': ambiguous_required,
            'approved_reference_exceptions': sorted(
                approved, key=lambda item: (item['component'], item['sketch'])),
            'declared_intentional_free_sketches': declared_exemptions,
            'stale_exemption_policy_entries': stale_exemptions,
            'release_relevant_move_align_features': relevant_moves,
            'reference_move_align_features': reference_moves,
            'external_references': references,
            'visible_external_references': visible_references,
            'linked_document_sketches': sorted(
                linked_sketches,
                key=lambda item: (item['component'], item['sketch'])),
        },
    }


def _list(lines, values, success):
    if not values:
        lines.append(success)
    for value in values:
        if isinstance(value, dict):
            lines.append('- {component} / {sketch}: {reason}'.format(**value))
        else:
            lines.append('- ' + value)
    lines.append('')


def format_role_record(item):
    """Render compact per-sketch evidence without hiding aggregate state."""
    evidence = item['evidence']
    return ('%(component)s / %(sketch)s — %(classification)s; '
            'aggregate=%(aggregate)s, curves=%(curves)d, fixed=%(fixed)d, '
            'driven-curves=%(driven)d, reference-curves=%(reference)d, '
            'offset-related=%(offset)d, covered-curves=%(covered)d, '
            'aggregate-fallback=%(fallback)s, dimensions=%(dimensions)d, '
            'geometric=%(geometric)d, helpers=%(helpers)d, orphans=%(orphans)d. '
            '%(detail)s' % {
                'component': item['component'],
                'sketch': item['sketch'],
                'classification': item['classification'],
                'aggregate': evidence['sketch_aggregate_fully_constrained'],
                'curves': evidence['release_curve_count'],
                'fixed': evidence['fixed_release_curve_count'],
                'driven': evidence['dimension_or_geometric_driven_curve_count'],
                'reference': evidence['reference_backed_release_curve_count'],
                'offset': evidence['offset_constraint_related_release_curve_count'],
                'covered': evidence['accepted_coverage_release_curve_count'],
                'fallback': evidence['aggregate_solver_fallback_used'],
                'dimensions': evidence['dimension_count'],
                'geometric': evidence['geometric_constraint_count'],
                'helpers': evidence['independent_parametric_driving_helper_point_count'],
                'orphans': evidence['independent_unconnected_point_count'],
                'detail': item['detail'],
            })


def markdown(result):
    summary, checks, findings = (result['summary'], result['checks'],
                                 result['findings'])
    lines = [
        '# Fusion timeline audit', '',
        'Generated by `tools/fusion/release/Fusion_Timeline_Audit/'
        'Fusion_Timeline_Audit.py`; this is a read-only '
        'inspection of the currently open design.', '',
        '## Release gate', '',
        '**%s**' % ('PASS' if result['release_gate_clean'] else 'FAIL'), '',
        '| Check | Result |', '| --- | --- |',
    ]
    for name in sorted(checks):
        lines.append('| %s | %s |' % (name.replace('_', ' '),
                                      'PASS' if checks[name] else 'FAIL'))
    if result['advisories']:
        lines.extend(['', '## Advisories', ''])
        lines.extend('- %(message)s (%(count)d occurrence(s)).' % advisory
                     for advisory in result['advisories'])
        lines.extend(['', '## Release-gate inventory', '',
                      '| Item | Result |', '| --- | --- |'])
    lines.extend([
        '| Timeline objects | %d |' % summary['timeline_objects'],
        '| Timeline groups | %d |' % summary['timeline_groups'],
        '| Collapsed timeline groups | %d |' % summary['collapsed_timeline_groups'],
        '| Ungrouped top-level items | %d |' % summary['ungrouped_top_level_items'],
        '| Component definitions | %d |' % summary['component_definitions'],
        '| Active-master unhealthy features | %d |' % summary['unhealthy_features'],
        '| Linked-document unhealthy features | %d |' % summary['linked_document_unhealthy_features'],
        '| Active-master required role-governed sketches | %d |' % summary['active_master_required_role_governed_sketches'],
        '| Required sketch role failures | %d |' % summary['required_sketch_role_failures'],
        '| Locked legacy technical-debt warnings | %d |' % summary['locked_legacy_required_sketches'],
        '| Hybrid driving/locked technical-debt warnings | %d |' % summary['hybrid_driving_locked_required_sketches'],
        '| Ambiguous required policy entries | %d |' % summary['ambiguous_required_policy_entries'],
        '| Unclassified unconstrained sketches | %d |' % summary['unclassified_unconstrained_sketches'],
        '| Release-relevant Move/Align features | %d |' % summary['release_relevant_move_align_features'],
        '| Visible linked-document occurrences (advisory) | %d |' % summary['visible_external_reference_occurrences'],
        '| Linked-document component definitions | %d |' % summary['linked_document_component_definitions'],
        '| Linked-document sketches | %d |' % summary['linked_document_sketches'],
        '| Linked-document unaccepted sketches | %d |' % summary['linked_document_unaccepted_sketches'],
        '', '## Timeline groups', '',
        '| Timeline index | Group | Items | State | Classification |',
        '| ---: | --- | ---: | --- | --- |',
    ])
    for group in result['timeline']['groups']:
        index = str(group['index']) if group['index'] >= 0 else 'expanded'
        lines.append('| %s | %s | %d | %s | %s |' % (
            index, group['name'], group['count'],
            'collapsed' if group['collapsed'] else 'expanded',
            group['classification']))
    lines.extend(['', '## Findings', ''])
    sections = (
        ('Unhealthy features', findings['unhealthy_features']),
        ('Linked-document unhealthy features (recorded, not gate-blocking)',
         findings['linked_document_unhealthy_features']),
        ('Required sketch classifications', [
            format_role_record(item) for item in findings['required_sketch_classifications']]),
        ('Required sketch role failures', findings['required_sketch_role_failures']),
        ('Locked legacy technical-debt warnings', [
            format_role_record(item) for item in findings['required_sketch_classifications']
            if item['classification'] == 'LOCKED_LEGACY']),
        ('Hybrid driving/locked technical-debt warnings', [
            format_role_record(item) for item in findings['required_sketch_classifications']
            if item['classification'] == 'HYBRID_DRIVING_LOCKED']),
        ('Unconstrained sketches missing policy', findings['unclassified_unconstrained_sketches']),
        ('Stale required-sketch policy entries', findings['stale_required_policy_entries']),
        ('Ambiguous required-sketch policy entries', findings['ambiguous_required_policy_entries']),
        ('Approved reference exceptions', [
            format_role_record(item) + ' Rationale: ' + item['reason']
            for item in findings['approved_reference_exceptions']]),
        ('Declared active-master intentional-free sketches',
         findings['declared_intentional_free_sketches']),
        ('Stale exemption policy entries', findings['stale_exemption_policy_entries']),
        ('Release-relevant Move/Align features', findings['release_relevant_move_align_features']),
        ('Reference-only Move/Align features', findings['reference_move_align_features']),
        ('Visible linked-document references (advisory)', ['%(component)s / %(path)s' % item
                                                           for item in findings['visible_external_references']]),
        ('Linked-document sketch inventory', [
            format_role_record(item) + '; ' + ', '.join(
                    '%s (visible=%s)' % (occurrence['path'], occurrence['visible'])
                    for occurrence in item['occurrences']) or '(no occurrence path)'
            for item in findings['linked_document_sketches']]),
        ('Ungrouped top-level timeline items', result['timeline']['ungrouped_top_level_items']),
    )
    for title, values in sections:
        lines.extend(['### ' + title, ''])
        _list(lines, values, 'None.')
    lines.extend([
        '## Policy', '',
        'The 42 active-master release-driving sketches use an entity-role policy. '
        '`PARAMETRIC_DRIVING` is preferred; `LOCKED_LEGACY` and '
        '`HYBRID_DRIVING_LOCKED` pass with visible technical-debt warnings; '
        '`ORPHAN_ENTITY` and `FREE_DRIVING` fail. Three exact '
        'active-master reference sketches have `REFERENCE_EXCEPTION`; `ACTIVE_ROOT` '
        'identifies Fusion\'s actual root component rather than the mutable document/version '
        'name. Curve-owned endpoints/centers and constrained scaffold points do not create '
        'orphan failures. Linked-document sketches are inventoried with provenance and '
        'visibility. Visible linked occurrences are advisory-only because named public '
        'exports never include them. Stale '
        'policy entries still fail the gate.', '',
        'The JSON companion (`fusion_timeline_audit.json`) is the machine-readable '
        'source for release automation.', '',
    ])
    return '\n'.join(lines)


def write_reports(result):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(markdown(result), encoding='utf-8')
    JSON_REPORT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n',
                                encoding='utf-8')
    if ERROR_PATH.exists():
        ERROR_PATH.unlink()


def gate_error(result):
    if result['release_gate_clean']:
        return None
    return 'Fusion release gate failed: %s. Run Fusion_Timeline_Audit.py for details.' % (
        ', '.join(result['violations']))


def run(_context):
    app = adsk.core.Application.get()
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            raise RuntimeError('Open the parametric Fusion release design first.')
        if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
            raise RuntimeError('The release design must use parametric history.')
        result = evaluate(design)
        write_reports(result)
        print(markdown(result))
        app.userInterface.messageBox(
            'Timeline audit %s. Markdown and JSON written to:\n%s' % (
                'passed' if result['release_gate_clean'] else 'failed', REPORT_PATH),
            'ARCI timeline audit')
    except Exception:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        error = traceback.format_exc()
        ERROR_PATH.write_text(error, encoding='utf-8')
        print(error)
        app.userInterface.messageBox(
            'Audit failed. Error details were written to:\n%s' % ERROR_PATH,
            'ARCI timeline audit failed')


def stop(_context):
    pass
