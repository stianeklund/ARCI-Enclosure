"""Stand fasteners for the ARCI enclosure tilt stand, plus the assembly joints.

Creates real hardware components rather than decorative stand-ins, sized to the
pockets and bores that ``Tilt_Stand_Build.py`` already produces.  One hardware
set is owned by the reusable ``STAND_HINGE`` subassembly, so its second assembly
occurrence automatically carries the matching left-side fasteners:

    HW_M3x12_CSK_SCREW   four off, bracket plate -> rear-wall boss pilots
    HW_M5x30_HEX_BOLT    two off, hinge pivot, DIN 931 (partially threaded)
    HW_M5_WASHER         two off, DIN 125 under the nut
    HW_M5_NYLOC_NUT      two off, DIN 985, with the nylon collar as its own body

Fit notes, all measured off the existing bodies:

  * The hinge is a clevis: bracket ears occupy X 98..102 and 116..120, the pad
    knuckle X 102.6..115.4, bore 5.4 mm, pivot at Y 67.04 / Z -61.
  * The hex pocket is cut into the outer ear, so the bolt head is captive and
    the nut is the part that turns.  That is the whole reason for the pocket:
    one spanner, no second tool holding the head.
  * A DIN 931 M5x30 has a 14 mm plain shank, which spans the full 12.8 mm
    knuckle.  The rotating bore therefore bears on plain shank, never on
    thread, which would otherwise cut into the PLA within a few cycles.
  * The nut is nyloc.  A plain nut on a hinge that is worked by hand backs off,
    and this joint's friction preload is what holds a tilt angle between
    castellation teeth.

``standHexDepth`` is raised from 3 mm to 3.5 mm so a DIN 933/931 M5 head
(3.5 mm high) finishes flush instead of standing 0.5 mm proud.

Threads are not modelled.  Shanks are plain cylinders at nominal major
diameter, which is the normal treatment for assembly hardware; modelled helices
here would cost far more rebuild time than they buy.

Entry point: run(context).  Safe to re-run: it removes its own components and
joints first.
"""

import math
import adsk.core
import adsk.fusion


# Pivot and clevis, mm, right-hand stand.
PIVOT_Y = 67.040
PIVOT_Z = -61.000
EAR_INNER_OUTER_FACE = 98.000    # outboard face of the inner (nut side) ear
EAR_OUTER_OUTER_FACE = 120.000   # outboard face of the outer (head side) ear
HEX_DEPTH = 3.5

# Fasteners, mm.
M5_AF = 8.0
M5_HEAD_H = 3.5
M5_SHANK_D = 5.0
M5_LENGTH = 30.0
M5_PLAIN_SHANK = 14.0
M5_WASHER_OD = 10.0
M5_WASHER_ID = 5.3
M5_WASHER_T = 1.0
M5_NUT_H = 5.0
M5_NYLON_H = 1.2

M3_SCREW_X = 109.0
M3_SCREW_Z = (-38.0, -50.0)
M3_HEAD_FACE_Y = 59.040          # bracket plate outer face
M3_HEAD_D = 5.6
M3_SHANK_D = 3.0
M3_LENGTH = 12.0

HARDWARE = ('HW_M3x12_CSK_SCREW', 'HW_M5x30_HEX_BOLT',
            'HW_M5_WASHER', 'HW_M5_NYLOC_NUT')


def mm(value):
    return value / 10.0


def vi(value):
    return adsk.core.ValueInput.createByString('%.6f mm' % value)


def new_component(root, name):
    matrix = adsk.core.Matrix3D.create()
    occurrence = root.occurrences.addNewComponent(matrix)
    occurrence.component.name = name
    return occurrence


def plane_at_x(comp, x):
    inp = comp.constructionPlanes.createInput()
    inp.setByOffset(comp.yZConstructionPlane, vi(x))
    return comp.constructionPlanes.add(inp)


def plane_at_z(comp, z):
    inp = comp.constructionPlanes.createInput()
    inp.setByOffset(comp.xYConstructionPlane, vi(z))
    return comp.constructionPlanes.add(inp)


def to_sketch(sketch, x, y, z):
    return sketch.modelToSketchSpace(adsk.core.Point3D.create(mm(x), mm(y), mm(z)))


