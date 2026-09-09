"""Native, parametric Fusion 360 rebuild of the ARCI enclosure back half.

The source measurements come from ``cad/reference/legacy/Back.step``. The STEP
is used only as a reference; this script creates editable Fusion sketches and
features.

Canonical coordinate convention:
    X = enclosure width, Y = front-to-back depth, Z = enclosure height.
    Viewed from the exterior front, +X is right and +Z is up.
    The front half occupies Y=0..30 mm.  The back half occupies
    Y=24.04..54.04 mm so the 6.10 mm mating regions overlap.

The legacy/reference coordinate tables used by this script were authored in
the earlier Rev2 frame.  ``model_point`` applies the audited rigid 180-degree
rotation about Y at the single source boundary: (X, Y, Z) -> (-X, Y, -Z).
"""

import math
import adsk.core
import adsk.fusion


def mm(value):
    return value / 10.0


def vi_mm(value):
    if isinstance(value, str):
        return adsk.core.ValueInput.createByString(value)
    return adsk.core.ValueInput.createByString(f'{value} mm')


def add_param(design, name, expression, units='mm', comment=''):
    existing = design.userParameters.itemByName(name)
    if existing:
        return existing
    return design.userParameters.add(
        name, adsk.core.ValueInput.createByString(expression), units, comment
    )


def model_point(x, y, z):
    return adsk.core.Point3D.create(mm(-x), mm(y), mm(-z))


def sketch_point(sketch, x, y, z):
    return sketch.modelToSketchSpace(model_point(x, y, z))


def fix_entities(entities):
    for entity in entities:
        entity.isFixed = True


def centered_rect_xz(sketch, width, height, fixed=False):
    """Centered X/Z rectangle on a sketch whose plane is parallel to XZ."""
    corner = sketch_point(sketch, width / 2.0, 0, height / 2.0)
    lines = sketch.sketchCurves.sketchLines.addCenterPointRectangle(
        sketch_point(sketch, 0, 0, 0), corner
    )
    if fixed:
        fix_entities([lines.item(i) for i in range(lines.count)])
    return lines


def parametric_centered_rect_xz(sketch, width_expr, height_expr, width, height):
    """Fully constrain a centered X/Z rectangle to named parameter expressions."""
    x0, x1 = -width / 2.0, width / 2.0
    z0, z1 = -height / 2.0, height / 2.0
    lines = sketch.sketchCurves.sketchLines
    bottom = lines.addByTwoPoints(
        sketch_point(sketch, x0, 0, z0), sketch_point(sketch, x1, 0, z0))
    right = lines.addByTwoPoints(
        bottom.endSketchPoint, sketch_point(sketch, x1, 0, z1))
    top = lines.addByTwoPoints(
        right.endSketchPoint, sketch_point(sketch, x0, 0, z1))
    left = lines.addByTwoPoints(top.endSketchPoint, bottom.startSketchPoint)
    constraints = sketch.geometricConstraints
    constraints.addHorizontal(bottom)
    constraints.addVertical(right)
    constraints.addHorizontal(top)
    constraints.addVertical(left)
    dims = sketch.sketchDimensions
    width_dim = dims.addDistanceDimension(
        bottom.startSketchPoint, bottom.endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(0, mm(height / 2 + 8), 0))
    width_dim.parameter.expression = width_expr
    height_dim = dims.addDistanceDimension(
        right.startSketchPoint, right.endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(mm(width / 2 + 8), 0, 0))
    height_dim.parameter.expression = height_expr
    half_width = dims.addDistanceDimension(
        sketch.originPoint, bottom.endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(mm(width / 4), mm(height / 2 + 14), 0))
    half_width.parameter.expression = f'{width_expr} / 2'
    half_height = dims.addDistanceDimension(
        sketch.originPoint, bottom.endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(mm(width / 2 + 14), mm(height / 4), 0))
    half_height.parameter.expression = f'{height_expr} / 2'
    return [bottom, right, top, left]


def rect_xz(sketch, cx, cz, width, height, fixed=True):
    x0, x1 = cx - width / 2.0, cx + width / 2.0
    z0, z1 = cz - height / 2.0, cz + height / 2.0
    pts = [
        sketch_point(sketch, x0, 0, z0),
        sketch_point(sketch, x1, 0, z0),
        sketch_point(sketch, x1, 0, z1),
        sketch_point(sketch, x0, 0, z1),
    ]
    lines = sketch.sketchCurves.sketchLines
    result = [lines.addByTwoPoints(pts[i], pts[(i + 1) % 4]) for i in range(4)]
    if fixed:
        fix_entities(result)
    return result


