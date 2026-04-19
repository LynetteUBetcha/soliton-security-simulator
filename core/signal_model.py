import numpy as np

class Signal():
    """
    Represents a dual-polarization QPSK modulated optical pulse train.
    """
    def __init__(self, num_samples, time_window_ps, peak_power_w, pulse_width_ps, symbols_x, symbols_y):
        self.num_samples = num_samples
        self.time_window_s = time_window_ps * 1e-12
        self.T0_s = pulse_width_ps * 1e-12
        self.P0_w = peak_power_w
        
        # Store ideal data for EVM calculations
        self.ideal_symbols_x = np.array(symbols_x)
        self.ideal_symbols_y = np.array(symbols_y)
        
        # Ensure the amount of data on both axes is the same
        if len(self.ideal_symbols_x) != len(self.ideal_symbols_y):
            raise ValueError("X and Y symbol arrays must be the same length.")
        self.num_symbols = len(self.ideal_symbols_x)
        
        # Create the time grid
        self.time_array = np.linspace(-self.time_window_s/2, self.time_window_s/2, num_samples)
        self.time_step = self.time_window_s / num_samples
        
        # Generate the dual-polarization modulated data stream
        self.complex_amplitude_x, self.complex_amplitude_y = self._generate_dp_pulse_train()

    def _generate_dp_pulse_train(self):
        """
        Generates a sequence of solitons across both X and Y polarizations.
        Splits total peak power equally between the two axes.
        """
        total_signal_x = np.zeros(self.num_samples, dtype=complex)
        total_signal_y = np.zeros(self.num_samples, dtype=complex)
        
        # Bit Period calculation to space the pulses evenly
        bit_period_s = self.time_window_s / (self.num_symbols + 1)
        start_time = -self.time_window_s/2 + bit_period_s
        
        axis_power = self.P0_w / 2
        
        for i in range(self.num_symbols):
            pulse_center_t = start_time + (i * bit_period_s)
            
            # The physical sech envelope (same for both axes)
            envelope = np.sqrt(axis_power) * (1.0 / np.cosh((self.time_array - pulse_center_t) / self.T0_s))
            
            # X-Axis Modulation
            sym_x = self.ideal_symbols_x[i]
            mod_x = envelope * (sym_x / np.abs(sym_x))
            total_signal_x += mod_x
            
            # Y-Axis Modulation
            sym_y = self.ideal_symbols_y[i]
            mod_y = envelope * (sym_y / np.abs(sym_y))
            total_signal_y += mod_y
            
        return total_signal_x, total_signal_y

    def get_current_width(self):
        """
        Calculates the RMS width using the combined energy of both polarizations.
        """
        # Calculate combined power profile
        power_x = np.abs(self.complex_amplitude_x)**2
        power_y = np.abs(self.complex_amplitude_y)**2
        total_power = power_x + power_y
        
        # Normalize the power to treat it like a probability distribution
        norm_power = total_power / np.sum(total_power)
        
        # Calculate the "Center of Mass" of the pulse
        t_mean = np.sum(self.time_array * norm_power)
        
        # Calculate the variance (spread) of the pulse
        t_var = np.sum(((self.time_array - t_mean)**2) * norm_power)
        t_rms = np.sqrt(t_var)
        
        # Convert RMS width back to the theoretical Soliton T0 parameter
        t0_current = t_rms * (2 * np.sqrt(3) / np.pi)
        
        return t0_current

    def get_total_peak_power(self):
        """
        Returns the combined peak power across both axes.
        """
        total_power = np.abs(self.complex_amplitude_x)**2 + np.abs(self.complex_amplitude_y)**2
        return np.max(total_power)