def circle_on(sketch, x, y, z, diameter):
    return sketch.sketchCurves.sketchCircles.addByCenterRadius(
        to_sketch(sketch, x, y, z), mm(diameter / 2.0))


def hexagon_on(sketch, x, y, z, across_flats):
    """Hexagon in a YZ-plane sketch, one flat parallel to Z (spanner on Y)."""
    radius = across_flats / math.sqrt(3.0)
    points = []
    for i in range(6):
        angle = math.radians(30.0 + 60.0 * i)
        points.append(to_sketch(sketch, x,
                                y + radius * math.cos(angle),
                                z + radius * math.sin(angle)))
    lines = sketch.sketchCurves.sketchLines
    return [lines.addByTwoPoints(points[i], points[(i + 1) % 6]) for i in range(6)]


def extrude_profile(comp, profile, distance, operation, name, participants=None):
    features = comp.features.extrudeFeatures
    inp = features.createInput(profile, operation)
    inp.setDistanceExtent(False, vi(distance))
    if participants is not None:
        inp.participantBodies = participants
    feature = features.add(inp)
    feature.name = name
    return feature


def outer_profile(sketch):
    """Largest-area profile, i.e. the outline rather than an inner ring."""
    best, best_area = None, -1.0
    for i in range(sketch.profiles.count):
        profile = sketch.profiles.item(i)
        area = profile.areaProperties(
            adsk.fusion.CalculationAccuracy.LowCalculationAccuracy).area
        if area > best_area:
            best, best_area = profile, area
    return best


def ring_profile(sketch):
    """The annular profile.

    Two concentric closed curves give Fusion three profiles: the inner disc,
    the annulus, and (depending on the sketch) the whole outline.  Only the
    annulus has two loops, so select on loop count rather than on area.
    """
    for i in range(sketch.profiles.count):
        profile = sketch.profiles.item(i)
        if profile.profileLoops.count == 2:
            return profile
    raise RuntimeError('%s: no annular profile' % sketch.name)


def build_hex_bolt(root):
    """DIN 931 M5x30: hex head captive in the outer-ear pocket, plain shank
    through the knuckle, thread only where the nut runs."""
    occurrence = new_component(root, 'HW_M5x30_HEX_BOLT')
    comp = occurrence.component
    head_seat = EAR_OUTER_OUTER_FACE - HEX_DEPTH

    sketch = comp.sketches.add(plane_at_x(comp, head_seat))
    sketch.name = 'SK_BOLT_HEAD'
    hexagon_on(sketch, head_seat, PIVOT_Y, PIVOT_Z, M5_AF)
    head = extrude_profile(comp, sketch.profiles.item(0), HEX_DEPTH,
                           adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                           'FT_BOLT_HEAD')
    body = head.bodies.item(0)
    body.name = 'M5x30_HEX_BOLT'

    sketch = comp.sketches.add(plane_at_x(comp, head_seat))
    sketch.name = 'SK_BOLT_SHANK'
    circle_on(sketch, head_seat, PIVOT_Y, PIVOT_Z, M5_SHANK_D)
    extrude_profile(comp, sketch.profiles.item(0), -M5_LENGTH,
                    adsk.fusion.FeatureOperations.JoinFeatureOperation,
                    'FT_BOLT_SHANK', [body])

    for sk in comp.sketches:
        sk.isVisible = False
    thread_start = head_seat - M5_PLAIN_SHANK
    print('bolt: head %.2f..%.2f  plain shank to %.2f  tip %.2f'
          % (head_seat, EAR_OUTER_OUTER_FACE, thread_start, head_seat - M5_LENGTH))
    return occurrence


def build_washer(root):
    occurrence = new_component(root, 'HW_M5_WASHER')
    comp = occurrence.component
    sketch = comp.sketches.add(plane_at_x(comp, EAR_INNER_OUTER_FACE))
    sketch.name = 'SK_WASHER'
    circle_on(sketch, EAR_INNER_OUTER_FACE, PIVOT_Y, PIVOT_Z, M5_WASHER_OD)
    circle_on(sketch, EAR_INNER_OUTER_FACE, PIVOT_Y, PIVOT_Z, M5_WASHER_ID)
    feature = extrude_profile(comp, ring_profile(sketch), -M5_WASHER_T,
                              adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                              'FT_WASHER')
    feature.bodies.item(0).name = 'M5_WASHER'
    for sk in comp.sketches:
        sk.isVisible = False
    return occurrence


