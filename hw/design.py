"""PL60C DMX wake-up lamp controller - single source of truth for schematic + PCB.

Every Part lists: KiCad symbol, footprint, LCSC part number, schematic position and the
net attached to each pin (None = intentionally unconnected).
"""
import uuid

class Part:
    def __init__(self, ref, lib_id, value, footprint, pins, lcsc='', mpn='', desc='', datasheet='',
                 sch_pos=(0, 0), sch_rot=0, pcb_pos=(0, 0), pcb_rot=0, side='top', dnp=False,
                 stub=2.54, power_symbols_any=False, ref_pos=None, val_pos=None, jlc_rot=0):
        self.ref, self.lib_id, self.value, self.footprint = ref, lib_id, value, footprint
        self.pins = pins  # pin number -> net name
        self.lcsc, self.mpn, self.desc, self.datasheet = lcsc, mpn, desc, datasheet
        self.sch_pos, self.sch_rot = sch_pos, sch_rot
        self.pcb_pos, self.pcb_rot, self.side, self.dnp = pcb_pos, pcb_rot, side, dnp
        self.stub, self.power_symbols_any = stub, power_symbols_any
        self.ref_pos, self.val_pos = ref_pos, val_pos
        self.jlc_rot = jlc_rot   # extra rotation to add for the JLCPCB CPL file
        self.uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'pl60c.' + ref))

class Design:
    def __init__(self):
        self.parts = []
        self.texts = []   # (text, x, y, size, bold)
        self.boxes = []   # (x1,y1,x2,y2)
        self.pwr_flags = {}
        self.paper = 'A3'
        self.title = 'PL60C DMX wake-up lamp controller'
        self.date = '2026-09-02'
        self.rev = 'A'
        self.company = 'amodo design'
        self.sch_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'pl60c.sheet'))
        self.board = dict(w=76.0, h=52.0, corner=2.5)

    def add(self, *parts):
        self.parts.extend(parts)
        return parts[0] if len(parts) == 1 else parts

    def by_ref(self, ref):
        return next(p for p in self.parts if p.ref == ref)

    def nets(self):
        n = {}
        for p in self.parts:
            for pin, net in p.pins.items():
                if net is not None:
                    n.setdefault(net, []).append((p.ref, pin))
        return n

# ---------------------------------------------------------------- footprints
R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C0805 = 'Capacitor_SMD:C_0805_2012Metric'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'
SOT23_6 = 'Package_TO_SOT_SMD:SOT-23-6'
SOIC8 = 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
SW_TACT = 'Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92'   # 6x6 mm 4-leg SMD tactile (TS-6606 compatible)