def rounded_rect_xz(sketch, cx, cz, width, height, radius, fixed=True):
    x0, x1 = cx - width / 2.0, cx + width / 2.0
    z0, z1 = cz - height / 2.0, cz + height / 2.0
    r = radius
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    entities = []
    entities.append(lines.addByTwoPoints(
        sketch_point(sketch, x0 + r, 0, z0), sketch_point(sketch, x1 - r, 0, z0)))
    entities.append(arcs.addByThreePoints(
        sketch_point(sketch, x1 - r, 0, z0),
        sketch_point(sketch, x1 - r + r / math.sqrt(2), 0, z0 + r - r / math.sqrt(2)),
        sketch_point(sketch, x1, 0, z0 + r)))
    entities.append(lines.addByTwoPoints(
        sketch_point(sketch, x1, 0, z0 + r), sketch_point(sketch, x1, 0, z1 - r)))
    entities.append(arcs.addByThreePoints(
        sketch_point(sketch, x1, 0, z1 - r),
        sketch_point(sketch, x1 - r + r / math.sqrt(2), 0, z1 - r + r / math.sqrt(2)),
        sketch_point(sketch, x1 - r, 0, z1)))
    entities.append(lines.addByTwoPoints(
        sketch_point(sketch, x1 - r, 0, z1), sketch_point(sketch, x0 + r, 0, z1)))
    entities.append(arcs.addByThreePoints(
        sketch_point(sketch, x0 + r, 0, z1),
        sketch_point(sketch, x0 + r - r / math.sqrt(2), 0, z1 - r + r / math.sqrt(2)),
        sketch_point(sketch, x0, 0, z1 - r)))
    entities.append(lines.addByTwoPoints(
        sketch_point(sketch, x0, 0, z1 - r), sketch_point(sketch, x0, 0, z0 + r)))
    entities.append(arcs.addByThreePoints(
        sketch_point(sketch, x0, 0, z0 + r),
        sketch_point(sketch, x0 + r - r / math.sqrt(2), 0, z0 + r - r / math.sqrt(2)),
        sketch_point(sketch, x0 + r, 0, z0)))
    if fixed:
        fix_entities(entities)
    return entities


def circle_xz(sketch, cx, cz, diameter, fixed=True):
    center = sketch_point(sketch, cx, 0, cz)
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(center, mm(diameter / 2.0))
    if fixed:
        circle.isFixed = True
    return circle


HORIZONTAL_DIM = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
VERTICAL_DIM = adsk.fusion.DimensionOrientations.VerticalDimensionOrientation

# Fusion infers a horizontal/vertical alignment whenever a point being
# dimensioned shares a sketch coordinate with an already-dimensioned point, and
# that inference makes the new dimension redundant
# (VCS_SKETCH_OVER_CONSTRAINTS).  Nudging the geometry off its exact position
# first defeats the inference; the dimensions then pull it back exactly.
INFERENCE_NUDGE = adsk.core.Vector3D.create(0.037, 0.041, 0)


def param_circle_xz(sketch, cx, cz, diameter, x_expr, z_expr, d_expr):
    """Circle driven by |X| and drop-below-centreline parameters."""
    circle = circle_xz(sketch, cx, cz, diameter, fixed=False)
    center = circle.centerSketchPoint
    center.move(INFERENCE_NUDGE)
    point = center.geometry
    dims = sketch.sketchDimensions
    dims.addDiameterDimension(
        circle, adsk.core.Point3D.create(point.x + 1.2, point.y + 1.2, 0)
    ).parameter.expression = d_expr
    dims.addDistanceDimension(
        sketch.originPoint, center, HORIZONTAL_DIM,
        adsk.core.Point3D.create(point.x / 2.0, point.y + 2.2, 0)
    ).parameter.expression = x_expr
    dims.addDistanceDimension(
        sketch.originPoint, center, VERTICAL_DIM,
        adsk.core.Point3D.create(point.x + 2.4, point.y / 2.0, 0)
    ).parameter.expression = z_expr
    return circle


