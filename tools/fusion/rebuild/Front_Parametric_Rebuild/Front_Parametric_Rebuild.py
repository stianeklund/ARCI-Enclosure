"""Canonical native Fusion 360 rebuild of the ARCI enclosure front half.

Coordinates: X=width, Y=depth, Z=height.  From the exterior front, +X is
right and +Z is up.  Mechanical, mating, mounting, and AMS-text features are
kept in separate timeline groups for performance and downstream editing.
"""
import math
import adsk.core
import adsk.fusion


def mm(v): return v / 10.0
def vi(v): return adsk.core.ValueInput.createByString(v if isinstance(v, str) else f'{v} mm')
def point(x, y, z): return adsk.core.Point3D.create(mm(x), mm(y), mm(z))
def sp(sk, x, y, z): return sk.modelToSketchSpace(point(x, y, z))


def add_param(design, name, expression):
    unit = 'deg' if str(expression).strip().lower().endswith('deg') else 'mm'
    return (design.userParameters.itemByName(name) or
            design.userParameters.add(name, vi(expression), unit, 'ARCI canonical rebuild'))


def fix(items):
    for item in items: item.isFixed = True


def centered_parametric_rect(sk, w_expr, h_expr, w, h):
    x0, x1, z0, z1 = -w/2, w/2, -h/2, h/2
    ls = sk.sketchCurves.sketchLines
    a = ls.addByTwoPoints(sp(sk, x0, 0, z0), sp(sk, x1, 0, z0))
    b = ls.addByTwoPoints(a.endSketchPoint, sp(sk, x1, 0, z1))
    c = ls.addByTwoPoints(b.endSketchPoint, sp(sk, x0, 0, z1))
    d = ls.addByTwoPoints(c.endSketchPoint, a.startSketchPoint)
    gc = sk.geometricConstraints
    gc.addHorizontal(a); gc.addVertical(b); gc.addHorizontal(c); gc.addVertical(d)
    dims = sk.sketchDimensions
    q = dims.addDistanceDimension(a.startSketchPoint, a.endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(0, mm(h/2+8), 0)); q.parameter.expression = w_expr
    q = dims.addDistanceDimension(b.startSketchPoint, b.endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(mm(w/2+8), 0, 0)); q.parameter.expression = h_expr
    q = dims.addDistanceDimension(sk.originPoint, a.endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(mm(w/4), mm(h/2+14), 0)); q.parameter.expression = f'({w_expr})/2'
    q = dims.addDistanceDimension(sk.originPoint, a.endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(mm(w/2+14), mm(h/4), 0)); q.parameter.expression = f'({h_expr})/2'


def offset_parametric_rect(sk, cx_expr, cz_expr, w_expr, h_expr, cx, cz, w, h):
    """Create a fully constrained XZ rectangle driven by center and size parameters."""
    x0, x1, z0, z1 = cx-w/2, cx+w/2, cz-h/2, cz+h/2
    ls = sk.sketchCurves.sketchLines
    lines = [
        ls.addByTwoPoints(sp(sk, x0, 0, z0), sp(sk, x1, 0, z0)),
        ls.addByTwoPoints(sp(sk, x1, 0, z0), sp(sk, x1, 0, z1)),
        ls.addByTwoPoints(sp(sk, x1, 0, z1), sp(sk, x0, 0, z1)),
        ls.addByTwoPoints(sp(sk, x0, 0, z1), sp(sk, x0, 0, z0)),
    ]
    gc = sk.geometricConstraints
    for i in range(4):
        gc.addCoincident(lines[i].endSketchPoint, lines[(i+1) % 4].startSketchPoint)
    gc.addHorizontal(lines[0]); gc.addVertical(lines[1])
    gc.addHorizontal(lines[2]); gc.addVertical(lines[3])
    dims = sk.sketchDimensions
    q = dims.addDistanceDimension(lines[0].startSketchPoint, lines[0].endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(mm(cx), mm(h/2+8), 0)); q.parameter.expression = w_expr
    q = dims.addDistanceDimension(lines[1].startSketchPoint, lines[1].endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(mm(cx+w/2+8), 0, 0)); q.parameter.expression = h_expr
    bottom_right = lines[0].endSketchPoint
    q = dims.addDistanceDimension(sk.originPoint, bottom_right,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(mm(cx+w/2), mm(h/2+14), 0))
    q.parameter.expression = f'({cx_expr}) + ({w_expr})/2'
    q = dims.addDistanceDimension(sk.originPoint, bottom_right,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(mm(cx+w/2+14), mm(h/4), 0))
    q.parameter.expression = f'({h_expr})/2 - ({cz_expr})'
    return lines


