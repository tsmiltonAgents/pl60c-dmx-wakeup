"""PL60C DMX wake-up controller - MINI variant (rev A-mini).
Same circuit as design.py, shrunk: ESP32-S3-MINI-1, 4-layer, parts on both sides, 0402 passives,
XLR-5 kept, pigtail terminal / headers / RESET button / mounting holes dropped (XLR flange mounts the board).
"""
from design import Part, Design

R0402 = 'Resistor_SMD:R_0402_1005Metric'
C0402 = 'Capacitor_SMD:C_0402_1005Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'
SOT23_5 = 'Package_TO_SOT_SMD:SOT-23-5'
SOT23_6 = 'Package_TO_SOT_SMD:SOT-23-6'
SOIC8 = 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
SW_TACT = 'Button_Switch_SMD:SW_SPST_TS-1088-xR020'     # XUNPU TS-1088-AR02016, 3.9x3x2 mm (JLC Basic)
TP = 'TestPoint:TestPoint_Pad_1.5x1.5mm'
B = dict(side='bottom')

def build():
    d = Design()
    d.title = 'PL60C DMX wake-up lamp controller - MINI'
    d.rev = 'A-mini'
    d.board = dict(w=38.5, h=29.0, corner=0.6, layers=4, usb_vbus_via=3.2, inner_planes={'In1.Cu': 'GND'}, inner_pours=['In2.Cu'], min_width=0.1, min_clearance=0.1)
    d.via_in_pad = ['U1:61']   # vias in the module's 3x3 centre GND pads (Espressif reference layout)
    # ------------------------------------------------ USB & power
    d.texts += [('USB-C input & 3.3 V regulator', 20, 20, 2.5, True)]
    d.boxes += [(18, 14, 128, 120)]
    d.add(Part('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C 16P', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
               {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND',
                'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
                'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_D+', 'B6': 'USB_D+', 'A7': 'USB_D-', 'B7': 'USB_D-', 'A8': None, 'B8': None},
               lcsc='C165948', mpn='TYPE-C-31-M-12', desc='USB-C receptacle 16P, USB 2.0 (HRO TYPE-C-31-M-12)',
               sch_pos=(45, 65), pcb_pos=(6.4, 25.9), pcb_rot=0))
    d.add(Part('R1', 'Device:R', '5.1k', R0402, {'1': 'CC1', '2': 'GND'}, lcsc='C25905', desc='5.1k 0402 1% (USB-C CC pull-down)', sch_pos=(75, 80), pcb_pos=(3.4, 28.2), **B))
    d.add(Part('R2', 'Device:R', '5.1k', R0402, {'1': 'CC2', '2': 'GND'}, lcsc='C25905', desc='5.1k 0402 1% (USB-C CC pull-down)', sch_pos=(85, 80), pcb_pos=(9.4, 28.2), **B))
    d.add(Part('U4', 'Power_Protection:USBLC6-2SC6', 'USBLC6-2SC6', SOT23_6,
               {'1': 'USB_D+', '6': 'USB_D+', '3': 'USB_D-', '4': 'USB_D-', '2': 'GND', '5': 'VBUS'},
               lcsc='C7519', mpn='USBLC6-2SC6', desc='USB ESD protection array', sch_pos=(100, 100), pcb_pos=(6.4, 27.0), pcb_rot=0, **B))
    d.add(Part('F1', 'Device:Polyfuse', '0.75A PTC', 'Fuse:Fuse_0805_2012Metric', {'1': 'VBUS', '2': '+5V'},
               lcsc='C7472571', mpn='0805L075/6AR', desc='PTC resettable fuse 0805, 0.75 A hold, 6 V', sch_pos=(70, 40), pcb_pos=(13.6, 18.5), **B))
    d.add(Part('C1', 'Device:C', '10uF', C0603, {'1': '+5V', '2': 'GND'}, lcsc='C19702', desc='10uF 10V X5R 0603', sch_pos=(82, 50), pcb_pos=(3.0, 19.8), pcb_rot=90, **B))
    d.add(Part('U2', 'Regulator_Linear:AP2112K-3.3', 'AP2112K-3.3', SOT23_5,
               {'1': '+5V', '2': 'GND', '3': '+5V', '4': None, '5': '+3V3'}, lcsc='C51118', mpn='AP2112K-3.3TRG1', desc='LDO 3.3V 600mA SOT-23-5',
               sch_pos=(100, 40), pcb_pos=(13.8, 22.5), **B))
    d.add(Part('C2', 'Device:C', '10uF', C0603, {'1': '+3V3', '2': 'GND'}, lcsc='C19702', desc='10uF 10V X5R 0603', sch_pos=(115, 50), pcb_pos=(14.5, 25.3), **B))
    d.add(Part('C3', 'Device:C', '100nF', C0402, {'1': '+3V3', '2': 'GND'}, lcsc='C1525', desc='100nF 16V X7R 0402', sch_pos=(122, 50), pcb_pos=(10.6, 20.3), pcb_rot=90, **B))
    d.pwr_flags = {'+5V': (60, 100), 'GND': (60, 108)}
    # ------------------------------------------------ ESP32-S3-MINI-1
    d.texts += [('ESP32-S3-MINI-1 module, boot', 140, 20, 2.5, True)]
    d.boxes += [(138, 14, 262, 150)]
    U1 = Part('U1', 'RF_Module:ESP32-S3-MINI-1', 'ESP32-S3-MINI-1-N8', 'RF_Module:ESP32-S2-MINI-1',
              {'3': '+3V3', '45': 'EN', '4': 'IO0_BOOT', '23': 'USB_D-', '24': 'USB_D+',
               '21': 'DMX_TX', '22': 'DMX_RX', '20': 'DMX_DE', '30': 'LED_DATA', '9': 'BTN_USER', '10': 'BUZZER',
               '12': 'EXP_SDA', '13': 'EXP_SCL'},
              lcsc='C2913206', mpn='ESP32-S3-MINI-1-N8', desc='ESP32-S3 module 15.4x20.5 mm, 8 MB flash, PCB antenna (same land pattern as ESP32-S2-MINI-1)',
              sch_pos=(200, 80), pcb_pos=(5.25, 9.5), pcb_rot=90)
    for n in range(1, 66):
        U1.pins.setdefault(str(n), None)
    for n in [1, 2, 42, 43] + list(range(46, 66)):
        U1.pins[str(n)] = 'GND'
    d.add(U1)
    d.add(Part('C4', 'Device:C', '10uF', C0603, {'1': '+3V3', '2': 'GND'}, lcsc='C19702', desc='10uF 10V X5R 0603', sch_pos=(150, 40), pcb_pos=(12.5, 3.0), **B))
    d.add(Part('C5', 'Device:C', '100nF', C0402, {'1': '+3V3', '2': 'GND'}, lcsc='C1525', desc='100nF 16V X7R 0402', sch_pos=(158, 40), pcb_pos=(3.5, 8.0), **B))
    d.add(Part('R3', 'Device:R', '10k', R0402, {'1': '+3V3', '2': 'EN'}, lcsc='C25744', desc='10k 0402', sch_pos=(150, 65), pcb_pos=(3.5, 10.0), **B))
    d.add(Part('C6', 'Device:C', '1uF', C0402, {'1': 'EN', '2': 'GND'}, lcsc='C52923', desc='1uF 25V X5R 0402 (EN reset delay)', sch_pos=(158, 78), pcb_pos=(3.5, 12.0), **B))
    d.add(Part('R4', 'Device:R', '10k', R0402, {'1': '+3V3', '2': 'IO0_BOOT'}, lcsc='C25744', desc='10k 0402', sch_pos=(150, 110), pcb_pos=(6.5, 8.0), **B))
    d.add(Part('SW2', 'Switch:SW_Push', 'BOOT', SW_TACT, {'1': 'IO0_BOOT', '2': 'GND'}, lcsc='C720477', mpn='TS-1088-AR02016', desc='Tactile switch 3.9x3x2 mm SMD', sch_pos=(150, 130), pcb_pos=(15.3, 21.9)))
    # ------------------------------------------------ DMX / RS-485
    d.texts += [('DMX512 output (RS-485, 3.3 V transceiver)', 272, 20, 2.5, True)]
    d.boxes += [(270, 14, 412, 120)]
    d.add(Part('U3', 'Interface_UART:SP3485EN', 'SP3485EN', SOIC8,
               {'1': 'DMX_RX', '2': 'DMX_DE', '3': 'DMX_DE', '4': 'DMX_TX', '5': 'GND', '6': 'DMX_A', '7': 'DMX_B', '8': '+3V3'},
               lcsc='C8963', mpn='SP3485EN-L/TR', desc='RS-485 transceiver 3.3 V half-duplex SOIC-8', sch_pos=(300, 60), pcb_pos=(15.2, 9.8), pcb_rot=90, **B))
    d.add(Part('C7', 'Device:C', '100nF', C0402, {'1': '+3V3', '2': 'GND'}, lcsc='C1525', desc='100nF 16V X7R 0402', sch_pos=(280, 45), pcb_pos=(14.5, 5.0), **B))
    d.add(Part('R7', 'Device:R', '10k', R0402, {'1': 'DMX_DE', '2': 'GND'}, lcsc='C25744', desc='10k 0402 (DE pull-down)', sch_pos=(282, 90), pcb_pos=(14.7, 14.5), **B))
    d.add(Part('D1', 'Diode:SM712_SOT23', 'PSM712', SOT23, {'1': 'DMX_A', '2': 'DMX_B', '3': 'GND'},
               lcsc='C32677', mpn='PSM712-LF-T7', desc='RS-485 TVS array +12/-7 V SOT-23', sch_pos=(330, 90), pcb_pos=(17.9, 19.4), pcb_rot=90, **B))
    d.add(Part('R6', 'Device:R', '120R', R0402, {'1': 'DMX_A', '2': 'DMX_B'}, lcsc='C25079', desc='120R termination - DNP', sch_pos=(345, 65), pcb_pos=(18.6, 14.4), pcb_rot=0, dnp=True, **B))
    d.add(Part('J2', 'Connector_Audio:XLR5_Ground', 'XLR-5 female (DMX OUT)', 'Connector_Audio:Jack_XLR_Neutrik_NC5FAH_Horizontal',
               {'1': 'GND', '2': 'DMX_B', '3': 'DMX_A', '4': None, '5': None, 'G': None},
               lcsc='C368501', mpn='NC5FAH', desc='Neutrik XLR 5-pin female, horizontal PCB mount (DMX OUT)', sch_pos=(385, 60), pcb_pos=(21.35, 10.3), pcb_rot=0))
    # ------------------------------------------------ UI
    d.texts += [('User interface: RGB status LED, user button, alarm buzzer', 140, 165, 2.5, True)]
    d.boxes += [(138, 158, 262, 285)]
    d.add(Part('D2', 'LED:WS2812B-2020', 'WS2812B-2020', 'LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm',
               {'4': '+3V3', '1': None, '2': 'GND', '3': 'LED_DATA_R'},
               lcsc='C52917434', mpn='WS2812B-2020-V6', desc='Addressable RGB LED 2x2 mm (powered from 3V3 as on Espressif devkits)', sch_pos=(160, 195), pcb_pos=(17.1, 4.0), pcb_rot=90))
    d.add(Part('R8', 'Device:R', '330R', R0402, {'1': 'LED_DATA', '2': 'LED_DATA_R'}, lcsc='C25104', desc='330R 0402 series (WS2812 data)', sch_pos=(145, 215), pcb_pos=(6.5, 12.0), **B))
    d.add(Part('C8', 'Device:C', '100nF', C0402, {'1': '+3V3', '2': 'GND'}, lcsc='C1525', desc='100nF 16V X7R 0402', sch_pos=(180, 195), pcb_pos=(9.5, 12.0), **B))
    d.add(Part('R5', 'Device:R', '10k', R0402, {'1': '+3V3', '2': 'BTN_USER'}, lcsc='C25744', desc='10k 0402', sch_pos=(200, 195), pcb_pos=(6.5, 10.0), **B))
    d.add(Part('SW3', 'Switch:SW_Push', 'USER', SW_TACT, {'1': 'BTN_USER', '2': 'GND'}, lcsc='C720477', mpn='TS-1088-AR02016', desc='Tactile switch 3.9x3x2 mm SMD (snooze / manual on)', sch_pos=(200, 215), pcb_pos=(15.3, 26.0)))
    d.add(Part('R9', 'Device:R', '1k', R0402, {'1': 'BUZZER', '2': 'Q1_B'}, lcsc='C11702', desc='1k 0402', sch_pos=(222, 250), pcb_pos=(6.0, 2.5), **B))
    d.add(Part('Q1', 'Transistor_BJT:S8050', 'S8050', SOT23, {'2': 'Q1_B', '1': 'GND', '3': 'BZ_N'},
               lcsc='C2146', mpn='S8050', desc='NPN 0.5A SOT-23 buzzer driver', sch_pos=(240, 250), pcb_pos=(3.0, 4.0), **B))
    d.add(Part('D3', 'Device:D_Schottky', 'B5819W', 'Diode_SMD:D_SOD-123', {'1': '+5V', '2': 'BZ_N'}, lcsc='C8598', mpn='B5819W SL', desc='Schottky flyback diode SOD-123', sch_pos=(232, 225), pcb_pos=(8.5, 4.5), **B))
    d.add(Part('TP5', 'Connector:TestPoint', 'BZ+', TP, {'1': '+5V'}, desc='External buzzer pad (+5V)', sch_pos=(245, 200), pcb_pos=(28.5, 28.0), **B))
    d.add(Part('TP6', 'Connector:TestPoint', 'BZ-', TP, {'1': 'BZ_N'}, desc='External buzzer pad (driver collector)', sch_pos=(255, 200), pcb_pos=(31.2, 28.0), **B))
    # ------------------------------------------------ test pads (I2C expansion, UART0)
    d.texts += [('Test pads: I2C expansion (RTC / sensor)', 272, 165, 2.5, True)]
    d.boxes += [(270, 158, 412, 230)]
    for i, (net, x) in enumerate([('+3V3', 28.5), ('GND', 31.2), ('EXP_SDA', 33.9), ('EXP_SCL', 36.6)], 1):
        d.add(Part(f'TP{i}', 'Connector:TestPoint', net, TP, {'1': net}, desc='Test pad 1.5 mm', sch_pos=(290 + 18 * i, 190), pcb_pos=(x, 25.5), **B))
    d.texts += [('No mounting holes: the XLR flange (2x M3) mounts the board in its enclosure.', 20, 170, 1.5, False),
                ('Buzzer is off-board on the mini: wire a passive magnetic buzzer between BZ+ and BZ- pads.', 140, 290, 1.5, False)]
    # ------------------------------------------------ silkscreen
    d.silk_refs = False   # too dense for silkscreen designators: they go on the Fab layers
    d.silk = [
        ('BOOT', 15.3, 19.7, 0.8, 0, 'F.SilkS', False),
        ('USER', 15.3, 28.4, 0.8, 0, 'F.SilkS', False),
        ('DMX mini rev A', 32.0, 14.5, 0.8, 0, 'B.SilkS', True),
        ('DMX OUT', 25.5, 3.0, 0.8, 0, 'B.SilkS', True),
        ('3V3 GND SDA SCL', 32.5, 23.5, 0.8, 0, 'B.SilkS', True),
        ('BZ+ BZ-', 35.0, 28.0, 0.8, 0, 'B.SilkS', True),
    ]
    return d
