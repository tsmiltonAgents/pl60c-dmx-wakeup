/*
 * PL60C DMX wake-up lamp controller - board pin map and DMX constants (rev A).
 * This is the only "firmware" file in this repo: it documents what the hardware expects.
 * Target: ESP32-S3-WROOM-1 (N16R8) on rev A, ESP32-S3-MINI-1 (N8) on the mini: identical GPIO map.
 * Mini differences: no RESET button, no UART0 header, buzzer is external on the BZ+/BZ- pads.  Framework: ESP-IDF or Arduino-ESP32; DMX via the esp_dmx library.
 */
#pragma once

/* ---- DMX512 transmitter (SP3485EN RS-485, half duplex) ---- */
#define PIN_DMX_TX      17   /* UART TX  -> SP3485 DI          (use UART1 / dmx_port 1)        */
#define PIN_DMX_RX      18   /* UART RX  <- SP3485 RO          (only needed for RDM / monitor) */
#define PIN_DMX_DE      16   /* HIGH = drive the line (DE and /RE tied together, 10k pull-down) */

/* ---- USB ---- */
/* GPIO19 = USB D-, GPIO20 = USB D+ : native USB-Serial/JTAG, nothing to configure. */

/* ---- User interface ---- */
#define PIN_BTN_BOOT     0   /* BOOT button, active low (also strapping pin, safe to read after boot) */
#define PIN_BTN_USER     5   /* USER button, active low, 10k pull-up on board (snooze / manual light) */
#define PIN_RGB_LED     48   /* WS2812B data (330 R series), LED powered from 3V3 like the DevKitC   */
#define PIN_BUZZER       6   /* NPN driver, HIGH = coil energised. Drive with a 2.7 kHz PWM, <=50 % duty */

/* ---- Expansion header J4 (3V3, GND, SDA, SCL, IO10, IO11) ---- */
#define PIN_EXP_SDA      8
#define PIN_EXP_SCL      9
#define PIN_EXP_IO10    10
#define PIN_EXP_IO11    11

/* ---- UART0 debug header J5 (3V3, GND, TX, RX) ---- */
#define PIN_UART0_TX    43
#define PIN_UART0_RX    44

/* ---- DMX512 timing (ANSI E1.11) ---- */
#define DMX_BAUD              250000
#define DMX_BREAK_US             176   /* >= 92 us required, 176 us typical */
#define DMX_MAB_US                12   /* >= 12 us */
#define DMX_START_CODE             0
#define DMX_REFRESH_HZ            44   /* send a full frame at least ~40 Hz; PL60C reported flaky below 44 Hz */
#define DMX_UNIVERSE_SIZE        512

/* ---- Neewer PL60C, fixed personality (DMX start address = channel 1) ---- */
#define PL60C_CH_MODE              1   /* 0-31 CCT, 32-63 HSI, 64-95 FX, 96-127 GEL, 128-159 RGBCW, 160-191 XY */
#define PL60C_CH_INTENSITY         2   /* 0-255 -> 0-100 %                                      */
#define PL60C_CH_CCT               3   /* CCT mode: 0-255 -> 2500-10000 K                       */
#define PL60C_CH_GM                4   /* CCT mode: green/magenta -50 .. +50 (128 = neutral)    */
#define PL60C_MODE_CCT             0
#define PL60C_MODE_HSI            32
#define PL60C_MODE_RGBCW         128
#define PL60C_FOOTPRINT_CHANNELS   9   /* the FX mode uses up to 9 channels; keep the rest zero */
