"""Dual-concentric encoder knobs for the ARCI enclosure.

Run inside Fusion 360 via the MCP script runner. Builds KNOB_DUAL_OUTER_15 and
KNOB_DUAL_INNER_11 to the supplier drawing (Ø15 × 13.5 outer with an Ø10.2 × 4.5 top recess;
Ø11 inner with an Ø6.5 × 4.5 neck nesting in that recess and an Ø10 top band) at the lower
encoder (113, 2.9983) and copies them +37 mm in Z for the upper encoder.
Knurl: one 90° V groove swept along the axis with a twist (knob*KnurlTwist, derived from
knobKnurlHelixDeg) and circular-patterned knob*KnurlN times; both hands give the diamond.
Knurl the bare cylinder first (sweeps fail after bores exist). Existing KNOB_DUAL components
are deleted first. Entry point: run(context).
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
HOR=adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
VER=adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
def cm(v): return v/10.0

def plane(comp, base, offset_mm, name):
    pi=comp.constructionPlanes.createInput(); pi.setByOffset(base, V(cm(offset_mm)))
    pl=comp.constructionPlanes.add(pi); pl.name=name; return pl
def sk_y(comp, y, name):
    pl=plane(comp, comp.xZConstructionPlane, y, 'PL_'+name); sk=comp.sketches.add(pl); sk.name='SK_'+name; return sk
def sk_x(comp, x, name):
    pl=plane(comp, comp.yZConstructionPlane, x, 'PL_'+name); sk=comp.sketches.add(pl); sk.name='SK_'+name; return sk
def s(sk, x,y,z): return sk.modelToSketchSpace(P(cm(x),cm(y),cm(z)))
def circle(sk, c, d_mm): return sk.sketchCurves.sketchCircles.addByCenterRadius(c, cm(d_mm/2))
def poly(sk, pts):
    n=len(pts)
    return [sk.sketchCurves.sketchLines.addByTwoPoints(pts[i], pts[(i+1)%n]) for i in range(n)]

# Dimensions, not Fix constraints, keep the construction sketches editable and
# preserve the model's existing parameter-driven geometry on every rebuild.
def dim_origin(sk, point, orientation, expression):
    g=point.geometry
    d=sk.sketchDimensions.addDistanceDimension(sk.originPoint, point, orientation,
                                               P(g.x+0.2,g.y+0.2,0))
    d.parameter.expression=expression
    return d
def dim_diameter(sk, crv, expression):
    g=crv.centerSketchPoint.geometry
    d=sk.sketchDimensions.addDiameterDimension(crv, P(g.x+0.25,g.y+0.25,0))
    d.parameter.expression=expression
    return d
def constrain_xz_point(sk, point, x_expr, z_expr):
    # XZ sketches are created from the component XZ plane; dimension values are
    # unsigned, so the expression supplies the existing coordinate magnitude.
    dim_origin(sk, point, HOR, x_expr); dim_origin(sk, point, VER, z_expr)
def constrain_xz_circle(sk, crv, d_expr):
    dim_diameter(sk, crv, d_expr)
    constrain_xz_point(sk, crv.centerSketchPoint, 'knobDualCenterX', 'knobDualCenterZ')
def constrain_concentric_circle(sk, crv, centre_crv, d_expr):
    """A second circle needs one diameter and a relation, not duplicate centre dimensions."""
    dim_diameter(sk, crv, d_expr)
    sk.geometricConstraints.addConcentric(crv, centre_crv)
def constrain_yz_circle(sk, crv, d_expr, y_expr):
    # On YZ sketches horizontal is -model-Z and vertical is model-Y.
    dim_diameter(sk, crv, d_expr)
    dim_origin(sk, crv.centerSketchPoint, HOR, 'knobDualCenterZ')
    dim_origin(sk, crv.centerSketchPoint, VER, y_expr)
def constrain_yz_path(sk, line, y_expr, length_expr):
    """Lock a Y-axis path using its actual sketch orientation, not an assumption."""
    a,b=line.startSketchPoint.geometry,line.endSketchPoint.geometry
    vertical=abs(b.y-a.y) >= abs(b.x-a.x)
    sk.geometricConstraints.addVertical(line) if vertical else sk.geometricConstraints.addHorizontal(line)
    if vertical:
        dim_origin(sk,line.startSketchPoint,HOR,'knobDualCenterZ')
        dim_origin(sk,line.startSketchPoint,VER,y_expr)
        orient=VER
    else:
        dim_origin(sk,line.startSketchPoint,HOR,y_expr)
        dim_origin(sk,line.startSketchPoint,VER,'knobDualCenterZ')
        orient=HOR
    g=line.endSketchPoint.geometry
    d=sk.sketchDimensions.addDistanceDimension(line.startSketchPoint,line.endSketchPoint,orient,
                                                P(g.x+0.3,g.y+0.3,0))
    d.parameter.expression=length_expr
def constrain_knurl_v(sk, lines, d_param, depth_param, n_param, hand):
    """Dimension the existing three V vertices by their radial/tangential formulae."""
    sk.geometricConstraints.addCoincident(lines[0].endSketchPoint,lines[1].startSketchPoint)
    sk.geometricConstraints.addCoincident(lines[1].endSketchPoint,lines[2].startSketchPoint)
    sk.geometricConstraints.addCoincident(lines[2].endSketchPoint,lines[0].startSketchPoint)
    theta='0 deg' if hand>0 else '( 180 deg / %s )' % n_param
    apex='( %s / 2 - %s )' % (d_param,depth_param)
    base='( %s / 2 + knobKnurlVOverhang )' % d_param
    width='( %s + knobKnurlVOverhang )' % depth_param
    def xy(radial, offset):
        return ('( knobDualCenterX + %s * cos( %s ) - %s * sin( %s ) )' %
                (radial,theta,offset,theta),
                '( knobDualCenterZ + %s * sin( %s ) + %s * cos( %s ) )' %
                (radial,theta,offset,theta))
    for point, values in zip((lines[0].startSketchPoint, lines[0].endSketchPoint,
                              lines[1].endSketchPoint),
                             (xy(apex,'0 mm'),xy(base,width),xy(base,'-'+width))):
        constrain_xz_point(sk,point,*values)
def constrain_key_rect(sk, lines, inner_expr):
    """Constrain one closed drive-key rectangle by position, width, and height."""
    bottom,right,top,left=lines
    sk.geometricConstraints.addCoincident(bottom.endSketchPoint,right.startSketchPoint)
    sk.geometricConstraints.addCoincident(right.endSketchPoint,top.startSketchPoint)
    sk.geometricConstraints.addCoincident(top.endSketchPoint,left.startSketchPoint)
    sk.geometricConstraints.addCoincident(left.endSketchPoint,bottom.startSketchPoint)
    sk.geometricConstraints.addHorizontal(bottom)
    sk.geometricConstraints.addVertical(right)
    sk.geometricConstraints.addHorizontal(top)
    sk.geometricConstraints.addVertical(left)
    dim_origin(sk,bottom.startSketchPoint,HOR,inner_expr)
    dim_origin(sk,bottom.startSketchPoint,VER,'knobDualCenterZ - knobKeyW / 2')
    g=bottom.endSketchPoint.geometry
    d=sk.sketchDimensions.addDistanceDimension(bottom.startSketchPoint,bottom.endSketchPoint,HOR,
                                                P(g.x+0.3,g.y+0.3,0))
    d.parameter.expression='( knobOuterBoreD / 2 + knobKeyBoreOverlap ) - ( knobOuterPassD / 2 - knobKeyPassOverlap )'
    g=top.endSketchPoint.geometry
    d=sk.sketchDimensions.addDistanceDimension(bottom.startSketchPoint,top.endSketchPoint,VER,
                                                P(g.x+0.3,g.y+0.3,0))
    d.parameter.expression='knobKeyW'
def extrude(comp, sk, dist, direction, op, name, bodies=None, dist_expr=None):
    coll=adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count): coll.add(sk.profiles.item(i))
    ei=comp.features.extrudeFeatures.createInput(coll, op)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VS(dist_expr) if dist_expr else V(cm(dist))), direction)
    if bodies: ei.participantBodies=bodies
    f=comp.features.extrudeFeatures.add(ei); f.name=name; return f
def chamfer_circles(comp, body, y_mm, r_mm, size_mm, name):
    coll=adsk.core.ObjectCollection.create()
    for e in body.edges:
        g=e.geometry
        if isinstance(g, adsk.core.Circle3D) and abs(g.radius-cm(r_mm))<1e-5 and abs(g.center.y-cm(y_mm))<1e-5: coll.add(e)
    if coll.count==0: return None
    ci=comp.features.chamferFeatures.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll, V(cm(size_mm)), True)
    f=comp.features.chamferFeatures.add(ci); f.name=name; return f

def knurl(comp, body, cx, cz, R, y_top, y_bot, N, depth, hand, axis, tag, twist_param,
          n_param, y_top_expr, band_expr, d_param, depth_param, overhang):
    th0=0.0 if hand>0 else math.pi/N
    psk=sk_x(comp, cx, f'KNURL_PATH_{tag}')
    line=psk.sketchCurves.sketchLines.addByTwoPoints(s(psk,cx,y_top,cz), s(psk,cx,y_bot,cz))
    constrain_yz_path(psk,line,y_top_expr,band_expr)
    path=comp.features.createPath(line, False)
    vsk=sk_y(comp, y_top, f'KNURL_V_{tag}')
    w=depth+overhang
    ca,sa=math.cos(th0),math.sin(th0)
    def W(r,off): return s(vsk, cx+r*ca-off*sa, y_top, cz+r*sa+off*ca)
    lines=poly(vsk,[W(R-depth,0), W(R+overhang,w), W(R+overhang,-w)])
    constrain_knurl_v(vsk,lines,d_param,depth_param,n_param,hand)
    si=comp.features.sweepFeatures.createInput(vsk.profiles.item(0), path, CUT)
    si.twistAngle=VS(('' if hand>0 else '-')+twist_param)
    si.participantBodies=[body]
    sw=comp.features.sweepFeatures.add(si); sw.name=f'FT_KNURL_GROOVE_{tag}'
    ents=adsk.core.ObjectCollection.create(); ents.add(sw)
    ci=comp.features.circularPatternFeatures.createInput(ents, axis)
    ci.quantity=VS(n_param); ci.totalAngle=VS('360 deg'); ci.isSymmetric=False
    ci.patternComputeOption=adsk.fusion.PatternComputeOptions.AdjustPatternCompute
    cp=comp.features.circularPatternFeatures.add(ci); cp.name=f'FT_KNURL_PATTERN_{tag}'

def make_axis(comp, body, name):
    face=[fc for fc in body.faces if isinstance(fc.geometry, adsk.core.Cylinder)][0]
    ai=comp.constructionAxes.createInput(); ai.setByCircularFace(face)
    ax=comp.constructionAxes.add(ai); ax.name=name; return ax

def run(_c):
    app=adsk.core.Application.get(); d=app.activeProduct; root=d.rootComponent
    ups=d.userParameters
    for o in [o for o in root.occurrences if o.name.startswith('KNOB_DUAL')]: o.deleteMe()
    def setp(n,e,c,unit='mm'):
        p=ups.itemByName(n)
        if p is None: ups.add(n, VS(e), unit, c)
        else: p.expression=e; p.comment=c
    cx=113.0; cz=2.9983
    prm={'knobGapPanel':0.6,'knobOuterD':15.0,'knobOuterH':13.5,'knobOuterTopBandD':14.0,'knobOuterTopBandH':2.0,'knobOuterRecessD':10.2,'knobOuterRecessDepth':4.5,
         'knobOuterKnurlH':9.5,'knobOuterBoreD':6.2,'knobOuterBoreDepth':8.0,'knobOuterReliefD':8.0,'knobOuterReliefDepth':2.0,'knobOuterPassD':4.2,'knobKeyW':1.7,'knobKeyH':4.0,
         'knobOuterSetScrewY':4.5,'knobSetScrewD':2.5,'knobOuterKnurlDepth':0.3,
         'knobStackGap':0.3,'knobInnerD':11.0,'knobInnerNeckD':6.5,'knobInnerNeckL':4.5,'knobInnerKnurlH':9.5,'knobInnerTopBandD':10.0,'knobInnerTopBandH':1.5,
         'knobInnerBoreD':3.6,'knobInnerBoreDepth':10.0,'knobInnerRoundDepth':2.2,'knobInnerFlat':0.8,'knobInnerSetScrewY':6.5,'knobInnerKnurlDepth':0.28}
    cmt={'knobGapPanel':'Gap between outer knob underside and the panel face','knobOuterD':'Outer knob knurl OD (drawing O15)','knobOuterH':'Outer knob total height (2 skirt + 9.5 knurl + 2 top band)',
         'knobOuterTopBandD':'Outer knob top band OD (O14, C1 chamfer)','knobOuterTopBandH':'Outer knob top band height','knobOuterRecessD':'Top recess that receives the inner knob neck (O10.2)',
         'knobOuterRecessDepth':'Top recess depth (4.5)','knobOuterKnurlH':'Outer knurl band height','knobOuterBoreD':'Bore for the O6 slotted hollow shaft','knobOuterBoreDepth':'Bore depth from the underside (shaft protrudes 7.4 past the panel)',
         'knobOuterReliefD':'Bushing relief counterbore at the underside (O8)','knobOuterReliefDepth':'Relief depth (2)','knobOuterPassD':'Hole through the web for the O3.5 inner shaft',
         'knobKeyW':'Drive-key stub width in the O6 shaft slot','knobKeyH':'Drive-key stub height above the bore floor','knobOuterSetScrewY':'Set-screw height above the underside',
         'knobSetScrewD':'Radial grub-screw pilot (M3 thread-forming in PLA; drawing uses M2)','knobOuterKnurlDepth':'Outer knurl groove depth',
         'knobStackGap':'Axial clearance between inner knob and outer knob','knobInnerD':'Inner knob knurl OD (O11)','knobInnerNeckD':'Inner knob neck OD nesting in the outer recess (O6.5)',
         'knobInnerNeckL':'Inner knob neck length (recess depth - gap)','knobInnerKnurlH':'Inner knurl band height','knobInnerTopBandD':'Inner top band OD (O10, C0.5)','knobInnerTopBandH':'Inner top band height',
         'knobInnerBoreD':'Bore for the O3.5 D inner shaft','knobInnerBoreDepth':'Bore depth from the neck end (10)','knobInnerRoundDepth':'Round bore length before the D section','knobInnerFlat':'D-bore flat distance from the axis',
         'knobInnerSetScrewY':'Set-screw height above the neck end','knobInnerKnurlDepth':'Inner knurl groove depth'}
    for k,v in prm.items(): setp(k, f'{v} mm', cmt[k])
    setp('knobOuterKnurlN','60','Outer knurl tooth count (0.79 mm pitch on O15)','')
    setp('knobInnerKnurlN','44','Inner knurl tooth count (0.79 mm pitch on O11)','')
    setp('knobDualCenterX','113 mm','Lower encoder centre X','mm')
    setp('knobDualCenterZ','2.9983 mm','Lower encoder centre Z','mm')
    setp('knobDualUpperOffsetZ','37 mm','Upper encoder copy offset in Z','mm')
    setp('knobKnurlVOverhang','0.25 mm','V-groove base radial overhang','mm')
    setp('knobKeyPassOverlap','0.05 mm','Drive-key overlap into the pass hole','mm')
    setp('knobKeyBoreOverlap','0.2 mm','Drive-key overlap into the outer bore','mm')
    setp('knobKnurlHelixDeg','30 deg','Knurl helix angle from the axis','deg')
    setp('knobOuterKnurlTwist','( knobOuterKnurlH * tan(knobKnurlHelixDeg) / ( knobOuterD / 2 ) ) * 1 rad','Sweep twist for the outer knurl band','deg')
    setp('knobInnerKnurlTwist','( knobInnerKnurlH * tan(knobKnurlHelixDeg) / ( knobInnerD / 2 ) ) * 1 rad','Sweep twist for the inner knurl band','deg')
    g=lambda n: ups.itemByName(n).value*10
    cx=g('knobDualCenterX'); cz=g('knobDualCenterZ')
    y0=-g('knobGapPanel')
    # ---------------- OUTER ----------------
    D=g('knobOuterD'); R=D/2; H=g('knobOuterH'); y1=y0-H
    oc=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=oc.component; c.name='KNOB_DUAL_OUTER_15'
    sk=sk_y(c, y0, 'KNOB_OUTER_BODY'); crv=circle(sk, s(sk,cx,y0,cz), D); constrain_xz_circle(sk,crv,'knobOuterD')
    body=extrude(c, sk, H, NEG, NEW, 'FT_KNOB_OUTER_BODY').bodies.item(0); body.name='KNOB_DUAL_OUTER_15'
    axis=make_axis(c, body, 'AX_KNOB_OUTER')
    ytb=y1+g('knobOuterTopBandH'); yk_top=ytb+g('knobOuterKnurlH')
    knurl(c, body, cx, cz, R, yk_top, ytb, 60, g('knobOuterKnurlDepth'), +1, axis, 'OUTER_RH', 'knobOuterKnurlTwist', 'knobOuterKnurlN', 'knobGapPanel + knobOuterH - knobOuterTopBandH - knobOuterKnurlH', 'knobOuterKnurlH', 'knobOuterD', 'knobOuterKnurlDepth', g('knobKnurlVOverhang'))
    knurl(c, body, cx, cz, R, yk_top, ytb, 60, g('knobOuterKnurlDepth'), -1, axis, 'OUTER_LH', 'knobOuterKnurlTwist', 'knobOuterKnurlN', 'knobGapPanel + knobOuterH - knobOuterTopBandH - knobOuterKnurlH', 'knobOuterKnurlH', 'knobOuterD', 'knobOuterKnurlDepth', g('knobKnurlVOverhang'))
    sk=sk_y(c, y1, 'KNOB_OUTER_TOP_BAND'); crv=circle(sk, s(sk,cx,y1,cz), g('knobOuterTopBandD')); constrain_xz_circle(sk,crv,'knobOuterTopBandD'); outer_band=crv; crv=circle(sk, s(sk,cx,y1,cz), D+2); constrain_concentric_circle(sk,crv,outer_band,'knobOuterD + 2 mm')
    coll=adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        pr=sk.profiles.item(i)
        if pr.profileLoops.count==2: coll.add(pr)
    ei=c.features.extrudeFeatures.createInput(coll, CUT); ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VS('knobOuterTopBandH')), POS); ei.participantBodies=[body]
    c.features.extrudeFeatures.add(ei).name='FT_KNOB_OUTER_TOP_BAND'
    sk=sk_y(c, y1, 'KNOB_OUTER_RECESS'); crv=circle(sk, s(sk,cx,y1,cz), g('knobOuterRecessD')); constrain_xz_circle(sk,crv,'knobOuterRecessD')
    extrude(c, sk, 0, POS, CUT, 'FT_KNOB_OUTER_RECESS', [body], 'knobOuterRecessDepth')
    sk=sk_y(c, y0, 'KNOB_OUTER_RELIEF'); crv=circle(sk, s(sk,cx,y0,cz), g('knobOuterReliefD')); constrain_xz_circle(sk,crv,'knobOuterReliefD')
    extrude(c, sk, 0, NEG, CUT, 'FT_KNOB_OUTER_RELIEF', [body], 'knobOuterReliefDepth')
    sk=sk_y(c, y0, 'KNOB_OUTER_BORE'); crv=circle(sk, s(sk,cx,y0,cz), g('knobOuterBoreD')); constrain_xz_circle(sk,crv,'knobOuterBoreD')
    extrude(c, sk, 0, NEG, CUT, 'FT_KNOB_OUTER_BORE', [body], 'knobOuterBoreDepth')
    sk=sk_y(c, y0, 'KNOB_OUTER_PASS'); crv=circle(sk, s(sk,cx,y0,cz), g('knobOuterPassD')); constrain_xz_circle(sk,crv,'knobOuterPassD')
    extrude(c, sk, 0, NEG, CUT, 'FT_KNOB_OUTER_PASS', [body], 'knobOuterH')
    yf=y0-g('knobOuterBoreDepth'); kw=g('knobKeyW')/2; rb=g('knobOuterBoreD')/2
    sk=sk_y(c, yf, 'KNOB_OUTER_KEY')
    for sgn,side in ((1,'+'),(-1,'-')):
        inner='( knobDualCenterX %s ( knobOuterPassD / 2 - knobKeyPassOverlap ) )' % side
        lines=poly(sk,[s(sk,cx+sgn*(g('knobOuterPassD')/2-g('knobKeyPassOverlap')),yf,cz-kw), s(sk,cx+sgn*(rb+g('knobKeyBoreOverlap')),yf,cz-kw), s(sk,cx+sgn*(rb+g('knobKeyBoreOverlap')),yf,cz+kw), s(sk,cx+sgn*(g('knobOuterPassD')/2-g('knobKeyPassOverlap')),yf,cz+kw)])
        constrain_key_rect(sk,lines,inner)
    extrude(c, sk, 0, POS, JOIN, 'FT_KNOB_OUTER_KEY', [body], 'knobKeyH')
    sk=sk_x(c, cx+R+0.5, 'KNOB_OUTER_SETSCREW'); crv=circle(sk, s(sk,cx+R+0.5,y0-g('knobOuterSetScrewY'),cz), g('knobSetScrewD')); constrain_yz_circle(sk,crv,'knobSetScrewD','knobGapPanel + knobOuterSetScrewY')
    extrude(c, sk, R+0.5-rb+0.5, NEG, CUT, 'FT_KNOB_OUTER_SETSCREW', [body])
    chamfer_circles(c, body, y1, g('knobOuterTopBandD')/2, 1.0, 'FT_KNOB_OUTER_TOP_C1')
    chamfer_circles(c, body, y1, g('knobOuterRecessD')/2, 0.9, 'FT_KNOB_OUTER_RECESS_C1')
    chamfer_circles(c, body, ytb, R, 0.5, 'FT_KNOB_OUTER_BAND_C05')
    chamfer_circles(c, body, y0, R, 0.5, 'FT_KNOB_OUTER_BOTTOM_C05')
    lib=[L for L in app.materialLibraries if 'Appearance' in L.name][0]
    ap=None
    for a in lib.appearances:
        n=a.name.lower()
        if 'black' in n and 'paint' in n and 'glossy' in n: ap=a; break
    if ap: body.appearance=ap
    outer=body
    # ---------------- INNER ----------------
    D=g('knobInnerD'); R=D/2
    y_neck0=y1+g('knobOuterRecessDepth')-g('knobStackGap')   # neck end, just above the recess floor
    y_body0=y1-g('knobStackGap')                             # body underside, just above the outer top
    y_body1=y_body0-g('knobInnerKnurlH')-g('knobInnerTopBandH')
    oc=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=oc.component; c.name='KNOB_DUAL_INNER_11'
    sk=sk_y(c, y_body0, 'KNOB_INNER_BODY'); crv=circle(sk, s(sk,cx,y_body0,cz), D); constrain_xz_circle(sk,crv,'knobInnerD')
    body=extrude(c, sk, y_body0-y_body1, NEG, NEW, 'FT_KNOB_INNER_BODY').bodies.item(0); body.name='KNOB_DUAL_INNER_11'
    axis=make_axis(c, body, 'AX_KNOB_INNER')
    ytb=y_body1+g('knobInnerTopBandH')
    knurl(c, body, cx, cz, R, y_body0, ytb, 44, g('knobInnerKnurlDepth'), +1, axis, 'INNER_RH', 'knobInnerKnurlTwist', 'knobInnerKnurlN', 'knobGapPanel + knobOuterH + knobStackGap', 'knobInnerKnurlH', 'knobInnerD', 'knobInnerKnurlDepth', g('knobKnurlVOverhang'))
    knurl(c, body, cx, cz, R, y_body0, ytb, 44, g('knobInnerKnurlDepth'), -1, axis, 'INNER_LH', 'knobInnerKnurlTwist', 'knobInnerKnurlN', 'knobGapPanel + knobOuterH + knobStackGap', 'knobInnerKnurlH', 'knobInnerD', 'knobInnerKnurlDepth', g('knobKnurlVOverhang'))
    sk=sk_y(c, y_body0, 'KNOB_INNER_NECK'); crv=circle(sk, s(sk,cx,y_body0,cz), g('knobInnerNeckD')); constrain_xz_circle(sk,crv,'knobInnerNeckD')
    extrude(c, sk, 0, POS, JOIN, 'FT_KNOB_INNER_NECK', [body], 'knobInnerNeckL')
    sk=sk_y(c, y_body1, 'KNOB_INNER_TOP_BAND'); crv=circle(sk, s(sk,cx,y_body1,cz), g('knobInnerTopBandD')); constrain_xz_circle(sk,crv,'knobInnerTopBandD'); inner_band=crv; crv=circle(sk, s(sk,cx,y_body1,cz), D+2); constrain_concentric_circle(sk,crv,inner_band,'knobInnerD + 2 mm')
    coll=adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        pr=sk.profiles.item(i)
        if pr.profileLoops.count==2: coll.add(pr)
    ei=c.features.extrudeFeatures.createInput(coll, CUT); ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VS('knobInnerTopBandH')), POS); ei.participantBodies=[body]
    c.features.extrudeFeatures.add(ei).name='FT_KNOB_INNER_TOP_BAND'
    sk=sk_y(c, y_neck0, 'KNOB_INNER_BORE_ROUND'); crv=circle(sk, s(sk,cx,y_neck0,cz), g('knobInnerBoreD')); constrain_xz_circle(sk,crv,'knobInnerBoreD')
    extrude(c, sk, 0, NEG, CUT, 'FT_KNOB_INNER_BORE_ROUND', [body], 'knobInnerRoundDepth')
    yd=y_neck0-g('knobInnerRoundDepth'); rb=g('knobInnerBoreD')/2; fl=g('knobInnerFlat'); xi=math.sqrt(rb*rb-fl*fl)
    sk=sk_y(c, yd, 'KNOB_INNER_BORE_D')
    a=s(sk,cx+xi,yd,cz+fl); b=s(sk,cx-xi,yd,cz+fl); m=s(sk,cx,yd,cz-rb)
    arc=sk.sketchCurves.sketchArcs.addByThreePoints(a,m,b); chord=sk.sketchCurves.sketchLines.addByTwoPoints(b,a)
    sk.geometricConstraints.addCoincident(arc.startSketchPoint,chord.endSketchPoint)
    sk.geometricConstraints.addCoincident(arc.endSketchPoint,chord.startSketchPoint)
    rd=sk.sketchDimensions.addRadialDimension(arc,P(arc.centerSketchPoint.geometry.x+0.3,arc.centerSketchPoint.geometry.y+0.3,0)); rd.parameter.expression='knobInnerBoreD / 2'
    sk.geometricConstraints.addHorizontal(chord)
    constrain_xz_point(sk,arc.centerSketchPoint,'knobDualCenterX','knobDualCenterZ')
    dim_origin(sk,chord.startSketchPoint,VER,'knobDualCenterZ + knobInnerFlat')
    extrude(c, sk, 0, NEG, CUT, 'FT_KNOB_INNER_BORE_D', [body], 'knobInnerBoreDepth - knobInnerRoundDepth')
    sk=sk_x(c, cx+R+0.5, 'KNOB_INNER_SETSCREW'); crv=circle(sk, s(sk,cx+R+0.5,y_neck0-g('knobInnerSetScrewY'),cz), g('knobSetScrewD')); constrain_yz_circle(sk,crv,'knobSetScrewD','knobGapPanel + knobOuterH - knobOuterRecessDepth + knobStackGap + knobInnerSetScrewY')
    extrude(c, sk, R+0.5-rb+0.5, NEG, CUT, 'FT_KNOB_INNER_SETSCREW', [body])
    chamfer_circles(c, body, y_body1, g('knobInnerTopBandD')/2, 0.5, 'FT_KNOB_INNER_TOP_C05')
    chamfer_circles(c, body, ytb, R, 0.5, 'FT_KNOB_INNER_BAND_C05')
    chamfer_circles(c, body, y_body0, R, 0.5, 'FT_KNOB_INNER_BOTTOM_C05')
    if ap: body.appearance=ap
    # ---------------- upper encoder copies ----------------
    for o in [o for o in root.occurrences if o.name.startswith('KNOB_DUAL')]:
        t=adsk.core.Matrix3D.create(); t.translation=adsk.core.Vector3D.create(0,0,cm(g('knobDualUpperOffsetZ')))
        root.occurrences.addExistingComponent(o.component, t)
    if d.snapshots.hasPendingSnapshot: d.snapshots.add()
    print('outer', outer.faces.count, 'faces; inner', body.faces.count, 'faces')
