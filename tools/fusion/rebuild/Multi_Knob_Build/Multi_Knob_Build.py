"""Parametric MULTI knob (left encoder) for the ARCI enclosure front panel.

Run inside Fusion 360 via the MCP script runner on the Rev3 master. Builds
KNOB_MULTI as a child of FRONT_HALF, fitting a neutral 12 mm encoder reference
at the (-106, -22) control position, whose panel legend reads MULTI.

Geometry: a cylinder standing off the panel by multiKnobGap, carrying a diamond
knurl band, a chamfered front bezel, a shallow face recess with an indicator
dimple, a rear counterbore clearing the bushing nut, a D-shaped shaft bore and a
radial grub screw pilot.

Orientation trap: the front panel body occupies Y 0..+30 mm and the exterior is
the -Y direction, so every outward feature extrudes negative. Y=0 is both the
panel's outer face and the control sketch plane, so a sketch at Y=0 is not
evidence that +Y is outward. Getting this backwards buries the knob in the case.

Build-order traps, all of them learned the hard way:
  * Knurl the bare cylinder first. Sweeps fail once the bores exist.
  * Never sketch on a face. sketches.add(face) auto-projects that face's edges,
    so a lone circle on a counterbored face yields several profiles and
    profiles.item(0) is often the annulus, not the disc. The cut then removes a
    ring and leaves a central pillar, and nothing reports an error. Sketch on an
    explicit construction plane and select the profile by area.
  * constructionAxes.add() raises "Environment is not supported" when scripting
    into a non-active component, so the circular pattern uses the sweep path
    sketch line as its axis.
  * Plane.normal on a planar face is not guaranteed to be the outward normal,
    so the bezel chamfer picks its face by abs(normal.y) plus area, then by
    centroid.y, not by the sign of the normal.

Every sketch is fully constrained and every dimension is driven by a multi*
parameter, so multiKnobD alone resizes the knob, its knurl and its grub pilot
together. Note that multiBezelChamfer must stay below
(multiKnobD - multiFaceRecessD)/2, or the chamfer overruns the face recess.

Entry point: run(context).
"""
import adsk.core, adsk.fusion, math

P = adsk.core.Point3D.create
VS = adsk.core.ValueInput.createByString
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
POS = adsk.fusion.ExtentDirections.PositiveExtentDirection
HOR = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
VER = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation

COMPONENT = 'KNOB_MULTI'

# name, expression, unit, comment
PARAMS = [
    ('multiCenterX', 'encLeftX', 'mm', 'MULTI control centre X (shared with panel cutout)'),
    ('multiCenterZ', '-22 mm', 'mm', 'MULTI control centre Z'),
    ('multiKnobD', '20 mm', 'mm', 'Knob outside diameter (max ~27.8 before connector clearance clash)'),
    ('multiKnobL', '14 mm', 'mm', 'Knob length along -Y'),
    ('multiKnobGap', '1 mm', 'mm', 'Gap between panel face and knob rear'),
    ('multiBezelChamfer', '1.2 mm', 'mm', 'Front edge chamfer; keep below (multiKnobD - multiFaceRecessD)/2'),
    ('multiFaceRecessD', '18 mm', 'mm', 'Front face recess diameter'),
    ('multiFaceRecessDepth', '0.4 mm', 'mm', 'Front face recess depth'),
    ('multiDimpleD', '5 mm', 'mm', 'Indicator dimple diameter'),
    ('multiDimpleDepth', '2 mm', 'mm', 'Indicator dimple depth'),
    ('multiDimpleOffset', '6 mm', 'mm', 'Dimple centre radius from knob axis'),
    ('multiKnurlTeeth', '52', '', 'Knurl tooth count'),
    ('multiKnurlDepth', '0.4 mm', 'mm', 'Knurl groove depth'),
    ('multiKnurlH', '11 mm', 'mm', 'Knurl band height'),
    ('multiKnurlHelixDeg', '30 deg', 'deg', 'Knurl helix angle'),
    ('multiKnurlOverhang', '0.3 mm', 'mm', 'Knurl V base radial overhang past the knob surface'),
    ('multiKnurlInset', '1.0 mm', 'mm', 'Axial inset of the knurl band from the knob rear'),
    ('multiShaftBoreD', '6.15 mm', 'mm', 'D-shaft bore diameter (6 mm reference shaft)'),
    ('multiShaftFlatOffset', '1.55 mm', 'mm', 'D-shaft flat offset from axis'),
    ('multiShaftBoreDepth', '13.3 mm', 'mm', 'Blind shaft-bore depth for the 15 mm PEC11R shaft; leaves a 0.3 mm face wall'),
    ('multiBushingBoreD', '12 mm', 'mm', 'Rear counterbore to clear bushing nut'),
    ('multiBushingBoreDepth', '3 mm', 'mm', 'Rear counterbore depth'),
    ('multiGrubPilotD', '2.5 mm', 'mm', 'Radial grub screw pilot diameter'),
    ('multiGrubY', '5 mm', 'mm', 'Grub screw axis height above knob rear'),
    ('multiGrubStandoff', '1.0 mm', 'mm', 'Grub pilot cut start, outboard of the knob surface'),
    # derived: helix arc length over the band, divided by the knob radius
    ('multiKnurlTwist',
     '( multiKnurlH * tan(multiKnurlHelixDeg) / ( multiKnobD / 2 ) ) * 1 rad',
     'deg', 'Knurl sweep twist angle'),
]