def build_nyloc_nut(root):
    """DIN 985: hex body plus a separate nylon collar body so the insert can
    carry its own appearance in the assembly."""
    occurrence = new_component(root, 'HW_M5_NYLOC_NUT')
    comp = occurrence.component
    face = EAR_INNER_OUTER_FACE - M5_WASHER_T          # 97.0, washer back face
    steel_h = M5_NUT_H - M5_NYLON_H

    sketch = comp.sketches.add(plane_at_x(comp, face))
    sketch.name = 'SK_NUT_BODY'
    hexagon_on(sketch, face, PIVOT_Y, PIVOT_Z, M5_AF)
    circle_on(sketch, face, PIVOT_Y, PIVOT_Z, M5_SHANK_D)
    nut = extrude_profile(comp, ring_profile(sketch), -steel_h,
                          adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                          'FT_NUT_BODY')
    nut.bodies.item(0).name = 'M5_NYLOC_NUT'

    collar_face = face - steel_h
    sketch = comp.sketches.add(plane_at_x(comp, collar_face))
    sketch.name = 'SK_NUT_NYLON_COLLAR'
    hexagon_on(sketch, collar_face, PIVOT_Y, PIVOT_Z, M5_AF)
    circle_on(sketch, collar_face, PIVOT_Y, PIVOT_Z, M5_SHANK_D)
    collar = extrude_profile(comp, ring_profile(sketch), -M5_NYLON_H,
                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                             'FT_NUT_NYLON_COLLAR')
    collar.bodies.item(0).name = 'M5_NYLON_COLLAR'
    for sk in comp.sketches:
        sk.isVisible = False
    return occurrence