def rect(sk, cx, cz, w, h):
    pts = [sp(sk, cx-w/2, 0, cz-h/2), sp(sk, cx+w/2, 0, cz-h/2),
           sp(sk, cx+w/2, 0, cz+h/2), sp(sk, cx-w/2, 0, cz+h/2)]
    ls = sk.sketchCurves.sketchLines
    out = [ls.addByTwoPoints(pts[i], pts[(i+1)%4]) for i in range(4)]
    fix(out); return out


def rounded_rect(sk, cx, cz, w, h, r):
    x0, x1, z0, z1, s = cx-w/2, cx+w/2, cz-h/2, cz+h/2, r/math.sqrt(2)
    ls, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    out = [
      ls.addByTwoPoints(sp(sk,x0+r,0,z0),sp(sk,x1-r,0,z0)),
      arcs.addByThreePoints(sp(sk,x1-r,0,z0),sp(sk,x1-r+s,0,z0+r-s),sp(sk,x1,0,z0+r)),
      ls.addByTwoPoints(sp(sk,x1,0,z0+r),sp(sk,x1,0,z1-r)),
      arcs.addByThreePoints(sp(sk,x1,0,z1-r),sp(sk,x1-r+s,0,z1-r+s),sp(sk,x1-r,0,z1)),
      ls.addByTwoPoints(sp(sk,x1-r,0,z1),sp(sk,x0+r,0,z1)),
      arcs.addByThreePoints(sp(sk,x0+r,0,z1),sp(sk,x0+r-s,0,z1-r+s),sp(sk,x0,0,z1-r)),
      ls.addByTwoPoints(sp(sk,x0,0,z1-r),sp(sk,x0,0,z0+r)),
      arcs.addByThreePoints(sp(sk,x0,0,z0+r),sp(sk,x0+r-s,0,z0+r-s),sp(sk,x0+r,0,z0))]
    fix(out); return out


def circle(sk, cx, cz, diameter):
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(sp(sk,cx,0,cz), mm(diameter/2))
    c.isFixed = True; return c


def profiles(sk):
    out = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count): out.add(sk.profiles.item(i))
    if not out.count: raise RuntimeError(f'{sk.name}: no closed profiles')
    return out


def annular_profiles(sk):
    """Return only ring profiles from sketches containing concentric circles."""
    out = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        profile = sk.profiles.item(i)
        if profile.profileLoops.count == 2:
            out.add(profile)
    if not out.count:
        raise RuntimeError(f'{sk.name}: no annular profiles')
    return out


def parametric_circle(sk, cx, cz, diameter_expr, nominal_diameter):
    """Create a fixed-center circle with a user-parameter-driven diameter."""
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        sp(sk, cx, 0, cz), mm(nominal_diameter / 2))
    c.centerSketchPoint.isFixed = True
    dim = sk.sketchDimensions.addDiameterDimension(
        c, sp(sk, cx + nominal_diameter / 2 + 3, 0, cz + 3))
    dim.parameter.expression = diameter_expr
    return c


def positioned_parametric_circle(sk, cx_expr, cz_expr, diameter_expr,
                                 cx, cz, nominal_diameter):
    """Create a circle whose center and diameter are driven by user parameters."""
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        sp(sk, cx, 0, cz), mm(nominal_diameter / 2))
    dims = sk.sketchDimensions
    q = dims.addDistanceDimension(
        sk.originPoint, c.centerSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        sp(sk, cx / 2, 0, cz - 6))
    q.parameter.expression = cx_expr
    # XZ sketches use local +Y for model -Z.
    q = dims.addDistanceDimension(
        sk.originPoint, c.centerSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        sp(sk, cx + 8, 0, cz / 2))
    q.parameter.expression = f'-({cz_expr})'
    q = dims.addDiameterDimension(
        c, sp(sk, cx + nominal_diameter / 2 + 3, 0, cz + 3))
    q.parameter.expression = diameter_expr
    return c


def positioned_parametric_concentric_pair(sk, cx_expr, cz_expr, cx, cz,
                                           outer_expr, outer_d,
                                           inner_expr, inner_d):
    """Create a concentric pair with one parameter-driven center datum."""
    circles = [
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sp(sk, cx, 0, cz), mm(outer_d / 2)),
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            sp(sk, cx, 0, cz), mm(inner_d / 2)),
    ]
    sk.geometricConstraints.addConcentric(circles[0], circles[1])
    dims = sk.sketchDimensions
    q = dims.addDistanceDimension(
        sk.originPoint, circles[0].centerSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        sp(sk, cx / 2, 0, cz - 6))
    q.parameter.expression = cx_expr
    q = dims.addDistanceDimension(
        sk.originPoint, circles[0].centerSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        sp(sk, cx + 8, 0, cz / 2))
    q.parameter.expression = f'-({cz_expr})'
    for circle_entity, expression, nominal in (
            (circles[0], outer_expr, outer_d),
            (circles[1], inner_expr, inner_d)):
        q = dims.addDiameterDimension(
            circle_entity, sp(sk, cx + nominal / 2 + 3, 0, cz + 3))
        q.parameter.expression = expression
    return circles