def cm(value):
    return value / 10.0


def collection(items):
    coll = adsk.core.ObjectCollection.create()
    for item in items:
        coll.add(item)
    return coll


def ensure_params(design):
    """Create any missing multi* parameter. Existing values are left alone."""
    have = set(p.name for p in design.userParameters)
    for name, expr, unit, comment in PARAMS:
        if name not in have:
            design.userParameters.add(name, VS(expr), unit, comment)


def val(design, name):
    """Parameter value in mm."""
    return design.userParameters.itemByName(name).value * 10.0


def plane(comp, base, expr, name):
    plane_input = comp.constructionPlanes.createInput()
    plane_input.setByOffset(base, VS(expr))
    result = comp.constructionPlanes.add(plane_input)
    result.name = name
    return result


def sketch_on(comp, reference, name):
    sketch = comp.sketches.add(reference)
    sketch.name = name
    return sketch


def pick(sketch, want_mm2):
    """Select a profile by area. Never trust profiles.item(0)."""
    best, best_delta = None, 1e12
    for index in range(sketch.profiles.count):
        profile = sketch.profiles.item(index)
        delta = abs(profile.areaProperties().area * 100.0 - want_mm2)
        if delta < best_delta:
            best, best_delta = profile, delta
    return best


def dim_to_origin(sketch, point, horizontal, expression):
    """Distance dimension from the sketch origin, driven by an expression.

    Distance dimensions are unsigned, so a point at a negative model coordinate
    needs a negated expression (-multiCenterX rather than multiCenterX).
    """
    geom = point.geometry
    dimension = sketch.sketchDimensions.addDistanceDimension(
        sketch.originPoint, point, HOR if horizontal else VER,
        P(geom.x - 0.4, geom.y + 0.4, 0))
    dimension.parameter.expression = expression
    return dimension


def diameter_dim(sketch, circle, expression):
    geom = circle.centerSketchPoint.geometry
    dimension = sketch.sketchDimensions.addDiameterDimension(
        circle, P(geom.x + 0.5, geom.y + 0.5, 0))
    dimension.parameter.expression = expression
    return dimension


def extrude(comp, profile, expression, operation, name, participants=None):
    extrude_input = comp.features.extrudeFeatures.createInput(
        collection([profile]), operation)
    extrude_input.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(VS(expression)), POS)
    if participants:
        extrude_input.participantBodies = participants
    feature = comp.features.extrudeFeatures.add(extrude_input)
    feature.name = name
    return feature


def circle_cut(comp, reference, name, centre, diameter, expression,
               feature_name, body, dim_x, dim_y, diameter_expr):
    sketch = sketch_on(comp, reference, name)
    point = sketch.modelToSketchSpace(centre)
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
        point, cm(diameter / 2.0))
    diameter_dim(sketch, circle, diameter_expr)
    dim_to_origin(sketch, circle.centerSketchPoint, True, dim_x)
    dim_to_origin(sketch, circle.centerSketchPoint, False, dim_y)
    return extrude(comp, pick(sketch, math.pi * (diameter / 2.0) ** 2),
                   expression, CUT, feature_name, [body])


