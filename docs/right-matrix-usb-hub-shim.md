# Optional USB-hub parts

These parts support an optional internal USB hub. They are not required for the
core enclosure.

The design uses a nominal 40 × 30 × 1.6 mm hub PCB. Actual boards can differ.
Check your hub, connectors, and cables before installation.

## Available parts

| Part | Quantity | File |
| --- | ---: | --- |
| Right-matrix open cradle | 1 | [`HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA.3mf`](../export/3mf/HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA.3mf) |
| Upper retainer | 1 | [`HUB_RETAINER_UPPER.3mf`](../export/3mf/HUB_RETAINER_UPPER.3mf) |
| Lower retainer | 1 | [`HUB_RETAINER_LOWER.3mf`](../export/3mf/HUB_RETAINER_LOWER.3mf) |
| Rear tray | 1 | [`HUB_REAR_TRAY.3mf`](../export/3mf/HUB_REAR_TRAY.3mf) |

Select only the parts that match your installation.

## Right-matrix cradle

The cradle mounts above the right button matrix. It uses the four existing M3
mounting axes.

Two end webs connect the matrix standoffs. Side rails and transverse rails
support the hub PCB. The open center gives access to the matrix harness.

The cradle supports four hub orientations. Rotate the hub in 90° increments to
select the best cable direction.

The original orientation puts the three output ports toward the larger cable
space. It puts the USB input and power input toward the top.

## Checked clearances

| Item | Position or size |
| --- | --- |
| Matrix PCB rear face | Y = 12.72 mm |
| Matrix plug keep-out | Y = 12.72 to 23.02 mm |
| Seat-rail underside | Y = 27.70 mm |
| Hub PCB support plane | Y = 30.70 mm |
| Hub envelope | Y = 30.70 to 35.70 mm |
| Rear-cover inner surface | Approximately Y = 50.04 mm |
| Hub PCB | 40 × 30 × 1.6 mm |
| Width across USB-C plugs | 32 mm |

Clearance checks found no solid intersection at any of the four cradle
orientations. The checks included the shells, boards, carrier, hub, and cradle.

The hub envelope comes from photographs and caliper measurements. It is not a
manufacturer CAD model.

## Hardware

Use four M3 × 20 mm screws for the cradle. Check the screw engagement against
the actual matrix stack.

Use M2 fasteners for the hub-retainer positions. Select the length for your hub
board and captive nuts.

Use six M3 × 6 mm screws for the rear tray and retainers. Check the complete
hardware stack before installation.

## Printing

The cradle 3MF has its flat seat face on the build plate. The cradle does not
require generated support material.

Follow the [printing guide](printing.md) for general material and inspection
instructions.

## Files

- [Cradle STEP file](../cad/step/HUB_RIGHT_MATRIX_OPEN_CRADLE_PLA.step)
- [Assembly image](visual-reference/right-matrix-usb-hub-recessed-cradle.png)
