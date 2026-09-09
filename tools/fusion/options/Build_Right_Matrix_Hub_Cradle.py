"""Rebuild the right-matrix USB-hub mount as a rigid PLA open cradle.

The carrier is a one-piece, support-free FDM part. Two tapered end webs join
the four matrix standoffs, and two longitudinal plus two transverse seat rails
support either hub orientation. The center stays open for the right-matrix
harness. All production geometry is made with named native sketches and
extrude/cut features.

The realistic hub reference is reconstructed from project measurements and
photographs. The Fusion document is deliberately not saved.

The four matrix fasteners use locally reinforced, sketch-driven head recesses.
This preserves the compact 6 mm standoff stems while allowing readily
available M3 x 20 mm screws to retain useful engagement in the front shell.
"""

import adsk.core as C
import adsk.fusion as F
import math

MATRIX_REAR_Y = 12.72
FRAME_Y = 27.70
SEAT_Y = 30.70
MATRIX_HOLES = [(55.692, -3.712), (55.607, 47.460),
                (98.993, -3.712), (98.907, 47.460)]
HUB_X0 = 51.5
HUB_X1 = 91.5
PRIMARY_NOTCH_CENTERS = [(53.0, 20.0), (90.0, 20.0)]
# Same 3 x 3 mm hub notches after a 90-degree rotation about the hub center.
ROTATED_NOTCH_CENTERS = [(71.5, 1.5), (71.5, 38.5)]
ALL_NOTCH_CENTERS = PRIMARY_NOTCH_CENTERS + ROTATED_NOTCH_CENTERS


def upsert_parameter(design, name, expression, comment):
    p = design.userParameters.itemByName(name)
    if p is None:
        p = design.userParameters.add(name, C.ValueInput.createByString(expression),
                                      "mm", comment)
    else:
        p.expression = expression
        p.comment = comment
    return p


def point(sketch, x_mm, z_mm):
    return sketch.modelToSketchSpace(C.Point3D.create(x_mm / 10, 0, z_mm / 10))


def xy_point(sketch, x_mm, y_mm):
    return sketch.modelToSketchSpace(C.Point3D.create(x_mm / 10, y_mm / 10, 0))


def rectangle(sketch, x0, x1, z0, z1):
    lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        point(sketch, x0, z0), point(sketch, x1, z1))
    for line in lines:
        line.isFixed = True


def rectangle_sketch(component, name, rectangles):
    sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = name
    for bounds in rectangles:
        rectangle(sketch, *bounds)
    return sketch


def polygon_sketch_xy(component, name, vertices_mm):
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = name
    vertices = [xy_point(sketch, x, y) for x, y in vertices_mm]
    for index in range(len(vertices)):
        line = sketch.sketchCurves.sketchLines.addByTwoPoints(
            vertices[index], vertices[(index + 1) % len(vertices)])
        line.isFixed = True
    for sketch_point in sketch.sketchPoints:
        if not sketch_point.isFullyConstrained:
            sketch_point.isFixed = True
    return sketch


