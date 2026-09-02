"""Select the design variant: PL60C_VARIANT=a (default, rev A) or mini."""
import os, importlib
VARIANT = os.environ.get('PL60C_VARIANT', 'a')
BOARD = 'pl60c_dmx' if VARIANT == 'a' else 'pl60c_dmx_' + VARIANT
PROD_DIR = 'production' if VARIANT == 'a' else 'production_' + VARIANT

def design():
    return importlib.import_module('design' if VARIANT == 'a' else 'design_' + VARIANT)
