# ARCI Enclosure bill of materials

This bill of materials covers the parts necessary to build the enclosure.
It describes the mechanical package and the hardware needed to populate it; it does not replace the PCB-specific BOMs.

## Printed parts

The supported core print set is listed below. See the [printing guide](docs/printing.md) for material and orientation guidance.

| Part | Quantity | File | Status |
| --- | ---: | --- | --- |
| Front enclosure with label inlays | 1 | [`FRONT_HALF.3mf`](export/3mf/FRONT_HALF.3mf) | Supported core part |
| Back enclosure with label inlays | 1 | [`BACK_HALF.3mf`](export/3mf/BACK_HALF.3mf) | Supported core part |
| MULTI/CH knob | 1 | [`KNOB_MULTI.3mf`](export/3mf/KNOB_MULTI.3mf) | Print separately |
| Dual-encoder outer knob | 2 | [`KNOB_DUAL_OUTER_15.3mf`](export/3mf/KNOB_DUAL_OUTER_15.3mf) | AF/RF and IF-shift outer controls |
| Dual-encoder inner knob | 2 | [`KNOB_DUAL_INNER_11.3mf`](export/3mf/KNOB_DUAL_INNER_11.3mf) | AF/RF and IF-shift inner controls |
| VFO knob core | 1 | [`KNOB_VFO_CORE.3mf`](export/3mf/KNOB_VFO_CORE.3mf) | Print separately |
| VFO grip sleeve | 1 | [`KNOB_VFO_GRIP.3mf`](export/3mf/KNOB_VFO_GRIP.3mf) | Flexible grip material recommended |
| Button cap | 27 | [`BUTTON_CAP.3mf`](export/3mf/BUTTON_CAP.3mf) | Print separately; POWER cap uses red filament |
| Waveshare display carrier | 1 set | [`DISPLAY_CARRIER_WAVESHARE_ARCI.3mf`](export/3mf/DISPLAY_CARRIER_WAVESHARE_ARCI.3mf) | Supported core part |
| Stand bracket | 2 | [`STAND_BRACKET.3mf`](export/3mf/STAND_BRACKET.3mf) | Supported core part |
| Stand support | 2 | [`TILT_STAND_SUPPORT.3mf`](export/3mf/TILT_STAND_SUPPORT.3mf) | Supported core part |
| Near-hinge foot pad | 2 | [`TILT_STAND_FOOT_PAD_NEAR_HINGE.3mf`](export/3mf/TILT_STAND_FOOT_PAD_NEAR_HINGE.3mf) | TPU or rubber alternative |
| Far foot pad | 2 | [`TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.3mf`](export/3mf/TILT_STAND_FOOT_PAD_FAR_FROM_HINGE.3mf) | TPU or rubber alternative |

Optional USB-hub files are listed in the [USB-hub notes](docs/right-matrix-usb-hub-shim.md).

## Core electronics and controls

| Item | Quantity | Notes |
| --- | ---: | --- |
| ARCI main PCB | 1 | Control board; see [ARCI-PCB](https://github.com/stianeklund/ARCI-PCB). |
| Waveshare 5-DSI-TOUCH-A display | 1 | Current preferred display. |
| Waveshare ESP32-P4-Wifi6 | 1 | Connected to the display via MIPI DSI. |
| Left button-matrix PCB | 1 | Link and PCB-specific BOM still to be added. |
| Right button-matrix PCB | 1 | Link and PCB-specific BOM still to be added. |
| Function-key PCB | 1 | Link and PCB-specific BOM still to be added. |
| AF/RF encoder PCB | 1 | Part of the current control assembly. |
| Dual-shaft rotary encoders | 2 | `EC11EBB24C03` or `EC110701N2B` have been used successfully, sourced from AliExpress or similar. |
| MULTI/CH encoder | 1 | I just used a KY-040? type encoder that I had laying around, most encoders work here but take into consideration the shaft length |
| VFO encoder | 1 | Most encoders will work, I opted to use a real RMS20-250-201 by Nidec Copal |

## Buttons and caps

The front panel has 27 button positions. Final quantities must follow the finalized left/right matrix and function-key PCB designs.

| Item | Known part | Notes |
| --- | --- | --- |
| Surface-mount tactile switch | `TL3301SPF160QG` | Purchase part only. Alternatives must match the PCB footprint. |
| Keycaps | As required | DigiKey part numbers: EG1181-ND, and EG1185-ND made by E-Switch |
| Encoder caps | [Aluminum cap reference](https://www.aliexpress.com/item/1005009504767268.html) | These are suprisingly nice. |

In theory it's possible to print key caps as well, the reference model is printable and should work, but I prefer the real deal.

## Enclosure installation hardware

| Assembly | Quantity | Hardware | Notes |
| --- | ---: | --- | --- |
| Shell joint | — | None | The front and rear shells use the integrated snap fit. Assembled overlap is 5.96 mm; mating-groove depth is 6.10 mm. |
| ARCI PCB to display carrier | 4 | M3 × 8–10 mm screws | Confirm length against the final PCB stack and any washers. |
| Waveshare display to carrier | 4 | M2.5 machine screws | Confirm exact length during physical carrier fit testing. |

## Tilt stand

The stand uses two printed brackets, two supports, and four rubber or TPU pads. See [Tilt stand](docs/tilt-stand.md) for printing and assembly.

| Part | Quantity | Specification |
| --- | ---: | --- |
| Bracket screw | 4 | DIN 965 M3 × 12 countersunk |
| Hinge bolt | 2 | DIN 931 M5 × 30 hex bolt; 14 mm plain shank |
| Hinge washer | 2 | DIN 125; 10 × 5.3 × 1 mm |
| Hinge nut | 2 | DIN 985 M5 nyloc; AF 8 mm |
| Foot pads | 4 | Ø28 × 3 mm TPU pads or stick-on rubber equivalent |

## Optional USB-hub and rear-mount hardware

| Assembly | Hardware | Notes |
| --- | --- | --- |
| Right-matrix USB hub cradle | 4 × M3 × 20 mm screws | The cradle uses the matrix mounting axes. Verify actual matrix stack height. |
| Hub retainers | M2 screws or captive-nut hardware as required | Confirm the actual hub board, hole pattern, and screw length. |
| USB hub tray and retainers | 6 × M3 × 6 mm screws | Optional rear mount; verify the hardware stack. |

- The internal USB hub is optional. The cradle is based on a nominal [40 × 30 mm USB hub reference](https://www.aliexpress.com/item/1005009383595449.html); verify the actual board and connector clearances before installation.
- Use suitably short internal USB cables. Check bend radius and plug clearance with the enclosure closed; one [cable reference](https://www.aliexpress.com/item/1005006806265814.html) is available, but cable selection is installation-specific.
- The modeled 8-pin circular rear connector is cosmetic. Select a real connector only if that interface is required.
- Modeled encoder and connector envelopes are neutral fit-check geometry, not manufacturer CAD files. Verify the actual clone or supplier part before printing.

## Still to specify

- Links and final BOMs for the button-matrix and function-key PCBs.
- Exact Waveshare M2.5 screw length after a physical carrier fit check.
- The final rear-connector set and cable harness.