def build():
    d = Design()
    G = 2.54
    # =============================== schematic block: USB & power (x 20..120) ===============================
    d.texts += [('USB-C input & 3.3 V regulator', 20, 20, 2.5, True)]
    d.boxes += [(18, 14, 128, 120)]
    d.add(Part('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C 16P', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
               {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND',
                'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
                'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_D+', 'B6': 'USB_D+', 'A7': 'USB_D-', 'B7': 'USB_D-',
                'A8': None, 'B8': None},
               lcsc='C165948', mpn='TYPE-C-31-M-12', desc='USB-C receptacle 16P, USB 2.0 (HRO TYPE-C-31-M-12)',
               sch_pos=(45, 65), pcb_pos=(4.2, 26), pcb_rot=90))
    d.add(Part('R1', 'Device:R', '5.1k', R0603, {'1': 'CC1', '2': 'GND'}, lcsc='C25905', desc='5.1k 0603 1% (USB-C CC pull-down)',
               sch_pos=(75, 80), pcb_pos=(11.5, 20), pcb_rot=0))
    d.add(Part('R2', 'Device:R', '5.1k', R0603, {'1': 'CC2', '2': 'GND'}, lcsc='C25905', desc='5.1k 0603 1% (USB-C CC pull-down)',
               sch_pos=(85, 80), pcb_pos=(11.5, 32), pcb_rot=0))
    d.add(Part('U4', 'Power_Protection:USBLC6-2SC6', 'USBLC6-2SC6', SOT23_6,
               {'1': 'USB_D+', '6': 'USB_D+', '3': 'USB_D-', '4': 'USB_D-', '2': 'GND', '5': 'VBUS'},
               lcsc='C7519', mpn='USBLC6-2SC6', desc='USB ESD protection array', sch_pos=(100, 100), pcb_pos=(13, 26), pcb_rot=90))
    d.add(Part('F1', 'Device:Polyfuse', '0.75A PTC', 'Fuse:Fuse_1206_3216Metric', {'1': 'VBUS', '2': '+5V'},
               lcsc='C70069', desc='PTC resettable fuse 1206, 0.75 A hold', sch_pos=(70, 40), sch_rot=90, pcb_pos=(19, 10), pcb_rot=0))
    d.add(Part('C1', 'Device:C', '10uF', C0805, {'1': '+5V', '2': 'GND'}, lcsc='C15850', desc='10uF 25V X5R 0805',
               sch_pos=(82, 50), pcb_pos=(26, 10), pcb_rot=0))
    d.add(Part('U2', 'Regulator_Linear:AMS1117-3.3', 'AMS1117-3.3', 'Package_TO_SOT_SMD:SOT-223-3_TabPin2',
               {'3': '+5V', '2': '+3V3', '1': 'GND'}, lcsc='C6186', mpn='AMS1117-3.3', desc='LDO 3.3V 1A SOT-223',
               sch_pos=(100, 40), pcb_pos=(34, 10), pcb_rot=0))
    d.add(Part('C2', 'Device:C', '10uF', C0805, {'1': '+3V3', '2': 'GND'}, lcsc='C15850', desc='10uF 25V X5R 0805',
               sch_pos=(115, 50), pcb_pos=(42, 10), pcb_rot=0))
    d.add(Part('C3', 'Device:C', '100nF', C0603, {'1': '+3V3', '2': 'GND'}, lcsc='C14663', desc='100nF 50V X7R 0603',
               sch_pos=(122, 50), pcb_pos=(46, 10), pcb_rot=0))
    d.pwr_flags = {'+5V': (60, 100), 'GND': (60, 108)}
    # =============================== ESP32-S3 (x 140..260) ===============================
    d.texts += [('ESP32-S3-WROOM-1 module, reset / boot', 140, 20, 2.5, True)]
    d.boxes += [(138, 14, 262, 150)]
    U1 = Part('U1', 'RF_Module:ESP32-S3-WROOM-1', 'ESP32-S3-WROOM-1-N8', 'RF_Module:ESP32-S3-WROOM-1',
              {'1': 'GND', '40': 'GND', '41': 'GND', '2': '+3V3', '3': 'EN',
               '27': 'IO0_BOOT', '13': 'USB_D-', '14': 'USB_D+',
               '10': 'DMX_TX', '11': 'DMX_RX', '9': 'DMX_DE',
               '25': 'LED_DATA', '5': 'BTN_USER', '6': 'BUZZER',
               '12': 'EXP_SDA', '17': 'EXP_SCL', '18': 'EXP_IO10', '19': 'EXP_IO11',
               '36': 'RXD0', '37': 'TXD0'},
              lcsc='C2913202', mpn='ESP32-S3-WROOM-1-N8', desc='ESP32-S3 WiFi/BLE module, 8 MB flash, PCB antenna',
              sch_pos=(200, 80), pcb_pos=(38, 34), pcb_rot=0)
    for pn in ['4', '7', '8', '15', '16', '20', '21', '22', '23', '24', '26', '28', '29', '30', '31', '32', '33', '34', '35', '38', '39']:
        U1.pins.setdefault(pn, None)
    d.add(U1)
    d.add(Part('C4', 'Device:C', '10uF', C0805, {'1': '+3V3', '2': 'GND'}, lcsc='C15850', desc='10uF 25V X5R 0805', sch_pos=(150, 40), pcb_pos=(52, 44), pcb_rot=90))
    d.add(Part('C5', 'Device:C', '100nF', C0603, {'1': '+3V3', '2': 'GND'}, lcsc='C14663', desc='100nF 50V X7R 0603', sch_pos=(158, 40), pcb_pos=(52, 40), pcb_rot=90))
    d.add(Part('R3', 'Device:R', '10k', R0603, {'1': '+3V3', '2': 'EN'}, lcsc='C25804', desc='10k 0603', sch_pos=(150, 65), pcb_pos=(24, 44), pcb_rot=0))
    d.add(Part('C6', 'Device:C', '1uF', C0603, {'1': 'EN', '2': 'GND'}, lcsc='C15849', desc='1uF 50V X7R 0603', sch_pos=(158, 78), pcb_pos=(24, 47), pcb_rot=0))
    d.add(Part('SW1', 'Switch:SW_Push', 'RESET', SW_TACT, {'1': 'EN', '2': 'GND'}, lcsc='C318884', desc='Tactile switch 6x6 SMD', sch_pos=(150, 90), pcb_pos=(14, 46), pcb_rot=0))
    d.add(Part('R4', 'Device:R', '10k', R0603, {'1': '+3V3', '2': 'IO0_BOOT'}, lcsc='C25804', desc='10k 0603', sch_pos=(150, 110), pcb_pos=(24, 50), pcb_rot=0))
    d.add(Part('SW2', 'Switch:SW_Push', 'BOOT', SW_TACT, {'1': 'IO0_BOOT', '2': 'GND'}, lcsc='C318884', desc='Tactile switch 6x6 SMD', sch_pos=(150, 130), pcb_pos=(26, 46), pcb_rot=0))
    # =============================== DMX / RS-485 (x 270..410) ===============================
    d.texts += [('DMX512 output (RS-485, 3.3 V transceiver)', 272, 20, 2.5, True)]
    d.boxes += [(270, 14, 412, 120)]
    d.add(Part('U3', 'Interface_UART:MAX3485', 'MAX3485', SOIC8,
               {'1': 'DMX_RX', '2': 'DMX_DE', '3': 'DMX_DE', '4': 'DMX_TX', '5': 'GND', '6': 'DMX_A', '7': 'DMX_B', '8': '+3V3'},
               lcsc='C6785', mpn='MAX3485ESA+T', desc='RS-485 transceiver 3.3V half-duplex SOIC-8', sch_pos=(300, 60), pcb_pos=(58, 20), pcb_rot=0))
    d.add(Part('C7', 'Device:C', '100nF', C0603, {'1': '+3V3', '2': 'GND'}, lcsc='C14663', desc='100nF 50V X7R 0603', sch_pos=(280, 45), pcb_pos=(58, 13), pcb_rot=0))
    d.add(Part('R7', 'Device:R', '10k', R0603, {'1': 'DMX_DE', '2': 'GND'}, lcsc='C25804', desc='10k 0603 (DE pull-down: receiver idle until firmware drives)', sch_pos=(282, 90), pcb_pos=(52, 20), pcb_rot=90))
    d.add(Part('D1', 'Diode:SM712_SOT23', 'SM712', SOT23, {'1': 'DMX_A', '2': 'DMX_B', '3': 'GND'},
               lcsc='C58274', mpn='SM712', desc='RS-485 TVS array +12/-7V SOT-23', sch_pos=(330, 90), pcb_pos=(66, 26), pcb_rot=0))
    d.add(Part('R6', 'Device:R', '120R', R0603, {'1': 'DMX_A', '2': 'DMX_B'}, lcsc='C22787', desc='120R termination - DNP (fit only if this board ends the DMX line)',
               sch_pos=(345, 65), pcb_pos=(66, 32), pcb_rot=0, dnp=True))
    d.add(Part('J2', 'Connector_Audio:XLR5', 'XLR-5 female (DMX OUT)', 'Connector_Audio:Jack_XLR_Neutrik_NC5FAH_Horizontal',
               {'1': 'GND', '2': 'DMX_B', '3': 'DMX_A', '4': None, '5': None},
               lcsc='', mpn='NC5FAH', desc='XLR 5-pin female, horizontal PCB mount (DMX OUT)', sch_pos=(385, 60), pcb_pos=(60, 40), pcb_rot=0))
    d.add(Part('J3', 'Connector:Screw_Terminal_01x03', 'DMX pigtail', 'TerminalBlock:TerminalBlock_bornier-3_P5.08mm',
               {'1': 'GND', '2': 'DMX_B', '3': 'DMX_A'}, lcsc='C474881', mpn='KF301-5.0-3P', desc='Screw terminal 3P 5.08 mm (alt. DMX wire output: GND, D-, D+)',
               sch_pos=(385, 95), pcb_pos=(66, 8), pcb_rot=0))
    # =============================== UI: RGB LED, user button, buzzer (x 140..260, y 160..280) ===============================
    d.texts += [('User interface: RGB status LED, user button, alarm buzzer', 140, 165, 2.5, True)]
    d.boxes += [(138, 158, 262, 285)]
    d.add(Part('D2', 'LED:WS2812B', 'WS2812B', 'LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm',
               {'1': '+3V3', '2': None, '3': 'GND', '4': 'LED_DATA_R'},
               lcsc='C2761795', mpn='WS2812B-B/T', desc='Addressable RGB LED 5050 (powered from 3V3 as on ESP32-S3-DevKitC)', sch_pos=(160, 195), pcb_pos=(40, 48), pcb_rot=0))
    d.add(Part('R8', 'Device:R', '330R', R0603, {'1': 'LED_DATA', '2': 'LED_DATA_R'}, lcsc='C23138', desc='330R 0603 series (WS2812 data)', sch_pos=(145, 210), sch_rot=90, pcb_pos=(46, 48), pcb_rot=0))
    d.add(Part('C8', 'Device:C', '100nF', C0603, {'1': '+3V3', '2': 'GND'}, lcsc='C14663', desc='100nF 50V X7R 0603', sch_pos=(180, 195), pcb_pos=(40, 44), pcb_rot=0))
    d.add(Part('R5', 'Device:R', '10k', R0603, {'1': '+3V3', '2': 'BTN_USER'}, lcsc='C25804', desc='10k 0603', sch_pos=(200, 195), pcb_pos=(8, 44), pcb_rot=0))
    d.add(Part('SW3', 'Switch:SW_Push', 'USER', SW_TACT, {'1': 'BTN_USER', '2': 'GND'}, lcsc='C318884', desc='Tactile switch 6x6 SMD (snooze / manual on)', sch_pos=(200, 215), pcb_pos=(6, 46), pcb_rot=0))
    d.add(Part('R9', 'Device:R', '1k', R0603, {'1': 'BUZZER', '2': 'Q1_B'}, lcsc='C21190', desc='1k 0603', sch_pos=(220, 250), sch_rot=90, pcb_pos=(60, 46), pcb_rot=0))
    d.add(Part('Q1', 'Transistor_BJT:S8050', 'S8050', SOT23, {'2': 'Q1_B', '1': 'GND', '3': 'BZ_N'},
               lcsc='C2146', mpn='S8050', desc='NPN 0.5A SOT-23 buzzer driver', sch_pos=(240, 250), pcb_pos=(60, 50), pcb_rot=0))
    d.add(Part('D3', 'Diode:1N4148W', '1N4148W', 'Diode_SMD:D_SOD-123', {'1': '+5V', '2': 'BZ_N'}, lcsc='C81598', desc='Flyback diode SOD-123', sch_pos=(255, 225), sch_rot=90, pcb_pos=(66, 50), pcb_rot=0))
    d.add(Part('BZ1', 'Device:Buzzer', 'MLT-8530', 'Buzzer_Beeper:MagneticBuzzer_CUI_CMT-8504-100-SMT', {'1': '+5V', '2': 'BZ_N'},
               lcsc='C94599', mpn='MLT-8530', desc='Magnetic buzzer 8.5 mm SMD, 3-5 V, passive (drive with PWM ~2.7 kHz)', sch_pos=(245, 200), sch_rot=0, pcb_pos=(70, 44), pcb_rot=0))
    # =============================== Expansion / debug headers (x 270..410, y 130..200) ===============================
    d.texts += [('Expansion (I2C RTC / sensor) and UART0 debug headers', 272, 165, 2.5, True)]
    d.boxes += [(270, 158, 412, 230)]
    d.add(Part('J4', 'Connector_Generic:Conn_01x06', 'EXPANSION', 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
               {'1': '+3V3', '2': 'GND', '3': 'EXP_SDA', '4': 'EXP_SCL', '5': 'EXP_IO10', '6': 'EXP_IO11'},
               lcsc='C2337', desc='Pin header 1x6 2.54 mm', sch_pos=(300, 190), pcb_pos=(70, 20), pcb_rot=0))
    d.add(Part('J5', 'Connector_Generic:Conn_01x04', 'UART0', 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
               {'1': '+3V3', '2': 'GND', '3': 'TXD0', '4': 'RXD0'},
               lcsc='C2337', desc='Pin header 1x4 2.54 mm', sch_pos=(360, 190), pcb_pos=(70, 30), pcb_rot=0))
    # =============================== Mechanical ===============================
    d.texts += [('Mounting holes M3', 20, 165, 2.5, True)]
    for i, (x, y) in enumerate([(3.5, 3.5), (72.5, 3.5), (3.5, 48.5), (72.5, 48.5)], 1):
        d.add(Part(f'H{i}', 'Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', {}, desc='Mounting hole M3', sch_pos=(30 + 15 * i, 180), pcb_pos=(x, y)))
    return d
