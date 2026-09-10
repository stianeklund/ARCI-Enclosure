"""Parametric tilt stand for the ARCI enclosure (rebuild of 'Tilt Feet ARCI v41').

Run inside Fusion 360 via the MCP script runner on the Rev3 master.

Concept (from the user's Maestro-style feet): a flat desk pad per side, the enclosure pivots
on a hinge carried by a bracket plate screwed to the rear panel. Improvements applied:
 1/2 radial castellation teeth on both hinge faces (positive angle steps, both sides match)
 3   pivot placed behind the rear panel so nothing swings into the pad; plate bottom rests on the
     pad top at 0 deg and acts as the flat stop (7)
 4   M3 screws into bosses inside the rear wall instead of M4 into a 4 mm wall
 5   4.4 mm holes on 3 mm screws (was 6 mm on 4 mm)
 6   O14 hinge barrel / O5.4 bore, ears in double shear (clevis) instead of side-by-side knuckles
Assembly ownership follows the manufactured parts: the enclosure-integral bosses
stay in BACK_HALF, while the removable parts are nested as
TILT_STAND_ASSEMBLY -> two instances of STAND_HINGE -> STAND_BRACKET +
STAND_PAD.  Hardware is added to STAND_HINGE by Stand_Hardware_Build.py.

Hardware per side: M5 x 30 partially threaded bolt + washer + nyloc nut,
2 x M3 x 12 countersunk screws, and two O28 x 3 rubber discs. Parameters are
'stand*'. Entry point: run(context).

Rerun policy: a complete existing stand build is preserved as a validated
no-op. A partial or duplicate script-owned target set fails before any model
mutation. This builder does not retrofit constraints into an existing build.
"""
import adsk.core, adsk.fusion, math

def mm(v): return round(v*10,3)
def p3(p): return (mm(p.x),mm(p.y),mm(p.z))
P=adsk.core.Point3D.create
V=adsk.core.ValueInput.createByReal
VS=adsk.core.ValueInput.createByString
POS=adsk.fusion.ExtentDirections.PositiveExtentDirection
NEG=adsk.fusion.ExtentDirections.NegativeExtentDirection
NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
def cm(v): return v/10.0

def plane(comp, base, offset_mm, name):
    pi=comp.constructionPlanes.createInput(); pi.setByOffset(base, V(cm(offset_mm)))
    pl=comp.constructionPlanes.add(pi); pl.name=name; return pl
def sk_xy(comp, z, name):
    sk=comp.sketches.add(plane(comp, comp.xYConstructionPlane, z, 'PL_'+name)); sk.name='SK_'+name; return sk
def sk_yz(comp, x, name):
    sk=comp.sketches.add(plane(comp, comp.yZConstructionPlane, x, 'PL_'+name)); sk.name='SK_'+name; return sk
def sk_xz(comp, y, name):
    sk=comp.sketches.add(plane(comp, comp.xZConstructionPlane, y, 'PL_'+name)); sk.name='SK_'+name; return sk
def s(sk, x,y,z): return sk.modelToSketchSpace(P(cm(x),cm(y),cm(z)))
def circle(sk, c, d_mm): return sk.sketchCurves.sketchCircles.addByCenterRadius(c, cm(d_mm/2))


def parameter_circle(sk, c, d_mm, x_expression, y_expression, diameter_expression):
    """Create a fully constrained circle using existing stand parameters.

    The stand mounting sketches live on XZ planes, so their local X/Y values
    are deliberately supplied by the caller.  The small nudge prevents Fusion
    from inferring a redundant horizontal/vertical relationship before the
    named driving dimensions are added; the dimensions immediately restore
    the exact intended centre and diameter.
    """
    result = circle(sk, c, d_mm)
    center = result.centerSketchPoint
    center.move(adsk.core.Vector3D.create(0.0037, 0.0041, 0))
    point = center.geometry
    dims = sk.sketchDimensions
    dims.addDiameterDimension(
        result, adsk.core.Point3D.create(point.x + 1.2, point.y + 1.2, 0)
    ).parameter.expression = diameter_expression
    dims.addDistanceDimension(
        sk.originPoint, center,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(point.x / 2.0, point.y + 2.2, 0)
    ).parameter.expression = x_expression
    dims.addDistanceDimension(
        sk.originPoint, center,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(point.x + 2.2, point.y / 2.0, 0)
    ).parameter.expression = y_expression
    return result