def extrude(comp, prof, op, distance, start=None, taper=None, name=None, body=None):
    inp = comp.features.extrudeFeatures.createInput(prof, op)
    if start is not None: inp.startExtent = adsk.fusion.OffsetStartDefinition.create(vi(start))
    inp.setDistanceExtent(False, vi(distance))
    if taper: inp.taperAngle = adsk.core.ValueInput.createByString(taper)
    if body and op == adsk.fusion.FeatureOperations.CutFeatureOperation: inp.participantBodies = [body]
    feat = comp.features.extrudeFeatures.add(inp)
    if name: feat.name = name
    return feat


def outer_fillet(comp, body):
    edges, tol = adsk.core.ObjectCollection.create(), mm(.02)
    for e in body.edges:
        b = e.boundingBox
        if ((abs(b.minPoint.y)<tol and abs(b.maxPoint.y-mm(30))<tol) or
            (abs(b.minPoint.y)<tol and abs(b.maxPoint.y)<tol)): edges.add(e)
    if edges.count != 8: raise RuntimeError(f'Expected 8 front fillet edges, found {edges.count}')
    inp = comp.features.filletFeatures.createInput(); inp.isRollingBallCorner = False
    inp.addConstantRadiusEdgeSet(edges, vi('outerCornerR'), True)
    feat = comp.features.filletFeatures.add(inp); feat.name = 'FT_FRONT_COMBINED_SETBACK_FILLET'


def plane(comp, base, offset, name):
    inp = comp.constructionPlanes.createInput(); inp.setByOffset(base, vi(offset))
    p = comp.constructionPlanes.add(inp); p.name = name; return p


def plane_rect(sk, center, aa, ab, sa, sb):
    cx,cy,cz=center; ax,ay,az=aa; bx,by,bz=ab; pts=[]
    for ia,ib in ((-1,-1),(1,-1),(1,1),(-1,1)):
        pts.append(sk.modelToSketchSpace(point(cx+ia*ax*sa/2+ib*bx*sb/2,
            cy+ia*ay*sa/2+ib*by*sb/2, cz+ia*az*sa/2+ib*bz*sb/2)))
    ls=sk.sketchCurves.sketchLines; out=[ls.addByTwoPoints(pts[i],pts[(i+1)%4]) for i in range(4)]
    fix(out)


def notch(comp, pl, name, centers, aa, ab, depth):
    sk=comp.sketches.add(pl); sk.name=f'SK_FRONT_LIP_NOTCHES_{name}'
    for center in centers: plane_rect(sk,center,aa,ab,10,2)
    feat=extrude(comp,profiles(sk),adsk.fusion.FeatureOperations.CutFeatureOperation,
                 depth,taper='-45 deg',name=f'FT_FRONT_LIP_NOTCHES_{name}')
    crown_edges=adsk.core.ObjectCollection.create()
    for i in range(feat.endFaces.count):
        end_face=feat.endFaces.item(i)
        for edge in end_face.edges:
            if edge.length>mm(5): crown_edges.add(edge)
    if crown_edges.count!=6:
        raise RuntimeError(f'Expected 6 {name} notch crown edges, found {crown_edges.count}')
    fillet_input=comp.features.filletFeatures.createInput()
    fillet_input.addConstantRadiusEdgeSet(crown_edges,vi('backDetentCrownRadius'),True)
    crown=comp.features.filletFeatures.add(fillet_input)
    crown.name=f'FT_FRONT_LIP_NOTCH_CROWNS_{name}'
    sk.isVisible=False; return feat


BND_MINUS = 'BND ' + chr(0x2013)


