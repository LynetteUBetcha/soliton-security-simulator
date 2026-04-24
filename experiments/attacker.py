from __future__ import annotations
import numpy as np
import copy
from hardware.receiver import Receiver
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.signal_model import Signal
    from core.fiber import Fiber

class Attacker(Receiver):
    """
    Rogue receiver that taps the fiber to intercept the optical payload.
    Inherits all DSP and decoding capabilities from the legitimate Receiver.
    """
    def __init__(self, siphon_percentage):
        # Initialize the parent Receiver class
        super().__init__() 
        self.siphon_percentage = siphon_percentage

    def tap_fiber(self, fiber: Fiber, bend_radius_mm):
        """
        Executes the physical tap by bending the fiber.
        """
        print(f"\n[ATTACKER] Applying {bend_radius_mm}mm macro-bend to fiber...")
        fiber.induce_loss(bend_radius_mm)

    def intercept_payload(self, signal: Signal):
        """
        Steals a fraction of the light, scales the amplitude down to realistic 
        hardware levels, and attempts to decode the QPSK payload.
        """
        # Create an isolated clone of the signal state at this exact kilometer
        stolen_signal = copy.deepcopy(signal)
        
        # Scale the amplitude based on the power siphon percentage
        amplitude_scaling_factor = np.sqrt(self.siphon_percentage)
        
        stolen_signal.complex_amplitude_x *= amplitude_scaling_factor
        stolen_signal.complex_amplitude_y *= amplitude_scaling_factor
        
        # Use Receiver methods to sample and decode
        rx_symbols_x, rx_symbols_y = self.extract_symbols(stolen_signal)
        decoded_string = self.read_optical_payload(rx_symbols_x, rx_symbols_y)
        
        return decoded_string