def tapered_web_sketch_xy(component, name):
    """Create the closed, sketch-driven end-web profile with rounded knees.

    The four fillets live in this sketch instead of as a downstream body
    fillet.  That keeps the web extrusions associative and avoids leaving the
    timeline rolled back when the outline is edited.
    """
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = name
    vertices_mm = [
        (55.65, 15.5), (59.5, 15.5), (66.0, FRAME_Y),
        (88.6, FRAME_Y), (95.1, 15.5), (98.95, 15.5),
        (98.95, SEAT_Y), (55.65, SEAT_Y),
    ]
    vertices = [xy_point(sketch, x, y) for x, y in vertices_mm]
    lines = []
    for index in range(len(vertices)):
        lines.append(sketch.sketchCurves.sketchLines.addByTwoPoints(
            vertices[index], vertices[(index + 1) % len(vertices)]))

    # Fillet the two lower transitions and the two upper knees.  The point
    # arguments identify the shared corner on each pair of open curves.
    fillet_specs = [
        (0, 1, 1, 1.0),
        (1, 2, 2, 2.5),
        (2, 3, 3, 2.5),
        (3, 4, 4, 1.0),
    ]
    arcs = []
    for first_index, second_index, vertex_index, radius_mm in fillet_specs:
        arc = sketch.sketchCurves.sketchArcs.addFillet(
            lines[first_index], vertices[vertex_index],
            lines[second_index], vertices[vertex_index],
            radius_mm / 10)
        if arc is None:
            raise RuntimeError("Failed to create tapered-web sketch fillet")
        arc.isConstruction = False
        arcs.append(arc)

    # Fix the solved outline as one robust profile. This matches the other
    # production sketches and prevents Fusion's Sketch Fillet command state
    # from silently switching the arcs back to construction geometry.
    for line in lines:
        line.isFixed = True
    for arc in arcs:
        arc.isConstruction = False
        arc.isFixed = True
    for sketch_point in sketch.sketchPoints:
        if not sketch_point.isFullyConstrained:
            sketch_point.isFixed = True
    return sketch


def circle_sketch(component, name, centers, diameter_expression):
    sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = name
    for x_mm, z_mm in centers:
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
            point(sketch, x_mm, z_mm), 0.1)
        circle.centerSketchPoint.isFixed = True
        dim = sketch.sketchDimensions.addDiameterDimension(
            circle, point(sketch, x_mm + 3, z_mm + 3))
        dim.parameter.expression = diameter_expression
    return sketch


def hexagon_sketch(component, name, centers, across_flats_mm):
    sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = name
    radius = across_flats_mm / math.sqrt(3)
    for x_mm, z_mm in centers:
        vertices = [point(sketch,
                          x_mm + radius * math.cos(math.pi / 6 + i * math.pi / 3),
                          z_mm + radius * math.sin(math.pi / 6 + i * math.pi / 3))
                    for i in range(6)]
        for i in range(6):
            line = sketch.sketchCurves.sketchLines.addByTwoPoints(
                vertices[i], vertices[(i + 1) % 6])
            line.isFixed = True
    for sketch_point in sketch.sketchPoints:
        if not sketch_point.isFullyConstrained:
            sketch_point.isFixed = True
    return sketch


def extrude_profiles(component, sketch, start_expression, depth_expression,
                     operation, name):
    profiles = C.ObjectCollection.create()
    for profile in sketch.profiles:
        profiles.add(profile)
    if profiles.count == 0:
        raise RuntimeError("No profiles in " + sketch.name)
    inp = component.features.extrudeFeatures.createInput(profiles, operation)
    inp.startExtent = F.OffsetStartDefinition.create(
        C.ValueInput.createByString(start_expression))
    inp.setDistanceExtent(False, C.ValueInput.createByString(depth_expression))
    if operation == F.FeatureOperations.CutFeatureOperation:
        inp.participantBodies = list(component.bRepBodies)
    feature = component.features.extrudeFeatures.add(inp)
    feature.name = name
    sketch.isVisible = False
    return feature


def clear_component(component):
    for feature in sorted(list(component.features),
                          key=lambda item: item.timelineObject.index,
                          reverse=True):
        feature.deleteMe()
    for sketch in list(component.sketches):
        sketch.deleteMe()


def remove_timeline_group(design, name):
    groups = design.timeline.timelineGroups
    for index in range(groups.count - 1, -1, -1):
        group = groups.item(index)
        if group.name == name:
            group.deleteMe(False)


def group_component_timeline(design, component, name):
    objects = []
    for sketch in component.sketches:
        if sketch.timelineObject:
            objects.append(sketch.timelineObject)
    for feature in component.features:
        if feature.timelineObject:
            objects.append(feature.timelineObject)
    indexes = [item.index for item in objects]
    if not indexes or max(indexes) - min(indexes) + 1 != len(indexes):
        raise RuntimeError("Non-contiguous timeline for " + component.name)
    group = design.timeline.timelineGroups.add(min(indexes), max(indexes))
    group.name = name
    group.isCollapsed = True


