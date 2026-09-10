"""Add the verified missing internal control collars to an existing Rev3 front.

The geometry is reconstructed from Front_Half.step.  It deliberately excludes
the display-support work and does not invent push-button guide tunnels: the
reference main body contains only the original 3 mm-deep button openings.
"""
import adsk.core
import adsk.fusion


def mm(v):
    return v / 10.0


def vi(value):
    return adsk.core.ValueInput.createByString(
        value if isinstance(value, str) else f'{value} mm')


def point(x, y, z):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def sp(sketch, x, y, z):
    return sketch.modelToSketchSpace(point(x, y, z))


def add_param(design, name, expression):
    return (design.userParameters.itemByName(name) or
            design.userParameters.add(
                name, vi(expression), 'mm', 'Verified Front_Half.step control collar'))


def parametric_circle(sketch, cx, cz, diameter_expression, nominal_diameter):
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
        sp(sketch, cx, 0, cz), mm(nominal_diameter / 2))
    circle.centerSketchPoint.isFixed = True
    dimension = sketch.sketchDimensions.addDiameterDimension(
        circle, sp(sketch, cx + nominal_diameter / 2 + 3, 0, cz + 3))
    dimension.parameter.expression = diameter_expression
    return circle


def annular_profiles(sketch):
    rings = adsk.core.ObjectCollection.create()
    for index in range(sketch.profiles.count):
        profile = sketch.profiles.item(index)
        if profile.profileLoops.count == 2:
            rings.add(profile)
    if not rings.count:
        raise RuntimeError(f'{sketch.name}: no annular profiles')
    return rings


def extrude_join(component, profile_collection, distance, start, name):
    features = component.features.extrudeFeatures
    feature_input = features.createInput(
        profile_collection, adsk.fusion.FeatureOperations.JoinFeatureOperation)
    feature_input.startExtent = adsk.fusion.OffsetStartDefinition.create(vi(start))
    feature_input.setDistanceExtent(False, vi(distance))
    feature = features.add(feature_input)
    feature.name = name
    return feature


def feature_exists(component, name):
    return any(component.features.item(index).name == name
               for index in range(component.features.count))


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design or design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise RuntimeError('Open ARCI Enclosure Rev3 as a parametric design')
    if not app.activeDocument.name.startswith('ARCI Enclosure Rev3'):
        raise RuntimeError('ARCI Enclosure Rev3 must be the active document')

    component = next(
        (candidate for candidate in design.allComponents
         if candidate.name == 'FRONT_HALF'), None)
    if not component:
        raise RuntimeError('FRONT_HALF component not found')
    body = next(
        (candidate for candidate in component.bRepBodies
         if candidate.name == 'FRONT_SHELL'), None)
    if not body:
        raise RuntimeError('FRONT_SHELL body not found')
    if feature_exists(component, 'FT_FRONT_CONTROL_COLLARS_STANDARD'):
        raise RuntimeError('Control collars already exist; no duplicate was created')

    for name, expression in [
        ('rotaryMultiHoleD', '15.8 mm'),
        ('rotaryTuneHoleD', '8.4 mm'),
        ('rotaryRightHoleD', '6.8 mm'),
        ('rotaryAFRFHoleD', '8.85 mm'),
        ('collarMultiOD', '24 mm'),
        ('collarTuneOD', '18.3 mm'),
        ('collarRightOD', '13.6 mm'),
        ('collarAFRFOD', '21 mm'),
        ('collarStandardDepth', '3 mm'),
        ('collarAFRFDepth', '5.5 mm'),
        ('collarAFRFBoreStepD', '13 mm'),
        ('collarAFRFBoreStepDepth', '1.2 mm'),
    ]:
        add_param(design, name, expression)

    timeline_start = design.timeline.count

    sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = 'SK_FRONT_CONTROL_COLLARS_STANDARD'
    for x, z, outer_expression, outer_diameter, inner_expression, inner_diameter in [
        (-106, -46, 'collarMultiOD', 24, 'rotaryMultiHoleD', 15.8),
        (-106, -22, 'collarTuneOD', 18.3, 'rotaryTuneHoleD', 8.4),
        (113, 2.9983, 'collarRightOD', 13.6, 'rotaryRightHoleD', 6.8),
        (113, 39.9983, 'collarRightOD', 13.6, 'rotaryRightHoleD', 6.8),
    ]:
        parametric_circle(sketch, x, z, outer_expression, outer_diameter)
        parametric_circle(sketch, x, z, inner_expression, inner_diameter)
    extrude_join(component, annular_profiles(sketch),
                 'collarStandardDepth', 'frontThickness',
                 'FT_FRONT_CONTROL_COLLARS_STANDARD')
    sketch.isVisible = False

    sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = 'SK_FRONT_CONTROL_COLLAR_AFRF_PRIMARY'
    parametric_circle(sketch, 76.519, -33.6, 'collarAFRFOD', 21)
    parametric_circle(sketch, 76.519, -33.6, 'rotaryAFRFHoleD', 8.85)
    extrude_join(component, annular_profiles(sketch),
                 'collarAFRFDepth-collarAFRFBoreStepDepth', 'frontThickness',
                 'FT_FRONT_CONTROL_COLLAR_AFRF_PRIMARY')
    sketch.isVisible = False

    sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = 'SK_FRONT_CONTROL_COLLAR_AFRF_COUNTERBORE'
    parametric_circle(sketch, 76.519, -33.6, 'collarAFRFOD', 21)
    parametric_circle(sketch, 76.519, -33.6, 'collarAFRFBoreStepD', 13)
    extrude_join(
        component, annular_profiles(sketch), 'collarAFRFBoreStepDepth',
        'frontThickness+collarAFRFDepth-collarAFRFBoreStepDepth',
        'FT_FRONT_CONTROL_COLLAR_AFRF_COUNTERBORE')
    sketch.isVisible = False

    timeline_end = design.timeline.count - 1
    if timeline_end >= timeline_start:
        group = design.timeline.timelineGroups.add(timeline_start, timeline_end)
        if group:
            group.name = 'FRONT HALF - CONTROL SUPPORT COLLARS'

    design.computeAll()


def stop(_context: str):
    pass
