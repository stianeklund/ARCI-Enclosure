"""Native button caps, power LED dummy, and PLA translucency fix for the ARCI front panel.

Run inside Fusion 360 (MCP script runner or Scripts and Add-Ins) against
`ARCI Enclosure Rev3`. Four jobs, all idempotent - re-running replaces the
previous result rather than stacking duplicates.

1. MATERIALS. `PLA (Black)` and `PLA (White)` ship with the advanced-plastic
   `Translucency` flag on (Depth 0.75), so `FRONT_SHELL` and `BACK_SHELL`
   render subsurface-translucent and interior parts - the anodized VFO
   encoder in particular - show through the closed enclosure. Translucency is
   cleared on every opaque print appearance in the design.

2. LEGACY CAPS OFF. Earlier working assemblies can carry 27 imported cap
occurrences (one per switch, at the panel face, Y about 1.4-1.9). Only those
legacy cap references are hidden. The native replacement caps are used for
the public model.

3. NATIVE CAPS ON. 27 instances of `DEV_BUTTON_CAP_MASTER_NATIVE` are placed
   on the canonical cutout centres from `Front_Parametric_Rebuild.BUTTON_CENTERS`
   - the panel openings the caps must actually fit, not the slightly drifted
   legacy import positions (up to 0.22 mm off in X on the F row). They are
   `addExistingComponent` instances of one component, so all 27 share a single
   BRep and one graphics proxy: no body copies, no pattern feature, and one
   light bulb on the parent `BUTTON_CAPS` component toggles the whole set.

   Cap depth comes from the existing dev placement (Y translation 6.405 mm,
   giving a cap centre at Y = 1.905 and 2.595 mm of cap proud of the front
   face). That reproduces the legacy F-row cap centre of 1.90 mm to within
   0.005 mm, so the dev placement was already depth-matched and is reused.

4. POWER CAP RED + GREEN LED. The POWER instance gets an occurrence-level red
   override so the other 26 caps stay black, and `LED_POWER_GREEN` adds a T-1
   (3 mm) LED dummy on the `ledHoleX` / `ledHoleZ` axis to check the fit of a
   real LED in the panel's `auxHoleD` 3.5 mm hole. The LED is a separate
   component nested under `FRONT_HALF`, never joined to `FRONT_SHELL`.

Nothing is cut, joined or moved on the enclosure itself; this script only adds
occurrences and bodies and changes appearance/visibility.
Entry point: run(context).
"""
import adsk.core, adsk.fusion, math, os, tempfile

REPORT = os.path.join(tempfile.gettempdir(), 'ARCI_front_panel_report.txt')

BND_MINUS = 'BND –'

# Canonical panel-cutout centres (model X, Z), identical to
# Front_Parametric_Rebuild.BUTTON_CENTERS.
BUTTON_CENTERS = {('F%d' % (k + 1)): (-62.65 + 18 * k, -46.35) for k in range(6)}
BUTTON_CENTERS.update({
    'PWR': (-113, 0.66), 'SEND': (-98, 0.66), 'PRE': (-113, 12.66), 'ATT': (-98, 12.66),
    'TUNE': (-113, 24.66), 'PROC': (-98, 24.66), 'VOX': (-113, 36.66), 'XVTR': (-98, 36.66),
    'POWER': (-98, 48.66),
    'CLR': (61.5, 3.66), 'MODE': (76.5, 3.66), 'ENT': (91.5, 3.66),
    BND_MINUS: (61.5, 15.66), 'A / B': (76.5, 15.66), 'SPLIT': (91.5, 15.66),
    'BND +': (61.5, 27.66), 'RIT': (76.5, 27.66), 'XIT': (91.5, 27.66),
    'NTCH': (61.5, 39.66), 'NR': (76.5, 39.66), 'NB': (91.5, 39.66)})

CAP_MASTER = 'DEV_BUTTON_CAP_MASTER_NATIVE'
CAPS_PARENT = 'BUTTON_CAPS'
RED_COMP = 'BUTTON_CAP_POWER_RED'
RED_LABEL = 'POWER'
LEGACY_CAP = '1Cxxx'          # legacy imported cap component name
CAP_DEPTH_Y = 6.405           # mm, from the existing depth-matched dev placement
FRONT_COMP = 'FRONT_HALF'
LED_COMP = 'LED_POWER_GREEN'