def build_pla_cradle(root):
    occurrence = next((o for o in root.occurrences if o.component.name in
                       ("HUB_RIGHT_MATRIX_ELEVATED_SHIM",
                        "HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA")), None)
    if occurrence is None:
        raise RuntimeError("Existing right-matrix hub carrier was not found")
    component = occurrence.component
    clear_component(component)
    component.name = "HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA"

    sketch = circle_sketch(component, "SK_PLA_MATRIX_M3_STANDOFFS",
                           MATRIX_HOLES, "hubRMM3BossOD")
    extrude_profiles(component, sketch, "%s mm" % MATRIX_REAR_Y,
                     "hubRMSeatY - %s mm" % MATRIX_REAR_Y,
                     F.FeatureOperations.NewBodyFeatureOperation,
                     "FT_PLA_MATRIX_M3_STANDOFFS")

    # Widen only the head end of each standoff.  A counterbore inside the
    # original 6 mm boss would leave an unprintable wall around a common M3
    # head; the short 9 mm collars retain the same 1.3 mm minimum radial wall
    # as the 6 mm stem around its 3.4 mm through-hole.
    sketch = circle_sketch(component, "SK_PLA_MATRIX_M3_HEAD_COLLARS",
                           MATRIX_HOLES, "hubRMM3HeadCollarOD")
    extrude_profiles(component, sketch,
                     "hubRMSeatY - hubRMM3HeadCollarDepth",
                     "hubRMM3HeadCollarDepth",
                     F.FeatureOperations.JoinFeatureOperation,
                     "FT_PLA_MATRIX_M3_HEAD_COLLARS")

    # Material-efficient end web: a 3 mm seat-level beam spans the bosses,
    # while tapered gussets carry it down only near the M3 columns. In the
    # supplied print orientation the continuous seat edge is on the build
    # plate, so the taper grows inward without support material.
    sketch = tapered_web_sketch_xy(component,
                                   "SK_PLA_TAPERED_END_WEBS_XY")
    extrude_profiles(component, sketch, "-6.212 mm", "5 mm",
                     F.FeatureOperations.JoinFeatureOperation,
                     "FT_PLA_TAPERED_END_WEB_BOTTOM")
    extrude_profiles(component, sketch, "44.960 mm", "5 mm",
                     F.FeatureOperations.JoinFeatureOperation,
                     "FT_PLA_TAPERED_END_WEB_TOP")

    # Both seat rails are supported at both ends by the structural webs. The
    # complete 3 mm-wide left-rail end lies inside each 6 mm M3 boss profile,
    # leaving only the clean cylindrical exterior visible at the junction.
    sketch = rectangle_sketch(component, "SK_PLA_HUB_SEAT_SIDE_RAILS", [
        (54.1, 57.1, -1.212, 44.960),
        (88.0, 92.0, -1.212, 44.960),
    ])
    extrude_profiles(component, sketch, "hubRMFrameY",
                     "hubRMSeatY - hubRMFrameY",
                     F.FeatureOperations.JoinFeatureOperation,
                     "FT_PLA_HUB_SEAT_SIDE_RAILS")

    # Matching transverse rails support the 30 x 40 mm footprint when the hub
    # is rotated 90/270 degrees. They overlap both side rails, so each is also
    # supported at both ends rather than cantilevered from one wall.
    sketch = rectangle_sketch(component, "SK_PLA_HUB_SEAT_END_RAILS", [
        (55.5, 89.0, -1.212, 4.0),
        (55.5, 89.0, 36.0, 41.0),
    ])
    extrude_profiles(component, sketch, "hubRMFrameY",
                     "hubRMSeatY - hubRMFrameY",
                     F.FeatureOperations.JoinFeatureOperation,
                     "FT_PLA_HUB_SEAT_END_RAILS")

    sketch = circle_sketch(component, "SK_PLA_HUB_NOTCH_NUT_PADS",
                           ALL_NOTCH_CENTERS, "hubRMNotchPadOD")
    extrude_profiles(component, sketch, "hubRMFrameY",
                     "hubRMSeatY - hubRMFrameY",
                     F.FeatureOperations.JoinFeatureOperation,
                     "FT_PLA_HUB_NOTCH_NUT_PADS")

    sketch = circle_sketch(component, "SK_PLA_MATRIX_M3_CLEARANCES",
                           MATRIX_HOLES, "hubRMMatrixM3Clearance")
    extrude_profiles(component, sketch, "%s mm" % (MATRIX_REAR_Y - 0.2),
                     "hubRMSeatY - %s mm + 0.5 mm" % (MATRIX_REAR_Y - 0.2),
                     F.FeatureOperations.CutFeatureOperation,
                     "FT_PLA_MATRIX_M3_CLEARANCES")

    # Recess the bearing plane by 4.2 mm.  With the measured 19.49 mm stack,
    # an M3 x 20 screw then retains about 4.71 mm of pilot engagement.  The
    # 6.4 mm pocket accepts both 5.5 mm DIN 84 / ISO 4762 heads and common
    # 6.0 mm M3 pan heads without relying on slicer scaling.
    sketch = circle_sketch(component, "SK_PLA_MATRIX_M3_HEAD_RECESSES",
                           MATRIX_HOLES, "hubRMM3HeadPocketD")
    extrude_profiles(component, sketch,
                     "hubRMSeatY - hubRMM3HeadPocketDepth",
                     "hubRMM3HeadPocketDepth + 0.2 mm",
                     F.FeatureOperations.CutFeatureOperation,
                     "FT_PLA_MATRIX_M3_HEAD_RECESSES")

    sketch = circle_sketch(component, "SK_PLA_HUB_M2_CLEARANCES",
                           ALL_NOTCH_CENTERS, "hubRMHubM2Clearance")
    extrude_profiles(component, sketch, "hubRMFrameY - 0.2 mm",
                     "hubRMSeatY - hubRMFrameY + 0.5 mm",
                     F.FeatureOperations.CutFeatureOperation,
                     "FT_PLA_HUB_M2_CLEARANCES")

    sketch = hexagon_sketch(component, "SK_PLA_HUB_M2_CAPTIVE_NUTS",
                            ALL_NOTCH_CENTERS, 4.2)
    extrude_profiles(component, sketch, "hubRMFrameY - 0.2 mm",
                     "hubRMHubNutDepth + 0.2 mm",
                     F.FeatureOperations.CutFeatureOperation,
                     "FT_PLA_HUB_M2_CAPTIVE_NUTS")

    # D-flat clearance for the display-carrier tab, made as a native cut.
    sketch = rectangle_sketch(component, "SK_PLA_DISPLAY_CARRIER_RELIEF",
                              [(49.0, 52.8, 43.0, 52.0)])
    extrude_profiles(component, sketch, "12.5 mm",
                     "hubRMSeatY - 12.5 mm + 0.5 mm",
                     F.FeatureOperations.CutFeatureOperation,
                     "FT_PLA_DISPLAY_CARRIER_RELIEF")

    if component.bRepBodies.count != 1:
        raise RuntimeError("Expected one connected PLA body, got %d" %
                           component.bRepBodies.count)
    body = component.bRepBodies.item(0)
    if not body.isSolid or body.lumps.count != 1:
        raise RuntimeError("PLA cradle is not one connected solid")
    body.name = "HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA"
    return occurrence