# The 27 rectangular-button labels use the production 5.15 mm nominal
# center offset, 0.40 mm above the v66-matched placement.  This leaves
# 1.17-1.22 mm of printable land above each 10 x 5 mm opening.
LABELS=[('F1',-62.65,-41.193863),('F2',-44.65,-41.193863),('F3',-26.65,-41.219442),
('F4',-8.65,-41.193863),('F5',9.35,-41.225582),('F6',27.35,-41.219442),
('PWR',-113,5.81),('SEND',-98,5.808977),('PRE',-113,17.810001),('ATT',-98,17.810001),
('TUNE',-113,29.784419),('PROC',-98,29.809999),('VOX',-113,41.809999),
('XVTR',-98,41.809999),('POWER',-98,53.809998),('CLR',61.5,8.81),('MODE',76.5,8.81),
('ENT',91.5,8.81),(BND_MINUS,61.5,20.808977),('A / B',76.5,20.81),('SPLIT',91.5,20.808977),
('BND +',61.5,32.808975),('RIT',76.5,32.809998),('XIT',91.5,32.809998),
('NTCH',61.5,44.810001),('NR',76.5,44.810001),('NB',91.5,44.810001),
('MULTI',-106,-11.025579),
# Dual-encoder legends in the original v66 stack, centered on the encoder
# shaft X: SHIFT above the upper encoder, WIDTH below it, AF / RF above the
# lower encoder.  Two graphic variants (single-line SHIFT-(o)-WIDTH with
# leaders, and a two-row dot/ring legend) were tried on 2026-09-02 and
# rejected; the words alone at the panel's 4 mm size are the cleanest print.
('SHIFT',113,50.998977),('WIDTH',113,27.598299),('AF / RF',113,16.444501)]


DUAL_ENCODER_LABELS = {'SHIFT', 'WIDTH', 'AF / RF'}


def label_entities(sk, design):
    """Create the 31 labels as multi-line texts (createInput2).

    Center/middle alignment inside a box centred on the label datum puts the
    cap-height box exactly on the target, so no post-placement is needed.
    Multi-line texts expose characterSpacing; legacy createInput texts do not.
    NOTE: SketchText proxies returned by add() go stale after further sketch
    edits, so the collection handed to the extrudes must be re-read from
    sk.sketchTexts, and each extrude should run in its own transaction.
    """
    label_height=design.userParameters.itemByName('frontLabelHeight').value
    encoder_height=design.userParameters.itemByName('encoderLegendHeight').value
    spacing=design.userParameters.itemByName('frontLabelSpacingPct').value
    for label,cx,cz in LABELS:
        height=encoder_height if label in DUAL_ENCODER_LABELS else label_height
        c=sp(sk,cx,0,cz); inp=sk.sketchTexts.createInput2(label,height)
        inp.setAsMultiLine(adsk.core.Point3D.create(c.x-1.5,c.y-0.3,0),
                           adsk.core.Point3D.create(c.x+1.5,c.y+0.3,0),
                           adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                           adsk.core.VerticalAlignments.MiddleVerticalAlignment,spacing)
        inp.fontName='Arial'
        inp.textStyle=adsk.fusion.TextStyles.TextStyleBold
        inp.angle=math.pi
        sk.sketchTexts.add(inp)
    anchor_button_labels(sk, design)
    out=adsk.core.ObjectCollection.create()
    for i in range(sk.sketchTexts.count): out.add(sk.sketchTexts.item(i))
    return out


# Button centers for the 27 button labels (canonical model X, Z).  The label
# center sits buttonLabelOffset above the button center; the multi-line text
# box is 30 x 6 mm centered on the label, so its upper-right corner is at
# (btnX + 15, btnZ + buttonLabelOffset + 3).
BUTTON_CENTERS={('F%d'%(k+1)):(-62.65+18*k,-46.35) for k in range(6)}
BUTTON_CENTERS.update({'PWR':(-113,0.66),'SEND':(-98,0.66),'PRE':(-113,12.66),'ATT':(-98,12.66),
    'TUNE':(-113,24.66),'PROC':(-98,24.66),'VOX':(-113,36.66),'XVTR':(-98,36.66),'POWER':(-98,48.66),
    'CLR':(61.5,3.66),'MODE':(76.5,3.66),'ENT':(91.5,3.66),BND_MINUS:(61.5,15.66),'A / B':(76.5,15.66),
    'SPLIT':(91.5,15.66),'BND +':(61.5,27.66),'RIT':(76.5,27.66),'XIT':(91.5,27.66),
    'NTCH':(61.5,39.66),'NR':(76.5,39.66),'NB':(91.5,39.66)})