P = adsk.core.Point3D.create
V = adsk.core.ValueInput.createByReal
VS = adsk.core.ValueInput.createByString

def cm(v): return v / 10.0
def mm(v): return round(v * 10, 4)

def setp(ups, n, e, c, unit='mm'):
    p = ups.itemByName(n)
    if p is None:
        ups.add(n, VS(e), unit, c)
    else:
        p.expression = e; p.comment = c

def lib_appearance(app, *rules):
    """First library appearance matching a rule; each rule is a tuple of
    lowercase substrings that must all appear in the name."""
    libs = [L for L in app.materialLibraries if 'Appearance' in L.name]
    for rule in rules:
        for lib in libs:
            for a in lib.appearances:
                n = a.name.lower()
                if all(t in n for t in rule):
                    return a
    return None

def design_appearance(des, *rules):
    for rule in rules:
        for a in des.appearances:
            n = a.name.lower()
            if all(t in n for t in rule):
                return a
    return None

def cap_transform(bx, bz):
    """Place a cap on the panel cutout at (bx, bz).

    Orientation is taken from the parked dev occurrence: component-local +Z
    maps to world -Y (the cap stands out of the panel) and local +Y to world
    +Z. CAP_DEPTH_Y sets how deep the cap sits.
    """
    t = adsk.core.Matrix3D.create()
    t.setWithArray([1.0, 0.0, 0.0, cm(bx),
                    0.0, 0.0, -1.0, cm(CAP_DEPTH_Y),
                    0.0, 1.0, 0.0, cm(bz),
                    0.0, 0.0, 0.0, 1.0])
    return t


# ---------------------------------------------------------------- 1. materials

def fix_translucency(des, out):
    """Clear subsurface Translucency on the opaque filament appearances only.

    Scope is deliberately narrow: `PLA (*)` and `ABS (*)`, which is what the
    shells and inlays use. Appearances that are *meant* to be translucent -
    `Plastic - Translucent Glossy (Green)` on the LED, and the PA 11 nylon -
    are left alone, so do not widen this to every plastic or paint.

    `des.appearances` yields the same appearance more than once (PLA (Black)
    and PLA (White) even share one id), and mutating a property perturbs the
    iteration, so the sweep repeats until a clean pass finds nothing left.
    """
    out.append('--- 1. MATERIALS ---')

    def targets():
        return [a for a in des.appearances
                if (a.name.startswith('PLA (') or a.name.startswith('ABS ('))
                and 'translucent' not in a.name.lower()]

    fixed = []
    for _ in range(8):
        pending = []
        for a in targets():
            p = a.appearanceProperties.itemByName('Translucency')
            if p is not None and p.value:
                pending.append(a)
        if not pending:
            break
        for a in pending:
            p = a.appearanceProperties.itemByName('Translucency')
            if p is not None and p.value:
                p.value = False
                if a.name not in fixed:
                    fixed.append(a.name)
    for n in fixed:
        out.append('  Translucency OFF: %s' % n)
    out.append('  %d appearance(s) made opaque' % len(fixed))


# ------------------------------------------------------------- 2. legacy caps

def hide_legacy_caps(root, out):
    """Hide the imported cap occurrences only.

    The walk is deliberately scoped to front-assembly -> button matrix ->
    cap, two levels deep. A general recursive search would descend into the
    88-child `ARCI v6` PCB tree and its thousands of copper occurrences,
    which is slow enough to time the script runner out.
    """
    out.append('--- 2. LEGACY CAPS ---')
    hidden = 0
    matrices = 0
    for front in root.occurrences:
        if not front.component.name.startswith('Radio Enclosure Front - Proto_Front Components'):
            continue
        for matrix in front.childOccurrences:
            if 'BUTTON' not in matrix.component.name.upper():
                continue
            matrices += 1
            for occ in matrix.childOccurrences:
                if occ.component.name != LEGACY_CAP:
                    continue
                if occ.isLightBulbOn:
                    occ.isLightBulbOn = False
                    hidden += 1
    out.append('  scanned %d button matrices' % matrices)
    out.append('  hid %d legacy %s cap occurrence(s)' % (hidden, LEGACY_CAP))
    return hidden


# ------------------------------------------------------------- 3. native caps