def build_realistic_hub_reference(root):
    occurrence = next((o for o in root.occurrences if o.component.name in
                       ("REF_RIGHT_MATRIX_USB_HUB",
                        "REF_RIGHT_MATRIX_USB_HUB_REALISTIC")), None)
    if occurrence is None:
        raise RuntimeError("USB hub reference was not found")
    component = occurrence.component
    clear_component(component)
    component.name = "REF_RIGHT_MATRIX_USB_HUB_REALISTIC"

    sketch = rectangle_sketch(component, "SK_REF_HUB_PCB_40X30",
                              [(HUB_X0, HUB_X1, 5.0, 35.0)])
    extrude_profiles(component, sketch, "hubRMSeatY", "hubRMHubPCBT",
                     F.FeatureOperations.NewBodyFeatureOperation,
                     "FT_REF_HUB_PCB_40X30")

    sketch = component.sketches.add(component.xZConstructionPlane)
    sketch.name = "SK_REF_HUB_U_NOTCHES_3X3"
    for x_mm, z_mm in PRIMARY_NOTCH_CENTERS:
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
            point(sketch, x_mm, z_mm), 0.15)
        circle.isFixed = True
    rectangle(sketch, 51.3, 53.0, 18.5, 21.5)
    rectangle(sketch, 90.0, 91.7, 18.5, 21.5)
    extrude_profiles(component, sketch, "hubRMSeatY - 0.2 mm",
                     "hubRMHubPCBT + 0.4 mm",
                     F.FeatureOperations.CutFeatureOperation,
                     "FT_REF_HUB_U_NOTCHES_3X3")

    # Outputs face downward into the larger free routing area.
    usb_rectangles = []
    for x in (57.25, 71.5, 85.75):
        usb_rectangles.append((x - 4.45, x + 4.45, 4.0, 11.35))
    for x in (57.25, 85.75):
        usb_rectangles.append((x - 4.45, x + 4.45, 28.65, 36.0))
    sketch = rectangle_sketch(component, "SK_REF_USB_C_RECEPTACLES",
                              usb_rectangles)
    extrude_profiles(component, sketch, "hubRMSeatY + hubRMHubPCBT",
                     "hubRMUSBH", F.FeatureOperations.NewBodyFeatureOperation,
                     "FT_REF_FIVE_USB_C_RECEPTACLES")

    sketch = rectangle_sketch(component, "SK_REF_HUB_MAJOR_COMPONENTS", [
        (68.35, 75.15, 15.55, 24.75),
        (66.2, 76.8, 28.15, 32.15),
    ])
    extrude_profiles(component, sketch, "hubRMSeatY + hubRMHubPCBT", "1.55 mm",
                     F.FeatureOperations.NewBodyFeatureOperation,
                     "FT_REF_HUB_MAJOR_COMPONENTS")

    sketch = rectangle_sketch(component, "SK_REF_HUB_SMD_ENVELOPES", [
        (53.0, 66.5, 22.0, 31.0), (77.5, 88.0, 21.0, 30.0),
        (62.5, 68.0, 12.0, 20.0), (76.0, 81.5, 11.0, 20.0),
    ])
    extrude_profiles(component, sketch, "hubRMSeatY + hubRMHubPCBT", "0.65 mm",
                     F.FeatureOperations.NewBodyFeatureOperation,
                     "FT_REF_HUB_SMD_ENVELOPES")

    sketch = rectangle_sketch(component, "SK_REF_RIGHT_MATRIX_1X9_PLUG_KEEP_OUT",
                              [(95.1, 98.8, 6.9, 31.0)])
    extrude_profiles(component, sketch, "%s mm" % MATRIX_REAR_Y, "10.3 mm",
                     F.FeatureOperations.NewBodyFeatureOperation,
                     "FT_REF_RIGHT_MATRIX_1X9_PLUG_KEEP_OUT")
    for i, body in enumerate(component.bRepBodies):
        body.name = "USB_HUB_REFERENCE_ONLY_%02d" % (i + 1)