def anchor_button_labels(sk, design):
    """Dimension each button label's text box from the sketch origin so that
    buttonLabelOffset drives the label height from the Parameters dialog.
    Sketch axes here are x = -X, y = -Z; distance dimensions are magnitudes,
    hence the sign handling."""
    off=design.userParameters.itemByName('buttonLabelOffset').value*10
    dims=sk.sketchDimensions
    for i in range(sk.sketchTexts.count):
        t=sk.sketchTexts.item(i)
        if t.text not in BUTTON_CENTERS: continue
        bx,bz=BUTTON_CENTERS[t.text]
        lines=list(t.definition.rectangleLines)
        pts=[L.startSketchPoint for L in lines]+[L.endSketchPoint for L in lines]
        top=min(pts,key=lambda p:(p.geometry.x,p.geometry.y))      # model (bx+15, bz+off+3)
        bot=max(pts,key=lambda p:(p.geometry.y,-p.geometry.x))     # model (bx+15, bz+off-3)
        g=top.geometry; gb=bot.geometry
        ztop='%s(%.6g mm + buttonLabelOffset + 3 mm)'%('-' if bz+off+3<0 else '',bz)
        zbot='%s(%.6g mm + buttonLabelOffset - 3 mm)'%('-' if bz+off-3<0 else '',bz)
        xexpr='%s(%.6g mm + 15 mm)'%('-' if bx+15<0 else '',bx)
        # Both corners must be pinned: with only the top corner dimensioned the
        # solver stretches the box instead of translating it, and the
        # middle-aligned text then moves by half the intended amount.
        dv=dims.addDistanceDimension(sk.originPoint,top,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            adsk.core.Point3D.create(g.x-0.4,g.y/2,0)); dv.parameter.expression=ztop
        db=dims.addDistanceDimension(sk.originPoint,bot,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            adsk.core.Point3D.create(gb.x-0.8,gb.y/2,0)); db.parameter.expression=zbot
        dh=dims.addDistanceDimension(sk.originPoint,top,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            adsk.core.Point3D.create(g.x/2,g.y-0.4,0)); dh.parameter.expression=xexpr


def group(design,start,name):
    end=design.timeline.count-1
    if end>=start:
        g=design.timeline.timelineGroups.add(start,end)
        if g: g.name=name