def place_native_caps(des, root, out):
    out.append('--- 3. NATIVE CAPS ---')
    master = None
    for c in des.allComponents:
        if c.name == CAP_MASTER:
            master = c
            break
    if master is None:
        raise RuntimeError('Component %s not found' % CAP_MASTER)

    # A new occurrence inherits the light bulb of the source it is instanced
    # from, and a light bulb set on an occurrence created in this same
    # transaction does not persist. So switch the master body and the parked
    # dev occurrence on FIRST; the instances are then born visible.
    for b in master.bRepBodies:
        if not b.isLightBulbOn:
            b.isLightBulbOn = True
            out.append('  master body %s light bulb on' % b.name)
    for o in root.occurrences:
        if o.component.name == CAP_MASTER and not o.isLightBulbOn:
            o.isLightBulbOn = True
            out.append('  parked dev occurrence %s light bulb on' % o.name)

    for o in [o for o in root.occurrences if o.component.name == CAPS_PARENT]:
        o.deleteMe()
    parent_occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    parent = parent_occ.component
    parent.name = CAPS_PARENT

    # Orientation from the existing dev placement: local +Z maps to world -Y
    # (cap sticks out of the panel) and local +Y maps to world +Z.
    placed = []
    for label in sorted(BUTTON_CENTERS, key=lambda k: (BUTTON_CENTERS[k][0], BUTTON_CENTERS[k][1])):
        if label == RED_LABEL:
            continue    # gets its own component, see make_red_power_cap
        occ = parent.occurrences.addExistingComponent(master, cap_transform(*BUTTON_CENTERS[label]))
        # New instances inherit the parked dev occurrence's light bulb, which
        # is off; switch each one on explicitly.
        occ.isLightBulbOn = True
        try:
            occ.name = 'CAP_' + label.replace(' ', '').replace('/', '_').replace('+', 'PLUS').replace('–', 'MINUS')
        except Exception:
            pass  # Occurrence.name is read-only in some API builds
        placed.append((label, occ))
    out.append('  placed %d shared instances of %s under %s' % (len(placed), CAP_MASTER, CAPS_PARENT))
    return master, parent, placed


# --------------------------------------------------------- 4a. red POWER cap

def make_red_power_cap(des, master, parent, out):
    """Give the POWER cap its own component so it can be red.

    An occurrence-level appearance override does NOT work here: the cap
    master's body carries a body-level `PLA (Black)`, and body-level beats
    occurrence-level in Fusion's appearance precedence. `BRepBody`'s
    `appearanceSourceType` is read-only, so the body override cannot be
    cleared through the API either. Copying the body into a dedicated
    component and colouring that body red is the way that actually renders.
    Cost is one extra 49-face body; the other 26 caps still share one BRep.
    """
    out.append('--- 4a. POWER CAP RED ---')
    red = (design_appearance(des, ('abs', 'red'), ('pla', 'red'), ('red',)) or
           lib_appearance(adsk.core.Application.get(),
                          ('pla', 'red'), ('abs', 'red'),
                          ('paint', 'glossy', 'red'), ('plastic', 'red'), ('red',)))
    if red is None:
        out.append('  no red appearance available; POWER cap left black')
        return

    for k in list(parent.occurrences):
        if k.component.name == RED_COMP:
            k.deleteMe()

    bx, bz = BUTTON_CENTERS[RED_LABEL]
    occ = parent.occurrences.addNewComponent(cap_transform(bx, bz))
    comp = occ.component
    comp.name = RED_COMP
    occ.isLightBulbOn = True

    src = master.bRepBodies.item(0)
    comp.features.copyPasteBodies.add(src)
    body = comp.bRepBodies.item(comp.bRepBodies.count - 1)
    body.name = RED_COMP
    body.isVisible = True
    body.appearance = red

    # copyPasteBodies pastes at the SOURCE's world position expressed in the
    # new component's frame, so the body lands at the parked dev coordinates.
    # Move it so its local box matches the master's, then the occurrence
    # transform puts it on the POWER cutout.
    def centre(b):
        bb = b.boundingBox
        return ((bb.minPoint.x + bb.maxPoint.x) / 2,
                (bb.minPoint.y + bb.maxPoint.y) / 2,
                (bb.minPoint.z + bb.maxPoint.z) / 2)

    mc, rc = centre(src), centre(body)
    v = adsk.core.Vector3D.create(mc[0] - rc[0], mc[1] - rc[1], mc[2] - rc[2])
    # moveFeatures works in world space, so rotate the local delta by the
    # occurrence's orientation before applying it.
    rot = occ.transform2.copy()
    rot.translation = adsk.core.Vector3D.create(0, 0, 0)
    v.transformBy(rot)
    t = adsk.core.Matrix3D.create()
    t.translation = v
    coll = adsk.core.ObjectCollection.create()
    coll.add(body)
    mi = comp.features.moveFeatures.createInput2(coll)
    mi.defineAsFreeMove(t)
    comp.features.moveFeatures.add(mi).name = 'FT_RED_CAP_ALIGN_TO_MASTER_LOCAL'

    nc = centre(body)
    out.append('  %s body appearance = %s' % (RED_COMP, red.name))
    out.append('  local centre now (%.4f, %.4f, %.4f), master (%.4f, %.4f, %.4f)'
               % (mm(nc[0]), mm(nc[1]), mm(nc[2]), mm(mc[0]), mm(mc[1]), mm(mc[2])))
    out.append('  placed on the %s cutout at (%.2f, %.2f)' % (RED_LABEL, bx, bz))