def run(_context: str):
    app = C.Application.get()
    design = F.Design.cast(app.activeProduct)
    root = design.rootComponent
    remove_timeline_group(design, "REFERENCE - RIGHT MATRIX USB HUB")
    remove_timeline_group(design, "USB HUB CRADLE - RIGHT MATRIX PLA")
    parameters = [
        ("hubRMHubW", "40 mm", "Measured USB hub PCB width"),
        ("hubRMHubH", "30 mm", "Measured USB hub PCB height"),
        ("hubRMHubPCBT", "1.6 mm", "USB hub PCB thickness"),
        ("hubRMOverallH", "32 mm", "Hub footprint including receptacles"),
        ("hubRMUSBW", "8.9 mm", "Approximate USB-C receptacle width"),
        ("hubRMUSBD", "7.35 mm", "Approximate USB-C receptacle depth"),
        ("hubRMUSBH", "3.4 mm", "Approximate USB-C height above PCB"),
        ("hubRMFrameY", "%.2f mm" % FRAME_Y,
         "Cable-tunnel roof / rail underside"),
        ("hubRMSeatY", "%.2f mm" % SEAT_Y, "Hub PCB support plane"),
        ("hubRMM3BossOD", "6.0 mm", "Compact PLA matrix-standoff outside diameter"),
        ("hubRMMatrixM3Clearance", "3.4 mm", "M3 normal clearance"),
        ("hubRMM3HeadCollarOD", "9.0 mm",
         "Local reinforced collar around each recessed M3 head"),
        ("hubRMM3HeadCollarDepth", "5.0 mm",
         "Axial depth of each local M3 head collar"),
        ("hubRMM3HeadPocketD", "6.4 mm",
         "FDM clearance for M3 cylinder, socket-cap, and pan heads"),
        ("hubRMM3HeadPocketDepth", "4.2 mm",
         "M3 head recess yielding about 4.71 mm engagement with M3 x 20"),
        ("hubRMNotchOpening", "3 mm", "Hub U-notch opening width"),
        ("hubRMNotchDepth", "3 mm", "Hub U-notch depth"),
        ("hubRMNotchPadOD", "6.8 mm", "Minimum practical PLA pad around M2 nut"),
        ("hubRMHubM2Clearance", "2.2 mm", "M2 normal clearance"),
        ("hubRMHubNutAF", "4.2 mm", "M2 captive-nut pocket AF"),
        ("hubRMHubNutDepth", "1.8 mm", "M2 captive-nut pocket depth"),
    ]
    for name, expression, comment in parameters:
        upsert_parameter(design, name, expression, comment)

    carrier = build_pla_cradle(root)
    build_realistic_hub_reference(root)
    component = carrier.component
    unconstrained = [s.name for s in component.sketches if not s.isFullyConstrained]
    if unconstrained:
        raise RuntimeError("Unconstrained cradle sketches: " + ", ".join(unconstrained))
    obsolete = design.userParameters.itemByName("hubRMHubM2P5Clearance")
    if obsolete:
        obsolete.deleteMe()
    for obsolete_name in ("hubRMBaseWallY", "hubRMMatrixHeadPocketD",
                          "hubRMMatrixHeadPocketDepth",
                          "hubRMWebLowerFilletR", "hubRMWebUpperFilletR"):
        obsolete = design.userParameters.itemByName(obsolete_name)
        if obsolete:
            obsolete.deleteMe()
    reference = next(o.component for o in root.occurrences
                     if o.component.name == "REF_RIGHT_MATRIX_USB_HUB_REALISTIC")
    group_component_timeline(design, reference,
                             "REFERENCE - RIGHT MATRIX USB HUB")
    group_component_timeline(design, component,
                             "USB HUB CRADLE - RIGHT MATRIX PLA")
    print("Rebuilt HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA")
    print("One connected solid; %d fully constrained sketches" % component.sketches.count)
    print("Minimum production rail thickness: 3.0 mm; tapered webs: 5.0 mm")
    print("M3 head recess: 6.4 mm diameter x 4.2 mm deep in 9.0 mm collars")
    print("M3 x 20 nominal front-shell engagement: 4.71 mm")
    print("Central cable tunnel roof starts at Y = %.2f mm" % FRAME_Y)
    print("Hub seat Y = %.2f mm" % SEAT_Y)
    print("Document intentionally left unsaved")