def preflight_existing_stand_build(root):
    """Return True for a complete existing build, False for a fresh document.

    Any incomplete or duplicated script-owned target set is rejected before
    parameter edits, legacy cleanup, or new geometry creation can occur.
    """
    assemblies = [
        occurrence for occurrence in root.occurrences
        if occurrence.component and occurrence.component.name == 'TILT_STAND_ASSEMBLY'
    ]
    backs = [
        occurrence for occurrence in root.occurrences
        if occurrence.component and occurrence.component.name == 'BACK_HALF'
    ]
    if len(backs) != 1:
        raise RuntimeError(
            'Expected exactly one root BACK_HALF occurrence before building the tilt stand; '
            f'found {len(backs)}.'
        )
    back = backs[0].component
    sketches = {
        name: sum(1 for sketch in back.sketches if sketch.name == name)
        for name in ('SK_STAND_BOSSES', 'SK_STAND_PILOTS')
    }
    features = {
        name: sum(1 for feature in back.features.extrudeFeatures if feature.name == name)
        for name in ('FT_STAND_BOSSES', 'FT_STAND_PILOTS')
    }
    target_count = len(assemblies) + sum(sketches.values()) + sum(features.values())
    if target_count == 0:
        return False
    if len(assemblies) == 1 and all(count == 1 for count in sketches.values()) and all(
            count == 1 for count in features.values()):
        print('Tilt stand preflight: complete existing build preserved as validated no-op.')
        return True
    raise RuntimeError(
        'Tilt stand preflight found a partial or duplicate script-owned target set; '
        f'assemblies={len(assemblies)}, sketches={sketches}, features={features}. '
        'No model changes were made.'
    )


def poly(sk, pts):
    n=len(pts)
    for i in range(n): sk.sketchCurves.sketchLines.addByTwoPoints(pts[i], pts[(i+1)%n])
def extrude(comp, sk, dist, direction, op, name, bodies=None, expr=None, profiles=None):
    coll=adsk.core.ObjectCollection.create()
    if profiles is None:
        for i in range(sk.profiles.count): coll.add(sk.profiles.item(i))
    else:
        for p in profiles: coll.add(p)
    ei=comp.features.extrudeFeatures.createInput(coll, op)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VS(expr) if expr else V(cm(dist))), direction)
    if bodies: ei.participantBodies=bodies
    f=comp.features.extrudeFeatures.add(ei); f.name=name; return f
def fillet_edges(comp, body, pred, r_mm, name):
    coll=adsk.core.ObjectCollection.create()
    for e in body.edges:
        if pred(e): coll.add(e)
    if coll.count==0: return None
    fi=comp.features.filletFeatures.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(coll, V(cm(r_mm)), True)
    f=comp.features.filletFeatures.add(fi); f.name=name; return f
def sector(sk, cx, cy, cz, r0, r1, a0, a1):
    # sector in the YZ plane about the X-parallel axis through (cx,cy,cz); angle from +Y toward +Z
    def W(r,a): return s(sk, cx, cy+r*math.cos(math.radians(a)), cz+r*math.sin(math.radians(a)))
    am=(a0+a1)/2
    L=sk.sketchCurves.sketchLines; A=sk.sketchCurves.sketchArcs
    L.addByTwoPoints(W(r0,a0), W(r1,a0)); A.addByThreePoints(W(r1,a0), W(r1,am), W(r1,a1))
    L.addByTwoPoints(W(r1,a1), W(r0,a1)); A.addByThreePoints(W(r0,a1), W(r0,am), W(r0,a0))