# ------------------------------------------------------------- 4b. green LED

def power_led_appearance(app, des):
    """Dedicated low-luminance appearance; do not modify shared green plastic."""
    name = 'ARCI Power LED - Soft Green Emission'
    ap = des.appearances.itemByName(name)
    if ap is None:
        source = (lib_appearance(app, ('led (green)',)) or
                  lib_appearance(app, ('translucent', 'green', 'glossy')))
        if source is None:
            raise RuntimeError('No compatible green LED appearance available')
        ap = des.appearances.addByCopy(source, name)
    ap.appearanceProperties.itemById('opaque_emission').value = True
    ap.appearanceProperties.itemById('opaque_luminance').value = 30.0
    ap.appearanceProperties.itemById('opaque_luminance_modifier').value = (
        adsk.core.Color.create(25, 243, 25, 255))
    return ap


def build_led(app, des, root, out):
    out.append('--- 4b. GREEN POWER LED ---')
    ups = des.userParameters

    def val(name, default):
        p = ups.itemByName(name)
        return mm(p.value) if p else default

    ax = val('ledHoleX', -112.0)
    az = val('ledHoleZ', 52.1731)

    setp(ups, 'ledBodyD', '3 mm', 'T-1 LED barrel diameter (dummy)')
    setp(ups, 'ledFlangeD', '3.4 mm', 'T-1 LED base flange diameter (dummy)')
    setp(ups, 'ledFlangeT', '1 mm', 'T-1 LED base flange thickness (dummy)')
    setp(ups, 'ledBarrelL', '2.8 mm', 'LED barrel length between flange and dome (dummy)')
    setp(ups, 'ledProtrude', '0.4 mm', 'How far the LED dome stands proud of the front face')
    setp(ups, 'ledExtraFaceProud', '0.5 mm',
         'Additional source proud that replaces the legacy LED tail Move')

    rb = val('ledBodyD', 3.0) / 2.0
    rf = val('ledFlangeD', 3.4) / 2.0
    flange_t = val('ledFlangeT', 1.0)
    barrel_l = val('ledBarrelL', 2.8)
    protrude = val('ledProtrude', 0.4)
    extra_face_proud = val('ledExtraFaceProud', 0.5)

    front = next((o for o in root.occurrences if o.component.name == FRONT_COMP), None)
    if front is None:
        raise RuntimeError('%s occurrence was not found' % FRONT_COMP)

    # The LED source belongs under FRONT_HALF. Replace only that exact child
    # so re-runs are idempotent and do not create a second root-level LED.
    nested_removed = 0
    for i in range(front.component.occurrences.count - 1, -1, -1):
        existing = front.component.occurrences.item(i)
        if existing.component.name == LED_COMP:
            existing.deleteMe()
            nested_removed += 1

    # Versions of this script before the LED was nested created this exact
    # script-owned component at root. Remove it during migration; do not touch
    # other LED components or user-created root geometry.
    root_removed = 0
    for i in range(root.occurrences.count - 1, -1, -1):
        existing = root.occurrences.item(i)
        if existing.component.name == LED_COMP:
            existing.deleteMe()
            root_removed += 1
    if nested_removed or root_removed:
        out.append('  replaced %d nested and removed %d legacy root %s occurrence(s)'
                   % (nested_removed, root_removed, LED_COMP))

    occ = front.component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = LED_COMP

    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, V(cm(az)))
    pl = comp.constructionPlanes.add(pi)
    pl.name = 'PL_LED_POWER_AXIS'
    sk = comp.sketches.add(pl)
    sk.name = 'SK_LED_POWER_PROFILE'

    def s(x, y):
        return sk.modelToSketchSpace(P(cm(x), cm(y), cm(az)))

    # +Y runs from the front exterior face (Y=0) into the enclosure. The
    # additional source offset absorbs the existing 0.5 mm tail Move, so the
    # rebuilt source owns the final face position and needs no occurrence move.
    y_tip = -(protrude + extra_face_proud)
    y_dome = y_tip + rb
    y_barrel = y_dome + barrel_l
    y_back = y_barrel + flange_t

    lines = sk.sketchCurves.sketchLines
    a_tip = s(ax, y_tip)
    b_dome = s(ax + rb, y_dome)
    c_barrel = s(ax + rb, y_barrel)
    d_flange = s(ax + rf, y_barrel)
    e_flange = s(ax + rf, y_back)
    f_back = s(ax, y_back)

    arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(s(ax, y_dome), a_tip, math.pi / 2)
    barrel = lines.addByTwoPoints(b_dome, c_barrel)
    shoulder = lines.addByTwoPoints(c_barrel, d_flange)
    flange = lines.addByTwoPoints(d_flange, e_flange)
    back = lines.addByTwoPoints(e_flange, f_back)
    axis = lines.addByTwoPoints(f_back, a_tip)   # closes the profile on the axis

    if sk.profiles.count != 1:
        raise RuntimeError('LED profile did not close: %d profiles' % sk.profiles.count)

    # Make the source profile genuinely parametric without a Fix constraint.
    # The coincident/horizontal/vertical/tangent constraints describe its
    # topology; the six dimensions describe its LED parameters and placement.
    # Keeping the initial geometry on the negative X/Y branch is important:
    # Fusion distance dimensions are magnitudes, hence -ledHoleX and the
    # positive face-proud sum below.
    gc = sk.geometricConstraints

    def require(value, label):
        if value is None:
            raise RuntimeError('LED %s constraint failed' % label)
        return value

    for first, second in ((arc.endSketchPoint, barrel.startSketchPoint),
                          (barrel.endSketchPoint, shoulder.startSketchPoint),
                          (shoulder.endSketchPoint, flange.startSketchPoint),
                          (flange.endSketchPoint, back.startSketchPoint),
                          (back.endSketchPoint, axis.startSketchPoint),
                          (axis.endSketchPoint, arc.startSketchPoint)):
        require(gc.addCoincident(first, second), 'coincident')
    for line in (barrel, flange, axis):
        require(gc.addVertical(line), 'vertical')
    for line in (shoulder, back):
        require(gc.addHorizontal(line), 'horizontal')
    require(gc.addTangent(arc, barrel), 'dome tangent')
    # Tangency already fixes the centre's Y level; only its X alignment is
    # needed. A horizontal centre constraint would over-constrain the sketch.
    require(gc.addVerticalPoints(arc.centerSketchPoint, axis.endSketchPoint),
            'dome centre alignment')

    dims = sk.sketchDimensions

    def add_dim(dimension, expression, label):
        require(dimension, label + ' dimension')
        dimension.parameter.expression = expression

    add_dim(dims.addRadialDimension(arc, s(ax + 4, y_dome)),
            'ledBodyD / 2', 'body radius')
    add_dim(dims.addDistanceDimension(
        axis.endSketchPoint, flange.startSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        s(ax + 9, y_dome)), 'ledFlangeD / 2', 'flange radius')
    add_dim(dims.addDistanceDimension(
        barrel.startSketchPoint, barrel.endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        s(ax + 10, y_dome)), 'ledBarrelL', 'barrel length')
    add_dim(dims.addDistanceDimension(
        flange.startSketchPoint, flange.endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        s(ax + 12, y_back)), 'ledFlangeT', 'flange thickness')
    add_dim(dims.addDistanceDimension(
        sk.originPoint, axis.endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        s(ax / 2, y_tip - 2)), '-ledHoleX', 'axis X')
    if axis.endSketchPoint.geometry.x >= 0:
        raise RuntimeError('LED axis-X dimension selected the positive branch')
    add_dim(dims.addDistanceDimension(
        sk.originPoint, axis.endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        s(ax - 4, y_tip / 2)), 'ledProtrude + ledExtraFaceProud', 'tip Y')
    if axis.endSketchPoint.geometry.y >= 0:
        raise RuntimeError('LED tip-Y dimension selected the positive branch')
    if not sk.isFullyConstrained:
        raise RuntimeError('LED profile is not fully constrained')

    ri = comp.features.revolveFeatures.createInput(
        sk.profiles.item(0), axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ri.setAngleExtent(False, VS('360 deg'))
    rev = comp.features.revolveFeatures.add(ri)
    rev.name = 'FT_LED_POWER_REVOLVE'
    body = rev.bodies.item(0)
    body.name = LED_COMP

    ap = power_led_appearance(app, des)
    body.appearance = ap
    bb = body.boundingBox
    out.append('  axis (%.4f, %.4f), length %.2f mm, %.2f mm proud of the panel'
               % (ax, az, y_back - y_tip, protrude + extra_face_proud))
    out.append('  face proud = %.2f mm base + %.2f mm source offset; nested under %s'
               % (protrude, extra_face_proud, FRONT_COMP))
    out.append('  bbox X %.3f..%.3f  Y %.3f..%.3f  Z %.3f..%.3f'
               % (mm(bb.minPoint.x), mm(bb.maxPoint.x), mm(bb.minPoint.y),
                  mm(bb.maxPoint.y), mm(bb.minPoint.z), mm(bb.maxPoint.z)))
    out.append('  appearance %s' % (ap.name if ap else 'NONE FOUND'))


def run(_context):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    if des is None:
        raise RuntimeError('Active product is not a Design')
    root = des.rootComponent
    out = ['DOC %s' % app.activeDocument.name]

    fix_translucency(des, out)
    hide_legacy_caps(root, out)
    master, parent, placed = place_native_caps(des, root, out)
    make_red_power_cap(des, master, parent, out)
    build_led(app, des, root, out)

    if des.snapshots.hasPendingSnapshot:
        des.snapshots.add()

    # Light bulbs set in the same pass that creates an occurrence do not
    # stick, so switch the caps on here, after the geometry is committed.
    out.append('--- 5. VISIBILITY ---')
    switched = 0
    for k in parent.occurrences:
        if not k.isLightBulbOn:
            k.isLightBulbOn = True
            switched += 1
    visible = sum(1 for k in parent.occurrences if k.isLightBulbOn)
    out.append('  %d cap instances under %s, %d visible (%d switched on)'
               % (parent.occurrences.count, CAPS_PARENT, visible, switched))

    # The parked dev occurrence had to be switched on so the instances would
    # inherit a lit bulb; park it back out of sight now that they have one.
    for o in root.occurrences:
        if o.component.name == CAP_MASTER and o.isLightBulbOn:
            o.isLightBulbOn = False
            out.append('  parked dev occurrence %s hidden again' % o.name)
    out.append('  %d of %d cap instances still lit after parking'
               % (sum(1 for k in parent.occurrences if k.isLightBulbOn),
                  parent.occurrences.count))

    # Verify against the shells themselves; des.appearances hands out several
    # stale proxies per appearance and is not trustworthy as a check.
    out.append('--- 6. SHELL CHECK ---')
    for o in root.occurrences:
        if o.component.name not in ('FRONT_HALF', 'BACK_HALF'):
            continue
        b = o.component.bRepBodies.item(0)
        ap = b.appearance
        p = ap.appearanceProperties.itemByName('Translucency') if ap else None
        out.append('  %-11s %-12s appearance=%-12s translucency=%s'
                   % (o.component.name, b.name, ap.name if ap else 'None',
                      p.value if p is not None else 'n/a'))
    text = '\n'.join(out)
    with open(REPORT, 'w', encoding='utf-8') as fh:
        fh.write(text)
    print(text)