def param_rect_xz(sketch, cx, cz, width, height, x_expr, z_expr, w_expr, h_expr):
    """Centred rectangle driven by |X|, drop, width and height parameters.

    ``rect_xz`` emits four lines that touch but are not joined, so the
    coincidences have to be added before the rectangle can be dimensioned.
    """
    lines = rect_xz(sketch, cx, cz, width, height, fixed=False)
    points = []
    for line in lines:
        points.append(line.startSketchPoint)
        points.append(line.endSketchPoint)
    constraints = sketch.geometricConstraints
    joined = set()
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if i // 2 == j // 2 or i in joined or j in joined:
                continue
            a, b = points[i].geometry, points[j].geometry
            if abs(a.x - b.x) < 1e-7 and abs(a.y - b.y) < 1e-7:
                constraints.addCoincident(points[i], points[j])
                joined.add(j)
    horizontals, verticals = [], []
    for line in lines:
        a, b = line.startSketchPoint.geometry, line.endSketchPoint.geometry
        if abs(a.y - b.y) < 1e-7:
            constraints.addHorizontal(line)
            horizontals.append(line)
        else:
            constraints.addVertical(line)
            verticals.append(line)
    dims = sketch.sketchDimensions
    point = horizontals[0].startSketchPoint.geometry
    dims.addDistanceDimension(
        horizontals[0].startSketchPoint, horizontals[0].endSketchPoint, HORIZONTAL_DIM,
        adsk.core.Point3D.create(point.x, point.y + 1.5, 0)
    ).parameter.expression = w_expr
    point = verticals[0].startSketchPoint.geometry
    dims.addDistanceDimension(
        verticals[0].startSketchPoint, verticals[0].endSketchPoint, VERTICAL_DIM,
        adsk.core.Point3D.create(point.x + 1.5, point.y, 0)
    ).parameter.expression = h_expr
    corner = min(points, key=lambda p: (round(p.geometry.x, 6), round(p.geometry.y, 6)))
    point = corner.geometry
    # ``cx`` is a legacy-frame value, so the sketch sits at -cx: the near corner
    # is inboard of the centre parameter on one side and outboard on the other.
    operator = '-' if -cx > 0 else '+'
    dims.addDistanceDimension(
        sketch.originPoint, corner, HORIZONTAL_DIM,
        adsk.core.Point3D.create(point.x / 2.0, point.y - 2.0, 0)
    ).parameter.expression = '%s %s %s / 2' % (x_expr, operator, w_expr)
    dims.addDistanceDimension(
        sketch.originPoint, corner, VERTICAL_DIM,
        adsk.core.Point3D.create(point.x - 2.0, point.y / 2.0, 0)
    ).parameter.expression = '%s - %s / 2' % (z_expr, h_expr)
    return lines


def all_profiles(sketch):
    collection = adsk.core.ObjectCollection.create()
    for i in range(sketch.profiles.count):
        collection.add(sketch.profiles.item(i))
    if collection.count == 0:
        raise RuntimeError(f'{sketch.name}: no closed profiles')
    return collection


def extrude(comp, profiles, operation, distance, start_offset=None, taper_deg=None,
            name=None, participant_bodies=None):
    features = comp.features.extrudeFeatures
    ext_input = features.createInput(profiles, operation)
    if start_offset is not None:
        ext_input.startExtent = adsk.fusion.OffsetStartDefinition.create(vi_mm(start_offset))
    ext_input.setDistanceExtent(False, vi_mm(distance))
    if taper_deg is not None:
        ext_input.taperAngle = adsk.core.ValueInput.createByString(f'{taper_deg} deg')
    if participant_bodies is not None and operation in (
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            adsk.fusion.FeatureOperations.IntersectFeatureOperation):
        ext_input.participantBodies = participant_bodies
    feature = features.add(ext_input)
    if name:
        feature.name = name
    return feature


def add_combined_outer_setback_fillet(comp, body, start_y, depth, exterior_y, radius):
    """Fillet four depth edges and four exterior-face edges as one setback feature."""
    edges = adsk.core.ObjectCollection.create()
    tolerance = mm(0.02)
    for edge in body.edges:
        box = edge.boundingBox
        lengthwise = (
            abs(box.minPoint.y - mm(start_y)) < tolerance and
            abs(box.maxPoint.y - mm(start_y + depth)) < tolerance
        )
        exterior = (
            abs(box.minPoint.y - mm(exterior_y)) < tolerance and
            abs(box.maxPoint.y - mm(exterior_y)) < tolerance
        )
        if lengthwise or exterior:
            edges.add(edge)
    if edges.count != 8:
        raise RuntimeError(f'Expected 8 combined setback edges, found {edges.count}')
    inp = comp.features.filletFeatures.createInput()
    inp.isRollingBallCorner = False
    inp.addConstantRadiusEdgeSet(edges, vi_mm(radius), True)
    feature = comp.features.filletFeatures.add(inp)
    feature.name = 'FT_BACK_COMBINED_SETBACK_FILLET'
    return feature


def plane_offset(comp, base_plane, offset, name):
    inp = comp.constructionPlanes.createInput()
    inp.setByOffset(base_plane, vi_mm(offset))
    plane = comp.constructionPlanes.add(inp)
    plane.name = name
    return plane


def rect_on_plane(sketch, center, axis_a, axis_b, size_a, size_b):
    """Rectangle supplied in model coordinates on an arbitrary planar sketch."""
    cx, cy, cz = center
    ax, ay, az = axis_a
    bx, by, bz = axis_b
    pts = []
    for sa, sb in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        pts.append(sketch_point(
            sketch,
            cx + sa * ax * size_a / 2 + sb * bx * size_b / 2,
            cy + sa * ay * size_a / 2 + sb * by * size_b / 2,
            cz + sa * az * size_a / 2 + sb * bz * size_b / 2,
        ))
    lines = sketch.sketchCurves.sketchLines
    result = [lines.addByTwoPoints(pts[i], pts[(i + 1) % 4]) for i in range(4)]
    fix_entities(result)
    return result