def add_control_collars(design, comp, body):
    """Recreate the five rear control collars measured from Front_Half.step."""
    for n, e in [
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
        add_param(design, n, e)

    start = design.timeline.count
    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = 'SK_FRONT_CONTROL_COLLARS_STANDARD'
    for x, z, od_expr, od, id_expr, inner_d in [
        (-106, -46, 'collarMultiOD', 24, 'rotaryMultiHoleD', 15.8),
        (-106, -22, 'collarTuneOD', 18.3, 'rotaryTuneHoleD', 8.4),
        (113, 2.9983, 'collarRightOD', 13.6, 'rotaryRightHoleD', 6.8),
        (113, 39.9983, 'collarRightOD', 13.6, 'rotaryRightHoleD', 6.8),
    ]:
        parametric_circle(sk, x, z, od_expr, od)
        parametric_circle(sk, x, z, id_expr, inner_d)
    extrude(comp, annular_profiles(sk),
            adsk.fusion.FeatureOperations.JoinFeatureOperation,
            'collarStandardDepth', start='frontThickness',
            name='FT_FRONT_CONTROL_COLLARS_STANDARD')
    sk.isVisible = False

    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = 'SK_FRONT_CONTROL_COLLAR_AFRF_PRIMARY'
    positioned_parametric_concentric_pair(
        sk, 'vfoCenterX', 'vfoCenterZ', 76.5, -33.6,
        'collarAFRFOD', 21, 'rotaryAFRFHoleD', 8.85)
    extrude(comp, annular_profiles(sk),
            adsk.fusion.FeatureOperations.JoinFeatureOperation,
            'collarAFRFDepth-collarAFRFBoreStepDepth',
            start='frontThickness',
            name='FT_FRONT_CONTROL_COLLAR_AFRF_PRIMARY')
    sk.isVisible = False

    sk = comp.sketches.add(comp.xZConstructionPlane)
    sk.name = 'SK_FRONT_CONTROL_COLLAR_AFRF_COUNTERBORE'
    positioned_parametric_concentric_pair(
        sk, 'vfoCenterX', 'vfoCenterZ', 76.5, -33.6,
        'collarAFRFOD', 21, 'collarAFRFBoreStepD', 13)
    extrude(comp, annular_profiles(sk),
            adsk.fusion.FeatureOperations.JoinFeatureOperation,
            'collarAFRFBoreStepDepth',
            start='frontThickness+collarAFRFDepth-collarAFRFBoreStepDepth',
            name='FT_FRONT_CONTROL_COLLAR_AFRF_COUNTERBORE')
    sk.isVisible = False
    group(design, start, 'FRONT HALF - CONTROL SUPPORT COLLARS')


def run(_context: str):
    app=adsk.core.Application.get(); design=adsk.fusion.Design.cast(app.activeProduct)
    if not design or design.designType!=adsk.fusion.DesignTypes.ParametricDesignType:
        raise RuntimeError('Open a parametric Fusion design')
    comp=next((c for c in design.allComponents if c.name=='FRONT_HALF'),design.rootComponent)
    if any(b.name=='FRONT_SHELL' for b in comp.bRepBodies): raise RuntimeError('FRONT_SHELL already exists')
    for n,e in [('caseWidth','254 mm'),('caseHeight','130 mm'),('frontDepth','30 mm'),
      ('frontThickness','3 mm'),('wallThickness','4 mm'),('outerCornerR','1.9 mm'),
      ('lipStart','24.04 mm'),('lipInset','2 mm'),('dispBevelDepth','2.05 mm'),
      ('dispBevelAngle','45 deg'),('dispApertureW','110.32 mm'),('dispApertureH','62.28 mm'),
      ('dispCenterX','-18.5246 mm'),('dispCenterZ','11.7106 mm'),
      ('dispOpenW','dispApertureW + 2 * dispBevelDepth * tan(dispBevelAngle)'),
      ('dispOpenH','dispApertureH + 2 * dispBevelDepth * tan(dispBevelAngle)'),
      ('backDetentCrownRadius','0.4 mm'),
      ('rotaryRecessDepthDeep','2 mm'),('rotaryRecessDepthShallow','1.5 mm'),
      # Multi-line text engine: height is the true cap height (v66 evaluated
      # cap = 2.9 mm).  +18 % character spacing keeps every inter-letter black
      # gap >= ~0.44 mm, i.e. above one 0.4 mm nozzle line (XVTR was 0.09 mm).
      ('frontLabelHeight','2.9 mm'),('frontLabelSpacingPct','22'),
      ('ledHoleX','-112 mm'),('ledHoleZ','52.1731 mm'),
      ('labelDepth','0.6 mm'),('labelInlayRecess','0 mm'),('bossH','8.2 mm'),
      ('bossTallH','11.04 mm'),('mountTapDrillD','2.529 mm'),
      ('mountPilotBaseStandard','2 mm'),('mountPilotBasePower','2.7 mm'),
      ('mountPilotBaseFKey','3.474 mm'),('mountPilotBaseEncoder','6.65 mm'),
      ('buttonLabelOffset','5.15 mm'),('rightButtonMatrixCenterX','76.5 mm'),
      ('vfoCenterX','rightButtonMatrixCenterX'),('vfoCenterZ','-33.6 mm'),
      ('vfoRecessD','16 mm'),('rotaryAFRFHoleD','8.85 mm'),
      ('rightDualEncoderCenterX','113 mm'),('encoderLegendCenterX','rightDualEncoderCenterX'),
      ('encoderUpperLegendZ','50.998977 mm'),('encoderWidthLegendZ','27.598299 mm'),
      ('encoderLowerLegendZ','16.444501 mm'),
      ('encoderLegendHeight','frontLabelHeight')]: add_param(design,n,e)

    start=design.timeline.count
    sk=comp.sketches.add(comp.xZConstructionPlane); sk.name='SK_FRONT_OUTER_PROFILE'
    centered_parametric_rect(sk,'caseWidth','caseHeight',254,130)
    ft=extrude(comp,sk.profiles.item(0),adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
               'frontDepth',name='FT_FRONT_OUTER_BODY'); body=ft.bodies.item(0); body.name='FRONT_SHELL'
    outer_fillet(comp,body)
    sk=comp.sketches.add(comp.xZConstructionPlane); sk.name='SK_FRONT_INNER_CAVITY'
    centered_parametric_rect(sk,'caseWidth-2*wallThickness','caseHeight-2*wallThickness',246,122)
    extrude(comp,sk.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation,
            'frontDepth-frontThickness',start='frontThickness',name='FT_FRONT_INNER_CAVITY_CUT',body=body)
    sk=comp.sketches.add(comp.xZConstructionPlane); sk.name='SK_FRONT_LIP_RELIEF'
    centered_parametric_rect(sk,'caseWidth','caseHeight',254,130)
    centered_parametric_rect(sk,'caseWidth-2*lipInset','caseHeight-2*lipInset',250,126)
    # Nested rectangles create one large inner profile and one narrow outer
    # ring.  Only the ring is removed so the mating tongue remains intact.
    ring=min((sk.profiles.item(i) for i in range(sk.profiles.count)),key=lambda p:p.areaProperties().area)
    extrude(comp,ring,adsk.fusion.FeatureOperations.CutFeatureOperation,'frontDepth-lipStart',
            start='lipStart',name='FT_FRONT_LIP_RELIEF_CUT',body=body)
    sk=comp.sketches.add(comp.xZConstructionPlane); sk.name='SK_FRONT_DISPLAY_BEVEL'
    offset_parametric_rect(sk,'dispCenterX','dispCenterZ','dispOpenW','dispOpenH',
                           -18.5246,11.7106,114.42,66.38)
    extrude(comp,sk.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation,
            'dispBevelDepth',taper='-dispBevelAngle',name='FT_FRONT_DISPLAY_BEVEL_CUT',body=body)
    sk=comp.sketches.add(comp.xZConstructionPlane); sk.name='SK_FRONT_DISPLAY_APERTURE'
    offset_parametric_rect(sk,'dispCenterX','dispCenterZ','dispApertureW','dispApertureH',
                           -18.5246,11.7106,110.32,62.28)
    extrude(comp,sk.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation,
            'frontThickness+0.2 mm',name='FT_FRONT_DISPLAY_APERTURE_CUT',body=body)
    sk=comp.sketches.add(comp.xZConstructionPlane); sk.name='SK_FRONT_BUTTON_CUTOUTS'
    for i in range(6): rounded_rect(sk,-62.65+i*18,-46.35,10,5,.5)
    for ix in range(2):
        for iz in range(4): rounded_rect(sk,-113+ix*15,.66+iz*12,10,5,.5)
    rounded_rect(sk,-98,48.66,10,5,.5)
    for ix in range(3):
        for iz in range(4): rounded_rect(sk,61.5+ix*15,3.66+iz*12,10,5,.5)
    extrude(comp,profiles(sk),adsk.fusion.FeatureOperations.CutFeatureOperation,
            'frontThickness+0.2 mm',name='FT_FRONT_BUTTON_CUTS',body=body)
    sk=comp.sketches.add(comp.xZConstructionPlane); sk.name='SK_FRONT_ROTARY_THROUGH'
    for x,z,d in [(-106,-46,15.8),(-106,-22,8.4),(113,2.9983,6.8),
                  (113,39.9983,6.8)]: circle(sk,x,z,d)
    positioned_parametric_circle(
        sk,'vfoCenterX','vfoCenterZ','rotaryAFRFHoleD',76.5,-33.6,8.85)
    # Power LED hole.  Originally at (-108.9894, 52.1731) on the PCB LED axis;
    # moved left so POWER can carry full letter spacing.  The LED does not
    # need to be coaxial with the PCB part.
    positioned_parametric_circle(
        sk,'ledHoleX','ledHoleZ','auxHoleD',-112,52.1731,3.5)
    extrude(comp,profiles(sk),adsk.fusion.FeatureOperations.CutFeatureOperation,
            'frontThickness+0.2 mm',name='FT_FRONT_ROTARY_THROUGH_CUTS',body=body)
    for name,items,depth in [('DEEP',[(-106,-46,19),(-106,-22,15)],'rotaryRecessDepthDeep'),
                             ('SHALLOW',[(113,2.9983,14.6),(113,39.9983,14.6)],'rotaryRecessDepthShallow')]:
        sk=comp.sketches.add(comp.xZConstructionPlane); sk.name=f'SK_FRONT_ROTARY_RECESSES_{name}'
        for x,z,d in items: circle(sk,x,z,d)
        if name=='DEEP':
            positioned_parametric_circle(
                sk,'vfoCenterX','vfoCenterZ','vfoRecessD',76.5,-33.6,16)
        extrude(comp,profiles(sk),adsk.fusion.FeatureOperations.CutFeatureOperation,depth,
                name=f'FT_FRONT_ROTARY_RECESSES_{name}',body=body)
    group(design,start,'FRONT HALF - MECHANICAL')

    start=design.timeline.count
    top=plane(comp,comp.xYConstructionPlane,63,'PL_FRONT_LIP_TOP')
    bottom=plane(comp,comp.xYConstructionPlane,-63,'PL_FRONT_LIP_BOTTOM')
    right=plane(comp,comp.yZConstructionPlane,125,'PL_FRONT_LIP_RIGHT')
    left=plane(comp,comp.yZConstructionPlane,-125,'PL_FRONT_LIP_LEFT')
    xs=[-100,.5,101]; zs=[38,0,-38]
    notch(comp,top,'TOP',[(x,27,63) for x in xs],(1,0,0),(0,1,0),-.8343)
    notch(comp,bottom,'BOTTOM',[(x,27,-63) for x in xs],(1,0,0),(0,1,0),.8343)
    notch(comp,right,'RIGHT',[(125,27,z) for z in zs],(0,0,1),(0,1,0),-.7929)
    notch(comp,left,'LEFT',[(-125,27,z) for z in zs],(0,0,1),(0,1,0),.7929)
    group(design,start,'FRONT HALF - MATING LIP AND NOTCHES')

    start=design.timeline.count
    # Left matrix: 27 mm lower-hole pitch; upper hole +9.5 X / +53 Z
    # from the lower-left hole, measured from the imported PCB.
    short=[(-118.365,-7.3637,6.4),(-91.365,-7.3637,6.4),(-108.865,45.6363,7),
      (-74.6641,-55.0928,7),(-74.6641,-38.0008,7),(36.0629,-55.0928,7),
      (36.0629,-38.0008,7),(55.6,-3.712,7),(55.7,47.46,7),(98.9,-3.712,7),(99,47.46,7)]
    tall=[(106.725,-16.475,7.5),(106.725,55.075,7.5),(119.275,-16.475,6.5),(119.275,55.075,6.5)]
    for name,items,height in [('SHORT',short,'bossH'),('TALL',tall,'bossTallH')]:
        sk=comp.sketches.add(comp.xZConstructionPlane); sk.name=f'SK_FRONT_MOUNT_BOSSES_{name}'
        for x,z,d in items: circle(sk,x,z,d)
        extrude(comp,profiles(sk),adsk.fusion.FeatureOperations.JoinFeatureOperation,height,
                start='frontThickness',name=f'FT_FRONT_MOUNT_BOSSES_{name}')
    groups=[('STANDARD',[short[i] for i in (0,1,7,8,9,10)],'bossH','mountPilotBaseStandard'),
            ('POWER',[short[2]],'bossH','mountPilotBasePower'),
            ('FKEY',[short[i] for i in (3,4,5,6)],'bossH','mountPilotBaseFKey'),
            ('ENCODER',tall,'bossTallH','mountPilotBaseEncoder')]
    for name,items,height,base in groups:
        sk=comp.sketches.add(comp.xZConstructionPlane); sk.name=f'SK_FRONT_M3_PILOTS_{name}'
        for x,z,_ in items: circle(sk,x,z,2.529)
        extrude(comp,profiles(sk),adsk.fusion.FeatureOperations.CutFeatureOperation,
                f'-({height}-{base})',start=f'frontThickness+{height}',name=f'FT_FRONT_M3_PILOTS_{name}',body=body)
    # Cosmetic ISO threads preserve the M3 specification without the severe
    # regeneration/mesh cost of modeled helical thread geometry.
    thread_faces=adsk.core.ObjectCollection.create()
    for face in body.faces:
        geometry=face.geometry
        if (geometry and geometry.objectType==adsk.core.Cylinder.classType() and
                abs(geometry.radius-mm(1.2645))<mm(.001)):
            thread_faces.add(face)
    if thread_faces.count!=15:
        raise RuntimeError(f'Expected 15 M3 pilot cylinders, found {thread_faces.count}')
    thread_features=comp.features.threadFeatures
    thread_info=thread_features.createThreadInfo(True,'ISO Metric profile','M3x0.5','6H')
    thread_input=thread_features.createInput(thread_faces,thread_info)
    thread_input.isModeled=False; thread_input.isFullLength=True
    thread_feature=thread_features.add(thread_input)
    thread_feature.name='FT_FRONT_M3x0_5_COSMETIC_THREADS'
    group(design,start,'FRONT HALF - MOUNTING BOSSES AND M3 PILOTS')

    add_control_collars(design, comp, body)

    start=design.timeline.count
    # Put manufacturing text on the actual exterior face.  This gives the
    # sketch the outward -Y normal and avoids the mirrored/back-side text
    # basis produced by the component XZ construction plane.
    front_faces=[]
    for face in body.faces:
        box=face.boundingBox
        if abs(box.minPoint.y)<mm(.01) and abs(box.maxPoint.y)<mm(.01): front_faces.append(face)
    if not front_faces: raise RuntimeError('Could not resolve front exterior face for labels')
    front_face=max(front_faces,key=lambda f:f.area)
    sk=comp.sketches.add(front_face); sk.name='SK_FRONT_LABELS_NATIVE'
    entities=label_entities(sk,design)
    extrude(comp,entities,adsk.fusion.FeatureOperations.CutFeatureOperation,'-labelDepth',
            name='FT_FRONT_LABEL_DEBOSS_CUT',body=body)
    inlay=extrude(comp,entities,adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                  '-(labelDepth-labelInlayRecess)',start='-labelInlayRecess',name='FT_FRONT_AMS_WHITE_TEXT_INLAY')
    for b in inlay.bodies:
        box=b.boundingBox; cx=(box.minPoint.x+box.maxPoint.x)*5; cz=(box.minPoint.z+box.maxPoint.z)*5
        label=min(LABELS,key=lambda q:(cx-q[1])**2+(cz-q[2])**2)[0]
        slug=(label.replace(' / ','_').replace('/','_').replace('+','PLUS')
              .replace(chr(0x2013),'MINUS').replace('-','MINUS').replace(' ',''))
        b.name='INLAY_FRONT_'+slug

    group(design,start,'PRINT - AMS FRONT LABELS')
    for sk in comp.sketches: sk.isVisible=False
    print('FRONT_SHELL created',round(body.volume*1000,6),'inlays',inlay.bodies.count)


def stop(_context: str): pass