def run(_c):
    app=adsk.core.Application.get(); d=app.activeProduct; root=d.rootComponent
    if preflight_existing_stand_build(root):
        return
    ups=d.userParameters
    def setp(n,e,c,unit='mm'):
        p=ups.itemByName(n)
        if p is None: ups.add(n, VS(e), unit, c)
        else: p.expression=e; p.comment=c
    prm={'standX':109,'standPadW':30,'standPadL':100,'standPadT':6,'standPadRearReach':40,'standRubberD':28,'standRubberT':3,
         'standPivotBehind':13,'standPivotZ':-61,'standBarrelD':14,'standBoreD':5.4,'standHubW':12.8,'standEarGap':14,'standEarT':4,
         'standToothH':0.6,'standPlateW':27,'standPlateT':5,'standPlateTop':-31,'standScrewZ1':-50,'standScrewZ2':-38,'standScrewHoleD':3.4,
         'standBossOD':8,'standBossH':5,'standPilotD':2.5,'standPilotDepth':8.5,'standHexAF':8.2,'standHexDepth':3.5}
    cmt={'standX':'Stand centre |X|','standPadW':'Desk pad width (X)','standPadL':'Desk pad length (Y)','standPadT':'Desk pad thickness','standPadRearReach':'Pad length behind the pivot axis',
         'standRubberD':'Rubber disc diameter','standRubberT':'Rubber disc thickness (stick-on)','standPivotBehind':'Pivot axis distance behind the rear panel face',
         'standPivotZ':'Pivot axis Z (enclosure bottom is -65)','standBarrelD':'Hinge barrel diameter','standBoreD':'M5 bolt bore','standHubW':'Pad knuckle width = ear gap - 2 x tooth height',
         'standEarGap':'Clear gap between bracket ears','standEarT':'Bracket ear thickness','standToothH':'Castellation tooth height','standPlateW':'Bracket plate width (X)',
         'standPlateT':'Bracket plate thickness','standPlateTop':'Bracket plate top Z','standScrewZ1':'Lower M3 screw Z','standScrewZ2':'Upper M3 screw Z','standScrewHoleD':'M3 clearance hole',
         'standBossOD':'Rear-wall boss OD','standBossH':'Rear-wall boss height inside','standPilotD':'M3 thread-forming pilot','standPilotDepth':'Pilot depth from the rear face','standHexAF':'M5 hex head pocket across flats','standHexDepth':'Hex pocket depth'}
    # ---------------- remove the earlier paddle-foot modules and their bottom bosses ----------------
    for o in [o for o in root.occurrences if o.name.startswith('TILT_FOOT')]: o.deleteMe()
    fh=[o for o in root.occurrences if o.name.startswith('FRONT_HALF')][0]
    for nm in ('FT_TILT_FOOT_PILOTS','FT_TILT_FOOT_BOSSES'):
        for f in fh.component.features.extrudeFeatures:
            if f.name==nm: f.deleteMe(); break
    for nm in ('SK_TILT_FOOT_PILOTS','SK_TILT_FOOT_BOSSES'):
        for sk in fh.component.sketches:
            if sk.name==nm: sk.deleteMe(); break
    for nm in ('PL_TILT_FOOT_PILOTS','PL_TILT_FOOT_BOSSES'):
        for pl in fh.component.constructionPlanes:
            if pl.name==nm: pl.deleteMe(); break
    for k,v in prm.items(): setp(k, f'{v} mm', cmt[k])
    setp('standTeeth','24','Hinge castellation count (360/24 = 15 deg steps)','')
    g=lambda n: ups.itemByName(n).value*10
    NT=int(ups.itemByName('standTeeth').value)
    YR=54.04                                   # rear panel exterior face
    X=g('standX'); yp=YR+g('standPivotBehind'); zp=g('standPivotZ'); rb=g('standBarrelD')/2
    padTop=zp-rb-1.0                           # 1 mm between ear swing circle and pad top
    # ---------------- rear-wall bosses + pilots (BACK_HALF) ----------------
    mount_start=d.timeline.count
    bh=[o for o in root.occurrences if o.name.startswith('BACK_HALF')][0]; bc=bh.component
    shell=[b for b in bc.bRepBodies if b.name=='BACK_SHELL'][0]
    YI=YR-4.0                                  # rear wall interior face
    sk=sk_xz(bc, YI, 'STAND_BOSSES')
    # Dimension direction is inherited from the seeded point, so standX stays
    # positive on both sides; the seed supplies the left/right sign.
    for sx, x_expr in ((-X, 'standX'), (X, 'standX')):
        for z, z_expr in ((g('standScrewZ1'), '-standScrewZ1'),
                          (g('standScrewZ2'), '-standScrewZ2')):
            parameter_circle(
                sk, s(sk,sx,YI,z), g('standBossOD'),
                x_expr, z_expr, 'standBossOD'
            )
    extrude(bc, sk, 0, NEG, JOIN, 'FT_STAND_BOSSES', [shell], 'standBossH')
    sk=sk_xz(bc, YR, 'STAND_PILOTS')
    for sx, x_expr in ((-X, 'standX'), (X, 'standX')):
        for z, z_expr in ((g('standScrewZ1'), '-standScrewZ1'),
                          (g('standScrewZ2'), '-standScrewZ2')):
            parameter_circle(
                sk, s(sk,sx,YR,z), g('standPilotD'),
                x_expr, z_expr, 'standPilotD'
            )
    extrude(bc, sk, 0, NEG, CUT, 'FT_STAND_PILOTS', [shell], 'standPilotDepth')
    mount_end=d.timeline.count-1
    if mount_end>=mount_start:
        group=d.timeline.timelineGroups.add(mount_start,mount_end)
        if group:
            group.name='BACK HALF - STAND BOSSES AND PILOTS'; group.isCollapsed=True
    # ---------------- removable stand assembly ----------------
    stand_start=d.timeline.count
    ao=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); ac=ao.component; ac.name='TILT_STAND_ASSEMBLY'
    ho=ac.occurrences.addNewComponent(adsk.core.Matrix3D.create()); hc=ho.component; hc.name='STAND_HINGE'
    ho.isGroundToParent=True
    # ---------------- BRACKET (right side, X=+standX) ----------------
    bo=hc.occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=bo.component; c.name='STAND_BRACKET'
    bo.isGroundToParent=True
    hw=g('standPlateW')/2; pt=g('standPlateT'); ztop=g('standPlateTop')
    sk=sk_xz(c, YR, 'STAND_PLATE')
    poly(sk,[s(sk,X-hw,YR,padTop), s(sk,X+hw,YR,padTop), s(sk,X+hw,YR,ztop), s(sk,X-hw,YR,ztop)])
    plate=extrude(c, sk, 0, POS, NEW, 'FT_STAND_PLATE', None, 'standPlateT').bodies.item(0); plate.name='STAND_BRACKET'
    # ears: lug from the plate rear face around the pivot (profile in YZ)
    gap=g('standEarGap'); et=g('standEarT'); yb=YR+pt
    for xs in (X-gap/2-et, X+gap/2):
        sk=sk_yz(c, xs, 'STAND_EAR')
        # rectangle from plate face to pivot, plus the round end
        L=sk.sketchCurves.sketchLines; A=sk.sketchCurves.sketchArcs
        p1=s(sk,xs,yb,zp+rb); p2=s(sk,xs,yp,zp+rb); p3_=s(sk,xs,yp,zp-rb); p4=s(sk,xs,yb,zp-rb)
        L.addByTwoPoints(p1,p2); A.addByThreePoints(p2, s(sk,xs,yp+rb,zp), p3_); L.addByTwoPoints(p3_,p4); L.addByTwoPoints(p4,p1)
        extrude(c, sk, 0, POS, JOIN, 'FT_STAND_EAR', [plate], 'standEarT')
    # bore through both ears
    xa=X-gap/2-et
    sk=sk_yz(c, xa, 'STAND_EAR_BORE'); circle(sk, s(sk,xa,yp,zp), g('standBoreD'))
    extrude(c, sk, gap+2*et, POS, CUT, 'FT_STAND_EAR_BORE', [plate])
    # hex pocket for the M5 head on the outer (+X) ear
    xo=X+gap/2+et
    sk=sk_yz(c, xo, 'STAND_HEX_POCKET'); R=g('standHexAF')/math.sqrt(3)
    poly(sk,[s(sk,xo,yp+R*math.cos(math.radians(60*i+30)),zp+R*math.sin(math.radians(60*i+30))) for i in range(6)])
    extrude(c, sk, 0, NEG, CUT, 'FT_STAND_HEX_POCKET', [plate], 'standHexDepth')
    # ear teeth (inner faces), centred at half-pitch offsets
    th=g('standToothH'); pitch=360.0/NT; tw=pitch*0.4
    for xs, direction in ((X-gap/2, POS), (X+gap/2, NEG)):
        sk=sk_yz(c, xs, 'STAND_EAR_TEETH')
        for k in range(NT):
            a=pitch/2+pitch*k; sector(sk, xs, yp, zp, g('standBoreD')/2+0.7, rb-1.0, a-tw/2, a+tw/2)
        extrude(c, sk, th, direction, JOIN, 'FT_STAND_EAR_TEETH', [plate])
    # screw holes + countersink
    sk=sk_xz(c, YR, 'STAND_SCREW_HOLES')
    for z in (g('standScrewZ1'), g('standScrewZ2')): circle(sk, s(sk,X,YR,z), g('standScrewHoleD'))
    extrude(c, sk, 0, POS, CUT, 'FT_STAND_SCREW_HOLES', [plate], 'standPlateT')
    coll=adsk.core.ObjectCollection.create()
    for e in plate.edges:
        ge=e.geometry
        if isinstance(ge, adsk.core.Circle3D) and abs(ge.radius-cm(g('standScrewHoleD')/2))<1e-6 and abs(ge.center.y-cm(yb))<1e-6: coll.add(e)
    ci=c.features.chamferFeatures.createInput2(); ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll, V(cm(1.5)), True)
    c.features.chamferFeatures.add(ci).name='FT_STAND_COUNTERSINKS'
    # plate corner rounds (vertical edges at the top corners)
    fillet_edges(c, plate, lambda e: isinstance(e.geometry, adsk.core.Line3D) and abs(e.geometry.startPoint.x-e.geometry.endPoint.x)<1e-9 and abs(e.geometry.startPoint.z-e.geometry.endPoint.z)<1e-9 and abs(e.geometry.startPoint.z-cm(ztop))<1e-6, 6.0, 'FT_STAND_PLATE_ROUNDS')
    # ---------------- PAD ----------------
    po=hc.occurrences.addNewComponent(adsk.core.Matrix3D.create()); pc=po.component; pc.name='STAND_PAD'
    pw=g('standPadW')/2; pl_=g('standPadL'); rr=g('standPadRearReach'); y0=yp+rr-pl_; y1=yp+rr; ptk=g('standPadT')
    sk=sk_xy(pc, padTop, 'STAND_PAD')
    poly(sk,[s(sk,X-pw,y0,padTop), s(sk,X+pw,y0,padTop), s(sk,X+pw,y1,padTop), s(sk,X-pw,y1,padTop)])
    pad=extrude(pc, sk, 0, NEG, NEW, 'FT_STAND_PAD', None, 'standPadT').bodies.item(0); pad.name='STAND_PAD'
    fillet_edges(pc, pad, lambda e: isinstance(e.geometry, adsk.core.Line3D) and abs(e.geometry.startPoint.x-e.geometry.endPoint.x)<1e-9 and abs(e.geometry.startPoint.y-e.geometry.endPoint.y)<1e-9, pw-0.01, 'FT_STAND_PAD_ENDS')
    # knuckle: barrel on a pedestal
    hwid=g('standHubW'); xh=X-hwid/2
    sk=sk_yz(pc, xh, 'STAND_KNUCKLE')
    L=sk.sketchCurves.sketchLines; A=sk.sketchCurves.sketchArcs
    q1=s(sk,xh,yp-rb,zp); q2=s(sk,xh,yp+rb,zp); q3=s(sk,xh,yp+rb,padTop); q4=s(sk,xh,yp-rb,padTop)
    A.addByThreePoints(q1, s(sk,xh,yp,zp+rb), q2); L.addByTwoPoints(q2,q3); L.addByTwoPoints(q3,q4); L.addByTwoPoints(q4,q1)
    extrude(pc, sk, 0, POS, JOIN, 'FT_STAND_KNUCKLE', [pad], 'standHubW')
    sk=sk_yz(pc, xh, 'STAND_KNUCKLE_BORE'); circle(sk, s(sk,xh,yp,zp), g('standBoreD'))
    extrude(pc, sk, hwid, POS, CUT, 'FT_STAND_KNUCKLE_BORE', [pad])
    for xs, direction in ((X-hwid/2, NEG), (X+hwid/2, POS)):
        sk=sk_yz(pc, xs, 'STAND_KNUCKLE_TEETH')
        for k in range(NT):
            a=pitch*k; sector(sk, xs, yp, zp, g('standBoreD')/2+0.7, rb-1.0, a-tw/2, a+tw/2)
        extrude(pc, sk, th, direction, JOIN, 'FT_STAND_KNUCKLE_TEETH', [pad])
    # rubber disc seats (shallow 0.5 recess) + rubber discs as separate reference bodies
    zb=padTop-ptk
    sk=sk_xy(pc, zb, 'STAND_RUBBER_SEATS')
    for yc in (y0+pw, y1-pw): circle(sk, s(sk,X,yc,zb), g('standRubberD'))
    extrude(pc, sk, 0.5, POS, CUT, 'FT_STAND_RUBBER_SEATS', [pad])
    sk=sk_xy(pc, zb+0.5, 'STAND_RUBBER')
    for yc in (y0+pw, y1-pw): circle(sk, s(sk,X,yc,zb+0.5), g('standRubberD'))
    f=extrude(pc, sk, 0, NEG, NEW, 'FT_STAND_RUBBER', None, 'standRubberT')
    for i in range(f.bodies.count): f.bodies.item(i).name=f'STAND_RUBBER_{i+1}'
    # ---------------- left side occurrence of the same hinge definition ----------------
    t=adsk.core.Matrix3D.create(); t.translation=adsk.core.Vector3D.create(cm(-2*X),0,0)
    left=ac.occurrences.addExistingComponent(hc, t); left.isGroundToParent=True
    if d.snapshots.hasPendingSnapshot: d.snapshots.add()
    stand_end=d.timeline.count-1
    if stand_end>=stand_start:
        group=d.timeline.timelineGroups.add(stand_start,stand_end)
        if group:
            group.name='STAND PARTS - BRACKET AND PAD'; group.isCollapsed=True
    print('bracket faces', plate.faces.count, p3(plate.boundingBox.minPoint), p3(plate.boundingBox.maxPoint))
    print('pad faces', pad.faces.count, p3(pad.boundingBox.minPoint), p3(pad.boundingBox.maxPoint), 'padTop', padTop, 'desk', zb+0.5-g('standRubberT'))