def fillet_detent_crowns(comp, extrude_feature, long_edge_threshold=5.0):
    edges = adsk.core.ObjectCollection.create()
    for i in range(extrude_feature.endFaces.count):
        face = extrude_feature.endFaces.item(i)
        for edge in face.edges:
            if edge.length > mm(long_edge_threshold):
                edges.add(edge)
    if edges.count != 6:
        raise RuntimeError(f'Expected 6 detent crown edges, found {edges.count}')
    inp = comp.features.filletFeatures.createInput()
    inp.addConstantRadiusEdgeSet(edges, vi_mm(0.4), True)
    feature = comp.features.filletFeatures.add(inp)
    return feature


def add_detent_set(comp, plane, name, centers, axis_a, axis_b, length, width, distance):
    sketch = comp.sketches.add(plane)
    sketch.name = f'SK_BACK_DETENTS_{name}'
    for center in centers:
        rect_on_plane(sketch, center, axis_a, axis_b, length, width)
    feature = extrude(
        comp, all_profiles(sketch), adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        distance, taper_deg=-45, name=f'FT_BACK_DETENTS_{name}'
    )
    crown = fillet_detent_crowns(comp, feature)
    crown.name = f'FT_BACK_DETENT_CROWNS_{name}'
    sketch.isVisible = False
    return feature, crown


def detent_tangent(base_half_width, crown_radius, total_depth):
    """Tangent point for a line from the detent base to its circular crown."""
    a = base_half_width
    r = crown_radius
    c = total_depth - r
    l2 = a * a + c * c
    k = r * math.sqrt(l2 - r * r) / l2
    ty = (r * r / l2) * a + k * c
    td = c - (r * r / l2) * c + k * a
    return ty, td


def add_exact_detent_profile(sketch, wall_axis, wall_coordinate, inward_sign,
                              center_y, base_width, crown_radius, total_depth):
    """Create the exact tangent-line + single cylindrical-crown cross-section."""
    half = base_width / 2.0
    ty, td = detent_tangent(half, crown_radius, total_depth)

    def pt(y, depth):
        coordinate = wall_coordinate + inward_sign * depth
        if wall_axis == 'Z':
            return sketch_point(sketch, 0, y, coordinate)
        return sketch_point(sketch, coordinate, y, 0)

    base_left = pt(center_y - half, 0)
    tangent_left = pt(center_y - ty, td)
    crown = pt(center_y, total_depth)
    tangent_right = pt(center_y + ty, td)
    base_right = pt(center_y + half, 0)
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    entities = [
        lines.addByTwoPoints(base_left, tangent_left),
        arcs.addByThreePoints(tangent_left, crown, tangent_right),
        lines.addByTwoPoints(tangent_right, base_right),
        lines.addByTwoPoints(base_right, base_left),
    ]
    fix_entities(entities)
    return entities


def extrude_profile_at_centers(comp, sketch, centers, length, name):
    profile = sketch.profiles.item(0)
    features = []
    for index, center in enumerate(centers, 1):
        features.append(extrude(
            comp, profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            length, start_offset=center - length / 2.0,
            name=f'FT_BACK_DETENT_{name}_{index:02d}'
        ))
    sketch.isVisible = False
    return features


def transform_ref_point(point):
    """Back.step reference X/Z -> centered Rev2 master X/Z."""
    return 127.0 - point[0], 65.0 - point[1]


def add_db9_profile(sketch):
    # Ordered points from the original native aperture; dimensions are mm.
    A = (122.218139595, 37.248912918)
    B = (133.147962100, 37.248912918)
    Cmid = (134.779382609, 37.871081656)
    C = (135.582216311, 39.421592818)
    D = (136.026520108, 43.321592818)
    Emid = (135.420097159, 45.230333427)
    E = (133.592265897, 46.048912918)
    F = (121.332109462, 46.048912918)
    Gmid = (119.799919783, 45.215082625)
    G = (119.314753830, 43.539525354)
    H = (119.783885384, 39.421592818)
    Imid = (120.586719086, 37.871081656)

    def q(ref):
        x, z = transform_ref_point(ref)
        return sketch_point(sketch, x, 0, z)

    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    entities = [
        lines.addByTwoPoints(q(A), q(B)),
        arcs.addByThreePoints(q(B), q(Cmid), q(C)),
        lines.addByTwoPoints(q(C), q(D)),
        arcs.addByThreePoints(q(D), q(Emid), q(E)),
        lines.addByTwoPoints(q(E), q(F)),
        arcs.addByThreePoints(q(F), q(Gmid), q(G)),
        lines.addByTwoPoints(q(G), q(H)),
        arcs.addByThreePoints(q(H), q(Imid), q(A)),
    ]
    fix_entities(entities)
    return entities