def delete_existing(front):
    for index in range(front.component.occurrences.count - 1, -1, -1):
        occurrence = front.component.occurrences.item(index)
        if occurrence.component.name == COMPONENT:
            occurrence.deleteMe()


def run(_context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design or design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise RuntimeError('Open the parametric ARCI Enclosure Rev3 design')

    front = None
    for occurrence in design.rootComponent.occurrences:
        if occurrence.name.startswith('FRONT_HALF'):
            front = occurrence
            break
    if not front:
        raise RuntimeError('FRONT_HALF occurrence was not found')

    ensure_params(design)
    delete_existing(front)

    comp = front.component.occurrences.addNewComponent(
        adsk.core.Matrix3D.create()).component
    comp.name = COMPONENT

    cx = val(design, 'multiCenterX')
    cz = val(design, 'multiCenterZ')
    diameter = val(design, 'multiKnobD')
    gap = val(design, 'multiKnobGap')
    inset = val(design, 'multiKnurlInset')
    teeth = int(round(design.userParameters.itemByName('multiKnurlTeeth').value))
    groove = val(design, 'multiKnurlDepth')
    overhang = val(design, 'multiKnurlOverhang')
    band = val(design, 'multiKnurlH')

    # ---- construction planes, all parameter driven -----------------------
    pl_rear = plane(comp, comp.xZConstructionPlane,
                    '-multiKnobGap', 'PL_MULTI_KNOB_REAR')
    pl_front = plane(comp, comp.xZConstructionPlane,
                     '-( multiKnobGap + multiKnobL )', 'PL_MULTI_KNOB_FRONT')
    pl_knurl = plane(comp, comp.xZConstructionPlane,
                     '-( multiKnobGap + multiKnurlInset )', 'PL_MULTI_KNURL_BACK')
    pl_axis = plane(comp, comp.xYConstructionPlane,
                    'multiCenterZ', 'PL_MULTI_KNOB_AXIS_XY')
    pl_grub = plane(comp, comp.xYConstructionPlane,
                    'multiCenterZ - multiKnobD / 2 - multiGrubStandoff',
                    'PL_MULTI_GRUB')

    # ---- core cylinder ---------------------------------------------------
    sketch = sketch_on(comp, comp.xZConstructionPlane, 'SK_MULTI_KNOB_CORE')
    centre = sketch.modelToSketchSpace(P(cm(cx), 0, cm(cz)))
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
        centre, cm(diameter / 2.0))
    diameter_dim(sketch, circle, 'multiKnobD')
    dim_to_origin(sketch, circle.centerSketchPoint, True, '-multiCenterX')
    dim_to_origin(sketch, circle.centerSketchPoint, False, '-multiCenterZ')
    core = extrude(comp, pick(sketch, math.pi * (diameter / 2.0) ** 2),
                   '-( multiKnobL )', NEW, 'FT_MULTI_KNOB_CORE')
    body = core.bodies.item(0)
    body.name = COMPONENT

    # ---- knurl: twisted V sweep, patterned, both hands cut as a diamond ---
    path_sketch = sketch_on(comp, pl_axis, 'SK_MULTI_KNURL_PATH')
    start = path_sketch.modelToSketchSpace(
        P(cm(cx), cm(-(gap + inset)), cm(cz)))
    end = path_sketch.modelToSketchSpace(
        P(cm(cx), cm(-(gap + inset + band)), cm(cz)))
    path_line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    path_sketch.geometricConstraints.addVertical(path_line)
    dim_to_origin(path_sketch, path_line.startSketchPoint, True, '-multiCenterX')
    dim_to_origin(path_sketch, path_line.startSketchPoint, False,
                  'multiKnobGap + multiKnurlInset')
    path_sketch.sketchDimensions.addDistanceDimension(
        path_line.startSketchPoint, path_line.endSketchPoint, VER,
        P(end.x - 0.4, end.y + 0.4, 0)).parameter.expression = 'multiKnurlH'

    profile_sketch = sketch_on(comp, pl_knurl, 'SK_MULTI_KNURL_PROFILE')
    half = math.pi / teeth
    band_y = -(gap + inset)
    outer = diameter / 2.0 + overhang
    apex = profile_sketch.modelToSketchSpace(
        P(cm(cx + diameter / 2.0 - groove), cm(band_y), cm(cz)))
    base_a = profile_sketch.modelToSketchSpace(
        P(cm(cx + outer * math.cos(half)), cm(band_y),
          cm(cz + outer * math.sin(half))))
    base_b = profile_sketch.modelToSketchSpace(
        P(cm(cx + outer * math.cos(half)), cm(band_y),
          cm(cz - outer * math.sin(half))))
    lines = profile_sketch.sketchCurves.sketchLines
    line_a = lines.addByTwoPoints(apex, base_a)
    line_b = lines.addByTwoPoints(line_a.endSketchPoint, base_b)
    lines.addByTwoPoints(line_b.endSketchPoint, line_a.startSketchPoint)
    radius_expr = '( multiKnobD / 2 + multiKnurlOverhang )'
    cos_expr = 'cos( 180 deg / multiKnurlTeeth )'
    sin_expr = 'sin( 180 deg / multiKnurlTeeth )'
    dim_to_origin(profile_sketch, line_a.startSketchPoint, True,
                  '-( multiCenterX + multiKnobD / 2 - multiKnurlDepth )')
    dim_to_origin(profile_sketch, line_a.startSketchPoint, False, '-multiCenterZ')
    for point, sign in ((line_a.endSketchPoint, '+'), (line_b.endSketchPoint, '-')):
        dim_to_origin(profile_sketch, point, True,
                      '-( multiCenterX + %s * %s )' % (radius_expr, cos_expr))
        dim_to_origin(profile_sketch, point, False,
                      '-( multiCenterZ %s %s * %s )' % (sign, radius_expr, sin_expr))

    tools = []
    for label, twist in (('RH', 'multiKnurlTwist'), ('LH', '-multiKnurlTwist')):
        sweep_input = comp.features.sweepFeatures.createInput(
            profile_sketch.profiles.item(0),
            comp.features.createPath(path_line, False), NEW)
        sweep_input.twistAngle = VS(twist)
        sweep = comp.features.sweepFeatures.add(sweep_input)
        sweep.name = 'FT_MULTI_KNURL_' + label
        tool = sweep.bodies.item(0)
        # constructionAxes.add() is unavailable here; the path line is the axis
        pattern_input = comp.features.circularPatternFeatures.createInput(
            collection([tool]), path_line)
        pattern_input.quantity = VS('multiKnurlTeeth')
        pattern_input.totalAngle = VS('360 deg')
        pattern_input.isSymmetric = False
        pattern = comp.features.circularPatternFeatures.add(pattern_input)
        pattern.name = 'FT_MULTI_KNURL_%s_PATTERN' % label
        tools.append(tool)
        for index in range(pattern.bodies.count):
            tools.append(pattern.bodies.item(index))

    combine_input = comp.features.combineFeatures.createInput(
        body, collection(tools))
    combine_input.operation = CUT
    combine_input.isKeepToolBodies = False
    comp.features.combineFeatures.add(
        combine_input).name = 'FT_MULTI_KNURL_DIAMOND'

    # ---- bezel chamfer on the outermost front face -----------------------
    face = None
    for candidate in body.faces:
        geom = candidate.geometry
        if not isinstance(geom, adsk.core.Plane):
            continue
        # abs(): Plane.normal is not reliably the outward normal
        if abs(geom.normal.y) > 0.99 and candidate.area * 100.0 > 3.0:
            if face is None or candidate.centroid.y < face.centroid.y:
                face = candidate
    if face is None:
        raise RuntimeError('Could not identify the knob front face to chamfer')
    chamfer_input = comp.features.chamferFeatures.createInput2()
    chamfer_input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        collection(list(face.edges)), VS('multiBezelChamfer'), True)
    comp.features.chamferFeatures.add(
        chamfer_input).name = 'FT_MULTI_KNOB_BEZEL_CHAMFER'

    # ---- face recess, indicator dimple, rear counterbore ------------------
    circle_cut(comp, pl_front, 'SK_MULTI_KNOB_FACE',
               P(cm(cx), 0, cm(cz)), val(design, 'multiFaceRecessD'),
               'multiFaceRecessDepth', 'FT_MULTI_KNOB_FACE_RECESS', body,
               '-multiCenterX', '-multiCenterZ', 'multiFaceRecessD')

    circle_cut(comp, pl_front, 'SK_MULTI_KNOB_DIMPLE',
               P(cm(cx), 0, cm(cz + val(design, 'multiDimpleOffset'))),
               val(design, 'multiDimpleD'),
               'multiFaceRecessDepth + multiDimpleDepth',
               'FT_MULTI_KNOB_DIMPLE', body, '-multiCenterX',
               '-( multiCenterZ + multiDimpleOffset )', 'multiDimpleD')

    circle_cut(comp, pl_rear, 'SK_MULTI_KNOB_BUSHING_BORE',
               P(cm(cx), 0, cm(cz)), val(design, 'multiBushingBoreD'),
               '-( multiBushingBoreDepth )', 'FT_MULTI_KNOB_BUSHING_BORE', body,
               '-multiCenterX', '-multiCenterZ', 'multiBushingBoreD')

    # ---- D-shaped shaft bore ---------------------------------------------
    radius = val(design, 'multiShaftBoreD') / 2.0
    flat = val(design, 'multiShaftFlatOffset')
    half_chord = math.sqrt(radius * radius - flat * flat)
    sketch = sketch_on(comp, pl_rear, 'SK_MULTI_KNOB_SHAFT_BORE')
    centre = sketch.modelToSketchSpace(P(cm(cx), 0, cm(cz)))
    arc_start = sketch.modelToSketchSpace(
        P(cm(cx - half_chord), 0, cm(cz - flat)))
    arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(
        centre, arc_start, math.pi + 2.0 * math.asin(flat / radius))
    chord = sketch.sketchCurves.sketchLines.addByTwoPoints(
        arc.endSketchPoint, arc.startSketchPoint)
    sketch.sketchDimensions.addRadialDimension(
        arc, P(centre.x + 0.5, centre.y + 0.5, 0)
    ).parameter.expression = 'multiShaftBoreD / 2'
    sketch.geometricConstraints.addHorizontal(chord)
    dim_to_origin(sketch, arc.centerSketchPoint, True, '-multiCenterX')
    dim_to_origin(sketch, arc.centerSketchPoint, False, '-multiCenterZ')
    dim_to_origin(sketch, chord.startSketchPoint, False,
                  '-( multiCenterZ - multiShaftFlatOffset )')
    segment = radius * radius * math.acos(flat / radius) - flat * half_chord
    extrude(comp, pick(sketch, math.pi * radius * radius - segment),
            '-( multiShaftBoreDepth )', CUT, 'FT_MULTI_KNOB_SHAFT_BORE', [body])

    # ---- radial grub screw pilot -----------------------------------------
    circle_cut(comp, pl_grub, 'SK_MULTI_KNOB_GRUB',
               P(cm(cx), cm(-(gap + val(design, 'multiGrubY'))), cm(cz)),
               val(design, 'multiGrubPilotD'),
               'multiKnobD / 2 + multiGrubStandoff',
               'FT_MULTI_KNOB_GRUB_PILOT', body,
               '-multiCenterX', 'multiKnobGap + multiGrubY', 'multiGrubPilotD')

    for appearance in design.appearances:
        if appearance.name == 'PLA (Black)':
            body.appearance = appearance
            break

    loose = [s.name for s in comp.sketches if not s.isFullyConstrained]
    if loose:
        raise RuntimeError('Sketches left unconstrained: ' + ', '.join(loose))

    print('%s built: %.3f mm3, %d faces, %d sketches, all fully constrained' % (
        COMPONENT, body.volume * 1000.0, body.faces.count, comp.sketches.count))
