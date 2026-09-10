"""Make the existing VFO knob's finger dimple scale safely with its diameter.

Run this once in Fusion 360 with the parametric ARCI master open.  It updates
the existing ``KNOB_VFO_MAIN`` component; it does not rebuild the knob or
touch the enclosure.  The script is safe to run again.

The legacy model drives the dimple circle from ``vfoDimpleD``, but the round
at its floor was a fixed value.  As a result, a diameter edit either made the
floor look flat or caused ``FT_VFO_KNOB_DIMPLE_ROUND`` to fail.

After this migration, change *only* ``vfoDimpleD`` for normal size changes.
The dimple retains a ``vfoDimpleFloorD``-wide flat at its lowest point and
derives both its depth and its floor-round radius from the diameter:

    vfoDimpleRoundR = (vfoDimpleD - vfoDimpleFloorD) / 2
    vfoDimpleDepth  = vfoDimpleRoundR

The shipped 9 mm dimple remains exactly 3.5 mm deep with a 2 mm flat floor.
Keep ``vfoDimpleD`` greater than ``vfoDimpleFloorD``.  Increase
``vfoDimpleFloorD`` only when a broader flat-bottomed cup is wanted.
"""
import adsk.core
import adsk.fusion


COMPONENT = 'KNOB_VFO_MAIN'
DIMPLE_FILLET = 'FT_VFO_KNOB_DIMPLE_ROUND'


def value_input(expression):
    return adsk.core.ValueInput.createByString(expression)


def ensure_parameter(parameters, name, expression, comment, unit='mm'):
    parameter = parameters.itemByName(name)
    if parameter is None:
        parameter = parameters.add(name, value_input(expression), unit, comment)
    else:
        parameter.comment = comment
    return parameter


def find_component(design, name):
    for component in design.allComponents:
        if component.name == name:
            return component
    return None


def find_feature(component, name):
    for index in range(component.features.count):
        feature = component.features.item(index)
        if feature.name == name:
            return feature
    return None


def run(_context):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None or design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise RuntimeError('Open the parametric ARCI design before running this script.')

    parameters = design.userParameters
    dimple_d = parameters.itemByName('vfoDimpleD')
    dimple_depth = parameters.itemByName('vfoDimpleDepth')
    if dimple_d is None or dimple_depth is None:
        raise RuntimeError('Expected user parameters vfoDimpleD and vfoDimpleDepth were not found.')

    component = find_component(design, COMPONENT)
    if component is None:
        raise RuntimeError('Component %s was not found.' % COMPONENT)

    fillet = adsk.fusion.FilletFeature.cast(find_feature(component, DIMPLE_FILLET))
    if fillet is None or fillet.edgeSets.count != 1:
        raise RuntimeError('Expected one-edge-set fillet %s was not found.' % DIMPLE_FILLET)

    # A 2 mm floor exactly preserves the original Ø9 mm, 3.5 mm-deep dimple.
    # The explicit floor parameter avoids a fragile zero-width/pointed floor.
    ensure_parameter(
        parameters, 'vfoDimpleFloorD', '2 mm',
        'Diameter of the dimple flat floor; keep below vfoDimpleD')
    round_radius = ensure_parameter(
        parameters, 'vfoDimpleRoundR', '( vfoDimpleD - vfoDimpleFloorD ) / 2',
        'Derived dimple floor-round radius; do not edit directly')

    # Both distances must track together: that preserves the tangent, curved
    # floor instead of leaving a fixed-radius fillet in a resized cut.
    dimple_depth.expression = 'vfoDimpleRoundR'
    fillet.edgeSets.item(0).radius.expression = round_radius.name

    app.userInterface.messageBox(
        'VFO dimple is now diameter-driven. Edit vfoDimpleD to resize it.\n\n'
        'Current relationships:\n'
        '  vfoDimpleRoundR = (vfoDimpleD - vfoDimpleFloorD) / 2\n'
        '  vfoDimpleDepth = vfoDimpleRoundR',
        'VFO dimple parameterized')