def add_back_labels(sketch):
    labels = [
        # Keep rear legends centered on their connector centerlines.  The
        # shared Z position places them above the openings in exterior view,
        # where installed cables are less likely to obscure them.
        ('WIFI', -88.0000, 10.54),
        ('USB', -36.5426, 10.54),
        ('RS232', -0.6831, 10.54),
        ('COM 0', 35.9169, 10.54),
    ]
    result = adsk.core.ObjectCollection.create()
    for text, cx, cz in labels:
        target = sketch_point(sketch, cx, 0, cz)
        inp = sketch.sketchTexts.createInput(text, mm(4.0), target)
        # Prototype v66 rear legends use this Autodesk face with the native
        # bold text-style flag.  Assigning an arbitrary ``isBold`` attribute
        # does not affect Fusion sketch text.
        inp.fontName = 'Artifakt Element Extra Bold'
        inp.textStyle = adsk.fusion.TextStyles.TextStyleBold
        # Fusion's outward rear-face basis is quarter-turned relative to the
        # enclosure X/Z convention.  Rotate native text into horizontal +Z-up
        # rear-view orientation.
        inp.angle = 3.0 * math.pi / 2.0
        created = sketch.sketchTexts.add(inp)
        # Point text is inserted at a font-dependent anchor.  Re-center from
        # its evaluated bounds so a font update cannot shift connector labels.
        box = created.boundingBox
        current_x = (box.minPoint.x + box.maxPoint.x) / 2.0
        current_y = (box.minPoint.y + box.maxPoint.y) / 2.0
        delta_x = target.x - current_x
        delta_y = target.y - current_y
        position = created.position
        created.position = adsk.core.Point3D.create(
            position.x + delta_x, position.y + delta_y, 0)
        result.add(created)
    return result


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError('Open a Fusion design before running this script')
    if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise RuntimeError('The target design must have parametric history enabled')

    root = design.rootComponent
    comp = None
    for candidate in design.allComponents:
        if candidate.name == 'BACK_HALF':
            comp = candidate
            break
    if comp is None:
        comp = root
    for body in comp.bRepBodies:
        if body.name == 'BACK_SHELL':
            raise RuntimeError('BACK_SHELL already exists; refusing to overwrite it')

    # Editable driving dimensions.  Connector standards are kept in their own
    # locked reference sketches so accidental edits cannot break mating hardware.
    params = [
        ('backWidth', '254 mm', 'Overall back width'),
        ('backHeight', '130 mm', 'Overall back height'),
        ('backDepth', '30 mm', 'Overall back depth'),
        ('backStartY', '24.04 mm', 'Back half front-most coordinate'),
        ('backCornerRadius', '1.9 mm', 'Outer and rear edge radius'),
        ('backGrooveDepth', '6.10 mm', 'Depth of front mating groove'),
        ('backGrooveOpeningWidth', '250 mm', 'First-stage mating opening width'),
        ('backGrooveOpeningHeight', '126 mm', 'First-stage mating opening height'),
        ('backMainOpeningWidth', '246 mm', 'Main internal cavity width'),
        ('backMainOpeningHeight', '122 mm', 'Main internal cavity height'),
        ('backWallThickness', '4 mm', 'Rear and main side wall thickness'),
        ('backDetentLength', '10 mm', 'Mating detent length'),
        ('backDetentBaseWidth', '2 mm', 'Mating detent base width'),
        ('backDetentDepthTB', '0.8343 mm', 'Top/bottom detent projection'),
        ('backDetentDepthLR', '0.8343 mm', 'Left/right detent projection'),
        ('backDetentCrownRadius', '0.4 mm', 'Detent crown radius'),
        ('backRearRecessDepth', '0.5 mm', 'Default exterior connector recess depth'),
        ('backLabelHeight', '4 mm', 'Native rear label text height'),
        ('backConnectorDropZ', '23.35 mm',
         'USB / COM 0 connector row centre, drop below the enclosure centreline'),
        ('wifiCenterX', '88 mm',
         'WIFI centre, |X| from centreline (left of centre in rear view)'),
        ('wifiDropZ', '19.35 mm', 'WIFI centre, drop below the enclosure centreline'),
        ('wifiThroughD', '6.4 mm', 'WIFI bulkhead through-hole diameter'),
        ('wifiRecessD', '10 mm', 'WIFI exterior counterbore diameter'),
        ('usbCenterX', '36.5426 mm',
         'USB centre, |X| from centreline (left of centre in rear view)'),
        ('usbThroughW', '14.2 mm', 'USB aperture width'),
        ('usbThroughH', '6.3 mm', 'USB aperture height'),
        ('usbRecessW', '15.8 mm', 'USB exterior relief width'),
        ('usbRecessH', '8.2 mm', 'USB exterior relief height'),
        ('com0CenterX', '35.9169 mm',
         'COM 0 centre, |X| from centreline (right of centre in rear view)'),
        ('com0W', '13.3 mm', 'COM 0 aperture width'),
        ('com0H', '11.5 mm', 'COM 0 aperture height'),
        ('db9ScrewRightX', '11.6195 mm',
         'DB9 jackscrew hole, right side in rear view (model X = -11.6195)'),
        ('db9ScrewLeftX', '12.8906 mm',
         'DB9 jackscrew hole, left side in rear view (model X = +12.8906)'),
        ('db9ScrewDropZ', '23.35 mm', 'DB9 jackscrew centre drop below the centreline'),
        ('db9ScrewD', '4 mm', 'DB9 jackscrew clearance hole diameter'),
        ('endConnCenterX', '94.1081 mm',
         'End connector centre, |X| from centreline (right of centre in rear view)'),
        ('endConnDropZ', '15.1574 mm', 'End connector centre, drop below the centreline'),
        ('endConnThroughD', '10.2 mm', 'End connector through-hole diameter'),
        ('endConnRecessD', '13 mm', 'End connector exterior counterbore diameter'),
        ('labelDepth', '0.6 mm', 'Shared front/back AMS inlay depth'),
        ('labelInlayRecess', '0 mm', 'Shared front/back white inlay top recess'),
    ]
    for name, expression, comment in params:
        add_param(design, name, expression, 'mm', comment)

    # In the Rev2 master, one case-width/height edit must drive both halves.
    # Keep standalone-script compatibility when those front parameters do not exist.
    if design.userParameters.itemByName('caseWidth'):
        design.userParameters.itemByName('backWidth').expression = 'caseWidth'
        design.userParameters.itemByName('backGrooveOpeningWidth').expression = 'backWidth - 4 mm'
        design.userParameters.itemByName('backMainOpeningWidth').expression = 'backWidth - 8 mm'
    if design.userParameters.itemByName('caseHeight'):
        design.userParameters.itemByName('backHeight').expression = 'caseHeight'
        design.userParameters.itemByName('backGrooveOpeningHeight').expression = 'backHeight - 4 mm'
        design.userParameters.itemByName('backMainOpeningHeight').expression = 'backHeight - 8 mm'
    if design.userParameters.itemByName('outerCornerR'):
        design.userParameters.itemByName('backCornerRadius').expression = 'outerCornerR'

    start_index = design.timeline.count
    # Build into the identity-positioned BACK_HALF component when present.
    # Standalone-script compatibility falls back to the root component.

    # 1. Main shell blank.
    sk_outer = comp.sketches.add(comp.xZConstructionPlane)
    sk_outer.name = 'SK_BACK_OUTER_PROFILE'
    parametric_centered_rect_xz(sk_outer, 'backWidth', 'backHeight', 254.0, 130.0)
    ft_outer = extrude(
        comp, sk_outer.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        'backDepth', start_offset='backStartY', name='FT_BACK_OUTER_BODY'
    )
    body = ft_outer.bodies.item(0)
    body.name = 'BACK_SHELL'
    add_combined_outer_setback_fillet(
        comp, body, 24.04, 30.0, 54.04, 'backCornerRadius')

    # 2. Two-stage cavity reproduces the original 2 mm groove wall followed by
    #    the 4 mm structural wall.  Each stage stays independently editable.
    sk_groove = comp.sketches.add(comp.xZConstructionPlane)
    sk_groove.name = 'SK_BACK_GROOVE_OPENING'
    parametric_centered_rect_xz(
        sk_groove, 'backGrooveOpeningWidth', 'backGrooveOpeningHeight', 250.0, 126.0)
    extrude(
        comp, sk_groove.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
        'backGrooveDepth', start_offset='backStartY', name='FT_BACK_GROOVE_CUT',
        participant_bodies=[body]
    )

    sk_cavity = comp.sketches.add(comp.xZConstructionPlane)
    sk_cavity.name = 'SK_BACK_MAIN_CAVITY'
    parametric_centered_rect_xz(
        sk_cavity, 'backMainOpeningWidth', 'backMainOpeningHeight', 246.0, 122.0)
    extrude(
        comp, sk_cavity.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
        'backDepth - backGrooveDepth - backWallThickness',
        start_offset='backStartY + backGrooveDepth', name='FT_BACK_MAIN_CAVITY_CUT',
        participant_bodies=[body]
    )

    # 3. Rear through features.  Connector geometry is isolated from the shell
    #    so swapping a connector later does not destabilize the enclosure.
    sk_ports = comp.sketches.add(comp.xZConstructionPlane)
    sk_ports.name = 'SK_BACK_PORTS_THROUGH'
    param_circle_xz(sk_ports, -88.0, 19.35, 6.4,
                    'wifiCenterX', 'wifiDropZ', 'wifiThroughD')
    param_rect_xz(sk_ports, -36.5426, 23.35, 14.2, 6.3,
                  'usbCenterX', 'backConnectorDropZ', 'usbThroughW', 'usbThroughH')
    # The DE-9 aperture outline is a connector standard, so it stays locked
    # reference geometry rather than being re-derived from parameters.
    add_db9_profile(sk_ports)                                  # RS232 DB9
    param_circle_xz(sk_ports, 11.6195, 23.35, 4.0,
                    'db9ScrewRightX', 'db9ScrewDropZ', 'db9ScrewD')
    param_circle_xz(sk_ports, -12.8906, 23.35, 4.0,
                    'db9ScrewLeftX', 'db9ScrewDropZ', 'db9ScrewD')
    param_rect_xz(sk_ports, 35.9169, 23.35, 13.3, 11.5,
                  'com0CenterX', 'backConnectorDropZ', 'com0W', 'com0H')
    param_circle_xz(sk_ports, 94.1081, 15.1574, 10.2,
                    'endConnCenterX', 'endConnDropZ', 'endConnThroughD')
    # The four 6 mm holes at |X| = 67.525 belonged to the superseded bracket
    # design and were removed with it.
    extrude(
        comp, all_profiles(sk_ports), adsk.fusion.FeatureOperations.CutFeatureOperation,
        4.20, start_offset=49.94, name='FT_BACK_PORTS_THROUGH_CUT', participant_bodies=[body]
    )

    sk_recess = comp.sketches.add(comp.xZConstructionPlane)
    sk_recess.name = 'SK_BACK_PORT_RECESSES'
    param_circle_xz(sk_recess, -88.0, 19.35, 10.0,
                    'wifiCenterX', 'wifiDropZ', 'wifiRecessD')   # 1.5 deep
    extrude(
        comp, sk_recess.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
        -1.50, start_offset=54.04, name='FT_BACK_WIFI_RECESS', participant_bodies=[body]
    )
    # Additional exterior recesses have different depths, so each owns a small
    # dedicated sketch and feature instead of relying on profile index order.
    sk_usb_recess = comp.sketches.add(comp.xZConstructionPlane)
    sk_usb_recess.name = 'SK_BACK_USB_RECESS'
    param_rect_xz(sk_usb_recess, -36.5426, 23.35, 15.8, 8.2,
                  'usbCenterX', 'backConnectorDropZ', 'usbRecessW', 'usbRecessH')
    extrude(comp, sk_usb_recess.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
            -0.50, start_offset=54.04, name='FT_BACK_USB_RECESS', participant_bodies=[body])

    sk_end_recess = comp.sketches.add(comp.xZConstructionPlane)
    sk_end_recess.name = 'SK_BACK_END_CONNECTOR_RECESS'
    param_circle_xz(sk_end_recess, 94.1081, 15.1574, 13.0,
                    'endConnCenterX', 'endConnDropZ', 'endConnRecessD')
    extrude(comp, sk_end_recess.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
            -0.50, start_offset=54.04, name='FT_BACK_END_CONNECTOR_RECESS', participant_bodies=[body])

    sk_db9_outer = comp.sketches.add(comp.xZConstructionPlane)
    sk_db9_outer.name = 'SK_BACK_DB9_OUTER_RECESS'
    rounded_rect_xz(sk_db9_outer, -0.6831, 23.3511, 31.3, 12.9, 1.7)
    extrude(comp, sk_db9_outer.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
            -1.0, start_offset=54.04, name='FT_BACK_DB9_OUTER_RECESS', participant_bodies=[body])

    sk_db9_inner = comp.sketches.add(comp.xZConstructionPlane)
    sk_db9_inner.name = 'SK_BACK_DB9_INNER_RECESS'
    rounded_rect_xz(sk_db9_inner, -0.6831, 23.3511, 32.5, 14.1, 2.3)
    extrude(comp, sk_db9_inner.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation,
            2.0, start_offset=50.04, name='FT_BACK_DB9_INNER_RECESS', participant_bodies=[body])

    # 4. Twelve mating detents.  The source design uses a 45-degree tapered
    #    extrusion followed by an R0.4 full crown.  Fusion represents the crown
    #    as two tangent cylindrical faces, but its physical envelope and snap
    #    interference match the source STEP to numerical precision.
    tb_x = [100.0, -0.5, -101.0]
    lr_z = [38.0, 0.0, -38.0]
    # RY(180) swaps physical top/bottom and left/right source planes.  Feature
    # names below describe the corrected canonical side, not the source side.
    top_plane = plane_offset(comp, comp.xYConstructionPlane, 63.0, 'PL_BACK_DETENTS_TOP')
    bottom_plane = plane_offset(comp, comp.xYConstructionPlane, -63.0, 'PL_BACK_DETENTS_BOTTOM')
    right_plane = plane_offset(comp, comp.yZConstructionPlane, 125.0, 'PL_BACK_DETENTS_RIGHT')
    left_plane = plane_offset(comp, comp.yZConstructionPlane, -125.0, 'PL_BACK_DETENTS_LEFT')
    detent_features = []
    # Canonical TOP is the transformed source BOTTOM.
    detent_features.append(add_detent_set(
        comp, top_plane, 'TOP', [(x, 27.14, -63.0) for x in tb_x],
        (1, 0, 0), (0, 1, 0), 10.0, 2.0, -0.8343)[1])
    # Canonical BOTTOM is the transformed source TOP.
    detent_features.append(add_detent_set(
        comp, bottom_plane, 'BOTTOM', [(x, 27.14, 63.0) for x in tb_x],
        (1, 0, 0), (0, 1, 0), 10.0, 2.0, 0.8343)[1])
    # Canonical RIGHT is the transformed source LEFT.
    detent_features.append(add_detent_set(
        comp, right_plane, 'RIGHT', [(-125.0, 27.02, z) for z in lr_z],
        (0, 0, 1), (0, 1, 0), 10.0, 2.0, -0.8343)[1])
    # Canonical LEFT is the transformed source RIGHT.
    detent_features.append(add_detent_set(
        comp, left_plane, 'LEFT', [(125.0, 27.04, z) for z in lr_z],
        (0, 0, 1), (0, 1, 0), 10.0, 2.0, 0.8343)[1])

    detent_bodies = adsk.core.ObjectCollection.create()
    for feature in detent_features:
        for index in range(feature.bodies.count):
            detent_bodies.add(feature.bodies.item(index))
    combine_input = comp.features.combineFeatures.createInput(body, detent_bodies)
    combine_input.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    combine_input.isKeepToolBodies = False
    combine = comp.features.combineFeatures.add(combine_input)
    combine.name = 'FT_BACK_DETENTS_JOIN'

    # 5. Native text is intentionally isolated from all mechanical sketches.
    #    The manufacturing method intentionally matches the front: a black
    #    deboss cavity plus aligned white AMS inlay bodies from the same text.
    rear_faces = []
    rear_y = mm(54.04)
    for face in body.faces:
        box = face.boundingBox
        if (abs(box.minPoint.y - rear_y) < mm(0.01) and
                abs(box.maxPoint.y - rear_y) < mm(0.01)):
            rear_faces.append(face)
    if not rear_faces:
        raise RuntimeError('Could not resolve rear exterior face for labels')
    rear_face = max(rear_faces, key=lambda item: item.area)
    sk_labels = comp.sketches.add(rear_face)
    sk_labels.name = 'SK_BACK_LABELS_NATIVE'
    label_entities = add_back_labels(sk_labels)
    sk_labels.isVisible = False

    for sketch in comp.sketches:
        sketch.isVisible = False

    mechanical_end_index = design.timeline.count - 1
    if mechanical_end_index >= start_index:
        group = design.timeline.timelineGroups.add(start_index, mechanical_end_index)
        if group:
            group.name = 'BACK HALF - PARAMETRIC REBUILD'

    print_start_index = design.timeline.count
    label_cut = extrude(
        comp, label_entities, adsk.fusion.FeatureOperations.CutFeatureOperation,
        '-labelDepth',
        name='FT_BACK_LABEL_DEBOSS_CUT', participant_bodies=[body]
    )
    label_inlay = extrude(
        comp, label_entities, adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        '-(labelDepth - labelInlayRecess)',
        start_offset='-labelInlayRecess',
        name='FT_BACK_AMS_WHITE_TEXT_INLAY'
    )

    # Reuse the already validated white front-inlay appearance when available.
    # The source lives in FRONT_HALF, so search the full design rather than
    # only this back component.
    white_appearance = None
    for source_component in design.allComponents:
        for candidate in source_component.bRepBodies:
            if (candidate.name.startswith('INLAY_FRONT_') and
                    candidate.appearance):
                white_appearance = candidate.appearance
                break
        if white_appearance:
            break

    label_centers = {
        'WIFI': 88.0000,
        'USB': 36.5426,
        'RS232': 0.6831,
        'COM_0': -35.9169,
    }
    grouped = {name: [] for name in label_centers}
    for inlay_body in label_inlay.bodies:
        center_x = (inlay_body.boundingBox.minPoint.x + inlay_body.boundingBox.maxPoint.x) * 5.0
        label_name = min(label_centers, key=lambda key: abs(center_x - label_centers[key]))
        grouped[label_name].append(inlay_body)
        if white_appearance:
            inlay_body.appearance = white_appearance
    for label_name, bodies in grouped.items():
        bodies.sort(key=lambda item: item.boundingBox.maxPoint.x, reverse=True)
        for index, inlay_body in enumerate(bodies, 1):
            inlay_body.name = f'INLAY_BACK_{label_name}_{index:02d}'

    print_end_index = design.timeline.count - 1
    if print_end_index >= print_start_index:
        print_group = design.timeline.timelineGroups.add(print_start_index, print_end_index)
        if print_group:
            print_group.name = 'PRINT - AMS BACK LABELS'

    print('BACK_SHELL created')
    print('root_body_count', comp.bRepBodies.count)
    print('sketch_count', comp.sketches.count)
    print('feature_count', comp.features.count)
    print('black_shell_volume_mm3', round(body.volume * 1000.0, 6))
    print('back_inlay_body_count', label_inlay.bodies.count)
    print('shell_faces', body.faces.count)


def stop(_context: str):
    pass
