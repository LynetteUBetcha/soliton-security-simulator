import numpy as np
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.config_helper import ConfigHelper

class Receiver():
    def __init__(self):

        config_vals = ConfigHelper()

        # Baseline values
        self.base_wavelength_nm = config_vals.center_wavelength_nm
        self.base_power_w = config_vals.receiver_power_mw

    def emit_symbiotic_control_beam(self, physical_seed):
        """
        Calculates the exact laser parameters based on the fiber's physical fingerprint.
        """
        # Seed the random number generator so the math is deterministic based on the fiber
        np.random.seed(physical_seed)
        
        # Wavelength Tuning (+/- 2.0 nm shift based on the seed)
        # The control beam be slightly offset from the Soliton to avoid direct interference,
        # but the exact offset dictates the XPM coupling efficiency.
        wavelength_shift = np.random.uniform(-2.0, 2.0)
        tuned_wavelength_nm = self.base_wavelength_nm + wavelength_shift
        
        # Power Tuning (+/- 20% power variation)
        power_shift = np.random.uniform(-0.2, 0.2)
        tuned_power_w = self.base_power_w * (1 + power_shift)
        
        # Reset the random seed so it doesn't affect other parts of the simulation
        np.random.seed(None)
        
        return {
            "power_w": tuned_power_w,
            "wavelength_nm": tuned_wavelength_nm
        }
