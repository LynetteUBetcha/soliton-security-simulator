from core.signal_model import Signal
import math

class Transmitter():
    def __init__(self, laser_power_w, pulse_width_ps):
        self.P0 = laser_power_w
        self.T0 = pulse_width_ps

    def generate_optical_payload(self, string_message):
        """
        Takes a string, converts to binary, maps to DP-QPSK, and generates the Signal.
        """
        # String to Binary
        bits = self._string_to_bits(string_message)
        
        # Ensure we have an even number of bits for QPSK
        if len(bits) % 2 != 0:
            bits.append(0)
            
        # Split bits for Dual Polarization
        midpoint = len(bits) // 2
        bits_x = bits[:midpoint]
        bits_y = bits[midpoint:]
        
        # Map to Symbols
        symbols_x = self._bits_to_qpsk(bits_x)
        symbols_y = self._bits_to_qpsk(bits_y)
        
        # Instantiate and return the Signal
        time_window = len(symbols_x) * 50 # 50ps per bit period

        # Dynamically calculate the num_samples using next highest power of 2
        min_samples_needed = len(symbols_x) * 128
        num_samples = 2**(math.ceil(math.log2(min_samples_needed)))
        
        return Signal(
            num_samples=num_samples,
            time_window_ps=time_window,
            peak_power_w=self.P0,
            pulse_width_ps=self.T0,
            symbols_x=symbols_x,
            symbols_y=symbols_y
        )

    def _string_to_bits(self, text):
        """Converts a string to 1s and 0s."""
        binary_string = ''.join(format(ord(char), '08b') for char in text)
        return [int(bit) for bit in binary_string]

    def _bits_to_qpsk(self, bit_list):
        """Maps pairs of bits to complex QPSK symbols."""
        # QPSK Mapping
        mapping = {
            (0, 0): -1 - 1j,
            (0, 1): -1 + 1j,
            (1, 0): 1 - 1j,
            (1, 1): 1 + 1j
        }
        
        symbols = []
        # Process bits in chunks of 2
        for i in range(0, len(bit_list), 2):
            pair = (bit_list[i], bit_list[i+1])
            symbols.append(mapping[pair])
            
        return symbols