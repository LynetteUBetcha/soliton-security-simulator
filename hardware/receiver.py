from __future__ import annotations
import numpy as np
from typing import TYPE_CHECKING
from utils.config_helper import ConfigHelper

if TYPE_CHECKING:
    from utils.config_helper import ConfigHelper
    from core.signal_model import Signal

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
        # The control beam should be slightly offset from the Soliton to avoid direct interference,
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
    
    def extract_symbols(self, signal: Signal):
        """
        Acts as the analog-to-digital sampler. 
        Slices the continuous waveform at the center of each bit period to extract the symbols.
        """
        num_symbols = len(signal.ideal_symbols_x)
        received_symbols_x = []
        received_symbols_y = []

        # Recreate the timing grid used by the Transmitter
        bit_period_s = signal.time_window_s / (num_symbols + 1)
        start_time = -signal.time_window_s/2 + bit_period_s        
        
        for i in range(num_symbols):
            target_time = start_time + (i * bit_period_s)
            closest_index = np.argmin(np.abs(signal.time_array - target_time))

            received_symbols_x.append(signal.complex_amplitude_x[closest_index])
            received_symbols_y.append(signal.complex_amplitude_y[closest_index])
            
        # Convert to numpy arrays for vector math
        rx_x = np.array(received_symbols_x)
        rx_y = np.array(received_symbols_y)
        
        # Calculate how far the fiber twisted the first "Pilot" symbol
        phase_error_x = np.angle(rx_x[0]) - np.angle(signal.ideal_symbols_x[0])
        phase_error_y = np.angle(rx_y[0]) - np.angle(signal.ideal_symbols_y[0])
        
        # Unwind the entire array by the accumulated error
        rx_x = rx_x * np.exp(-1j * phase_error_x)
        rx_y = rx_y * np.exp(-1j * phase_error_y)
        
        return rx_x.tolist(), rx_y.tolist()

    def read_optical_payload(self, symbols_x, symbols_y):
        """
        Takes the received QPSK symbols, demaps them to binary,
        and reconstructs the original string message.
        """
        # Demap complex symbols back to bits using a threshold slicer
        bits_x = self._qpsk_to_bits(symbols_x)
        bits_y = self._qpsk_to_bits(symbols_y)
        
        # Recombine the two polarization streams
        total_bits = bits_x + bits_y
        
        # Convert the flat binary array back into an ASCII string
        return self._bits_to_string(total_bits)

    def _qpsk_to_bits(self, symbols):
        """
        Slicer Logic: Demaps noisy QPSK symbols to bit pairs based on their complex quadrant.
        Matches the Tx mapping: 
        Re>0 = Bit 1, Re<0 = Bit 0
        Im>0 = Bit 1, Im<0 = Bit 0
        """
        bits = []
        for sym in symbols:
            # Check the sign of the real part
            bit1 = 1 if sym.real > 0 else 0
            
            # Check the sign of the imaginary part
            bit2 = 1 if sym.imag > 0 else 0
            
            bits.extend([bit1, bit2])
            
        return bits

    def _bits_to_string(self, bit_list):
        """
        Converts a flat list of 1s and 0s back into an ASCII string.
        """
        chars = []
        
        # Process the bits in chunks of 8 (1 byte per character)
        # the Tx might have added to make the payload even.
        for i in range(0, len(bit_list) - 7, 8):
            byte_array = bit_list[i : i+8]
            
            # Convert list of ints [0, 1, 0...] to string "010...", then parse as Base-2 int
            byte_str = ''.join(str(b) for b in byte_array)
            char_code = int(byte_str, 2)
            
            # Append the decoded ASCII character
            chars.append(chr(char_code))
            
        return ''.join(chars)
