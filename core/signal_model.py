import numpy as np

class Signal():
    """
    Represent the solitons traveling through fiber.
    """

    def __init__(self, num_samples, time_window_ps, peak_power_w, pulse_width_ps):
       
        self.num_samples = num_samples
        
        # Convert picoseconds to SI base units (seconds)
        self.time_window_s = time_window_ps * 1e-12
        self.T0_s = pulse_width_ps * 1e-12
        self.P0_w = peak_power_w
        
        # Create time array centered at t=0
        self.time_array = np.linspace(-self.time_window_s/2, self.time_window_s/2, num_samples)
        self.time_step = self.time_window_s / num_samples
        
        # Initialize X and Y polarization states
        self.complex_amplitude_x, self.complex_amplitude_y = self._generate_dp_soliton()

    def _generate_dp_soliton(self):
        """
        Creates the fundamental soliton shape and splits the power across X and Y axes.
        """
        # Half power to the X polarization
        amplitude_x = np.sqrt(self.P0_w / 2) * (1.0 / np.cosh(self.time_array / self.T0_s))
        
        # Half power to the Y polarization
        amplitude_y = np.sqrt(self.P0_w / 2) * (1.0 / np.cosh(self.time_array / self.T0_s))
        
        return amplitude_x.astype(complex), amplitude_y.astype(complex)

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