def build_csk_screw(root):
    """DIN 965 M3x12, revolved from its half section about the screw axis."""
    occurrence = new_component(root, 'HW_M3x12_CSK_SCREW')
    comp = occurrence.component
    z = M3_SCREW_Z[0]
    sketch = comp.sketches.add(plane_at_z(comp, z))
    sketch.name = 'SK_SCREW_SECTION'

    head_top = M3_HEAD_FACE_Y
    cone_base = head_top - (M3_HEAD_D - M3_SHANK_D) / 2.0
    tip = head_top - M3_LENGTH
    axis_x = M3_SCREW_X

    def pt(x, y):
        return to_sketch(sketch, x, y, z)

    lines = sketch.sketchCurves.sketchLines
    profile = [
        (axis_x, head_top),
        (axis_x + M3_HEAD_D / 2.0, head_top),
        (axis_x + M3_SHANK_D / 2.0, cone_base),
        (axis_x + M3_SHANK_D / 2.0, tip),
        (axis_x, tip),
    ]
    for i in range(len(profile)):
        a, b = profile[i], profile[(i + 1) % len(profile)]
        lines.addByTwoPoints(pt(a[0], a[1]), pt(b[0], b[1]))
    axis = lines.addByTwoPoints(pt(axis_x, head_top + 4.0), pt(axis_x, tip - 4.0))
    axis.isConstruction = True

    revolves = comp.features.revolveFeatures
    inp = revolves.createInput(
        sketch.profiles.item(0), axis,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inp.setAngleExtent(False, adsk.core.ValueInput.createByString('360 deg'))
    feature = revolves.add(inp)
    feature.name = 'FT_SCREW_REVOLVE'
    feature.bodies.item(0).name = 'M3x12_CSK_SCREW'
    for sk in comp.sketches:
        sk.isVisible = False
    return occurrence


def copy_at(root, occurrence, dx=0.0, dz=0.0):
    matrix = adsk.core.Matrix3D.create()
    matrix.translation = adsk.core.Vector3D.create(mm(dx), 0, mm(dz))
    return root.occurrences.addExistingComponent(occurrence.component, matrix)


def bore_face(occurrence, diameter, axis='x'):
    """Cylindrical face of the given diameter, used as joint geometry."""
    for body in occurrence.bRepBodies:
        for face in body.faces:
            geom = face.geometry
            if not isinstance(geom, adsk.core.Cylinder):
                continue
            direction = getattr(geom.axis, axis)
            if abs(abs(direction) - 1) > 1e-6:
                continue
            if abs(geom.radius * 20 - diameter) < 0.01:
                return face
    return None


def rigid_joint(root, moving, base, name):
    joints = root.asBuiltJoints
    inp = joints.createInput(moving, base, None)
    inp.setAsRigidJointMotion()
    joint = joints.add(inp)
    joint.name = name
    return joint


def revolute_joint(root, moving, base, axis_face, name):
    """As-built revolute about the hinge bore.

    As-built is deliberate: every occurrence is already in its correct place,
    and an as-built joint captures that pose instead of snapping parts to a
    new one, which is what a normal joint would do to an assembly this size.
    """
    joints = root.asBuiltJoints
    geometry = adsk.fusion.JointGeometry.createByNonPlanarFace(
        axis_face, adsk.fusion.JointKeyPointTypes.MiddleKeyPoint)
    inp = joints.createInput(moving, base, geometry)
    # Joint directions are local to the joint geometry, not to the model: a
    # cylindrical face puts its axis on the joint frame's Z, so XAxisJointDirection
    # would spin the pad about the wrong axis entirely.
    inp.setAsRevoluteJointMotion(
        adsk.fusion.JointDirections.ZAxisJointDirection)
    joint = joints.add(inp)
    joint.name = name
    return joint


def stow_direction(joint, occurrence):
    """Which way folds the pad up against the enclosure.

    Fusion measures a revolute joint from its as-built pose, so 0 deg is the
    deployed position; the sign of the useful travel depends on which ear the
    axis face came from and is cheaper to measure than to reason about.

    The test is the pad's lowest point.  Both directions raise its highest
    point -- the pad ends up vertical either way -- so only the low edge
    distinguishes folding up against the enclosure from swinging down through
    the desk.
    """
    motion = joint.jointMotion
    rest = occurrence.boundingBox.minPoint.z
    motion.rotationValue = math.radians(20.0)
    adsk.doEvents()
    lifted = occurrence.boundingBox.minPoint.z
    motion.rotationValue = 0.0
    adsk.doEvents()
    return 1.0 if lifted > rest else -1.0


def build_joints(root, stand_occurrence, hinge, fasteners, screws):
    """Mount the stand assembly to the enclosure and articulate each hinge.

    The fastener occurrences are passed in rather than looked up by name:
    occurrences created earlier in the same script are not yet resolvable
    through ``occurrences.itemByName``.
    """
    def occ(parent, name):
        found = parent.occurrences.itemByName(name)
        if not found:
            raise RuntimeError('missing occurrence %s' % name)
        return found

    back = occ(root, 'BACK_HALF:1')
    back.isGrounded = True

    made = [rigid_joint(root, stand_occurrence, back,
                        'J_STAND_ASSEMBLY_TO_BACK')]
    bracket = occ(hinge, 'STAND_BRACKET:1')
    pad = occ(hinge, 'STAND_PAD:1')
    bracket.isGroundToParent = True

    axis_face = bore_face(bracket, 14.0, 'x')
    if axis_face is None:
        raise RuntimeError('no hinge barrel face on STAND_BRACKET:1')
    joint = revolute_joint(hinge, pad, bracket, axis_face, 'J_STAND_HINGE')
    sign = stow_direction(joint, pad)
    limits = joint.jointMotion.rotationLimits
    low, high = sorted((0.0, sign * math.radians(90.0)))
    limits.isMinimumValueEnabled = True
    limits.minimumValue = low
    limits.isMaximumValueEnabled = True
    limits.maximumValue = high
    limits.isRestValueEnabled = True
    limits.restValue = 0.0
    made.append(joint)
    print('J_STAND_HINGE travel %.0f..%.0f deg, rest 0 (deployed)'
          % (math.degrees(low), math.degrees(high)))

    # Fasteners ride with the fixed bracket.  Because STAND_HINGE is reused,
    # these five occurrences and joints appear correctly on both sides.
    for index, fastener in enumerate(fasteners + screws, 1):
        made.append(rigid_joint(
            hinge, fastener, bracket,
            'J_HW_%s_%d' % (fastener.component.name[3:], index)))
    return made


def is_hardware(name):
    """Match this script's own components.

    Deleting a component does not release its name straight away, so a re-run
    can come back as ``HW_M5_WASHER (1)``.  Prefix matching catches those and
    the rename below puts the plain names back.
    """
    return any(name == base or name.startswith(base + ' ') for base in HARDWARE)


def clear_previous(des, root, hinge):
    for group in list(des.timeline.timelineGroups):
        if group.name in ('HARDWARE - STAND FASTENERS',
                           'STAND HARDWARE - COMPONENT DEFINITIONS'):
            group.deleteMe(False)
    for parent in (root, hinge):
        for collection in (parent.joints, parent.asBuiltJoints):
            for joint in list(collection):
                if joint.name.startswith('J_STAND') or joint.name.startswith('J_HW'):
                    joint.deleteMe()
    for parent in (root, hinge):
        for occurrence in list(parent.occurrences):
            if is_hardware(occurrence.component.name):
                occurrence.deleteMe()
    back = root.occurrences.itemByName('BACK_HALF:1')
    if back:
        for occurrence in list(back.component.occurrences):
            if is_hardware(occurrence.component.name):
                occurrence.deleteMe()
    for comp in list(des.allComponents):
        if comp != root and is_hardware(comp.name):
            try:
                comp.deleteMe()
            except Exception:
                pass


def normalise_names(des, root):
    """Drop any ``(n)`` suffix Fusion appended while the old name was reserved."""
    for comp in des.allComponents:
        for base in HARDWARE:
            if comp.name != base and comp.name.startswith(base + ' ('):
                comp.name = base
    for joint in root.asBuiltJoints:
        if ' (' in joint.name and joint.name.startswith('J_HW'):
            joint.name = joint.name.split(' (')[0] + joint.name.rsplit(')', 1)[-1]


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    if not des:
        raise RuntimeError('Open a Fusion design before running this script')
    root = des.rootComponent
    stand_occurrence = next(
        (item for item in root.occurrences
         if item.component.name == 'TILT_STAND_ASSEMBLY'), None)
    if not stand_occurrence:
        raise RuntimeError('Run Tilt_Stand_Build.py before the hardware build')
    stand = stand_occurrence.component
    hinge_occurrence = next(
        (item for item in stand.occurrences
         if item.component.name == 'STAND_HINGE'), None)
    if not hinge_occurrence:
        raise RuntimeError('TILT_STAND_ASSEMBLY has no STAND_HINGE component')
    hinge = hinge_occurrence.component

    depth = des.userParameters.itemByName('standHexDepth')
    if depth and abs(depth.value * 10 - HEX_DEPTH) > 1e-6:
        depth.expression = '%.1f mm' % HEX_DEPTH
        depth.comment = 'M5 hex head pocket depth; equals the DIN 931 head height'
        print('standHexDepth -> %.1f mm (head now finishes flush)' % HEX_DEPTH)

    clear_previous(des, root, hinge)
    timeline_start = des.timeline.count

    bolt = build_hex_bolt(hinge)
    washer = build_washer(hinge)
    nut = build_nyloc_nut(hinge)
    screw = build_csk_screw(hinge)

    fasteners = [bolt, washer, nut]
    screw_dz = M3_SCREW_Z[1] - M3_SCREW_Z[0]
    screws = [screw, copy_at(hinge, screw, dz=screw_dz)]

    joints = build_joints(root, stand_occurrence, hinge, fasteners, screws)
    normalise_names(des, root)
    if des.snapshots.hasPendingSnapshot:
        des.snapshots.add()
    timeline_end = des.timeline.count - 1
    if timeline_end >= timeline_start:
        group = des.timeline.timelineGroups.add(timeline_start, timeline_end)
        if group:
            group.name = 'STAND HARDWARE - COMPONENT DEFINITIONS'
            group.isCollapsed = True
    print('joints created:', len(joints))
    placed = [o for o in hinge.occurrences if is_hardware(o.component.name)]
    print('hardware occurrences per hinge:', len(placed))
    for occurrence in placed:
        for body in occurrence.bRepBodies:
            bb = body.boundingBox
            print('  %-24s %-18s x %8.2f..%8.2f  vol %7.2f mm3'
                  % (occurrence.component.name, body.name,
                     bb.minPoint.x * 10, bb.maxPoint.x * 10, body.volume * 1000))


def stop(_context: str):
    pass
