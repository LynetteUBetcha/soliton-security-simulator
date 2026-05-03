from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from scipy.fft import fft, ifft, fftfreq
from utils import physics_utils as phys

if TYPE_CHECKING:
    from core.signal_model import Signal

class Fiber():
    """
    Contains the attributes and physics methods specific to the fiber optic cabling.
    """
    
    def __init__(self, length_km, attenuation_db_km, mode_field_diameter_um, lambda_0_max_nm,
                 S_0_max, center_wavelength_nm, pmd_coefficient, n_linear_idx,
                  n2_nonlinear_idx, macro_bend_loss_db, symbiotic_lock_tolerance):
        
        # Speed of light constant
        self.c = 299792458

        # Raw parameters
        self.length_m = length_km * 1000
        self.center_wavelength_nm = center_wavelength_nm
        self.center_lambda_m = center_wavelength_nm * 1e-9
        self.pmd_coefficient = pmd_coefficient
        self.n_linear_idx = n_linear_idx
        self.macro_bend_loss_db = macro_bend_loss_db
        self.symbiotic_lock_tolerance = symbiotic_lock_tolerance

        # Initialize fiber profile here so it can be dynamically updated later
        self.control_profile = None
        self.coupling_efficiency = 0.0
        self.xpm_efficiency_profile = None


        # Effective area
        self.A_eff_m2 = np.pi * ((mode_field_diameter_um * 1e-6) / 2)**2

        # Gamma
        self.gamma = (2 * np.pi * n2_nonlinear_idx) / (self.center_lambda_m * self.A_eff_m2)

        # Alpha/loss
        self.alpha_np_m = (attenuation_db_km / (10 * np.log10(np.exp(1)))) / 1000
        self.baseline_alpha_np_m = self.alpha_np_m

        # Chromatic dispersion
        l0 = lambda_0_max_nm
        l = center_wavelength_nm
        self.D = (S_0_max / 4) * (l - (l0**4 / l**3))

        # Beta2
        self.beta2 = -(self.center_lambda_m**2 / (2 * np.pi * self.c)) * (self.D * 1e-6)

        # Beta3
        self.beta3 = ((self.center_lambda_m / (2 * np.pi * self.c))**2 * (self.center_lambda_m**2 * S_0_max * 1e-3 + 2 * self.center_lambda_m * self.D * 1e-6))     

    def propagate_signal(self, signal: Signal, num_steps: int, control_beam=None):
        """
        Uses the Split-Step Fourier Method to propagate the DP-QPSK signal.
        Incorporates Cross-Phase Modulation (XPM) if a control beam is present.
        """
        dz = self.length_m / num_steps

        # Extract arrays for both polarizations
        A_x = signal.complex_amplitude_x
        A_y = signal.complex_amplitude_y
        
        # Calculate angular frequency grid
        omega = 2 * np.pi * fftfreq(signal.num_samples, d=signal.time_step)

        # Pre-calculate the Control Beam Profile and Walk-Off Penalty
        self.update_control_profile(control_beam, num_steps)

        for step in range(num_steps):
            current_distance_m = step * dz

            if control_beam is not None:
                # Distributed Raman Amplification (DRA)
                # Calculate how much power the control beam has lost to the attacker's tap if it occurred
                distance_to_rx = self.length_m - current_distance_m
                healthy_baseline_power = control_beam["power_w"] * np.exp(-self.baseline_alpha_np_m * distance_to_rx)
                survival_ratio = self.control_profile[step] / max(healthy_baseline_power, 1e-20)
                
                # Apply the Symbiotic Gain to counter natural attenuation
                lock_tolerance = self.symbiotic_lock_tolerance
                if survival_ratio >= lock_tolerance:
                    effective_alpha = self.alpha_np_m * (1.0 - survival_ratio)
                else:
                    effective_alpha = self.alpha_np_m
                
                # Cross-Phase Modulation (XPM)
                # Apply the walk-off penalty to calculate the effective interference power
                P_control = self.control_profile[step] * self.coupling_efficiency

                xpm_multiplier = self.xpm_efficiency_profile[step]
            else:
                effective_alpha = self.alpha_np_m
                P_control = 0.0
                xpm_multiplier = 0

            # Linear operator calculated every loop for dynamic events (i.e., tap occurs)
            linear_operator = np.exp( (-effective_alpha/2 - 1j*(self.beta2/2)*omega**2 - 1j*(self.beta3/6)*omega**3) * dz )

            # Nonlinear step (time domain)
            # The pulse is squeezed by its combined power (SPM) plus the Control Beam (XPM)
            total_pulse_power = np.abs(A_x)**2 + np.abs(A_y)**2
            
            # Calculate the shared phase shift
            nonlinear_phase_shift = np.exp(1j * self.gamma * (total_pulse_power + xpm_multiplier * P_control) * dz)
            
            # Apply shift to both polarizations
            A_x = A_x * nonlinear_phase_shift
            A_y = A_y * nonlinear_phase_shift

            if control_beam is not None and survival_ratio < lock_tolerance:
                # The tumbling control beam randomly rotates the phase of the forward pulse.
                # This creates a chaotic "Random Walk" that destroys QPSK data.
                phase_jitter_x = np.exp(1j * np.random.uniform(-0.15, 0.15, size=len(A_x))) 
                phase_jitter_y = np.exp(1j * np.random.uniform(-0.15, 0.15, size=len(A_y))) 
                
                A_x = A_x * phase_jitter_x
                A_y = A_y * phase_jitter_y

            # Linear step (frequency domain)
            A_x_f = fft(A_x) * linear_operator
            A_y_f = fft(A_y) * linear_operator
            
            A_x = ifft(A_x_f)
            A_y = ifft(A_y_f)

            # Update signal object state and yield to the main control loop
            signal.complex_amplitude_x = A_x
            signal.complex_amplitude_y = A_y
            
            yield signal, current_distance_m
    
    def calculate_stability(self, signal: Signal):
        """
        Calculates current soliton order (N).
        """
        # Peak power in Watts
        P0 = signal.get_total_peak_power()

        # Pulse width
        T0 = signal.get_current_width()

        N_squared = (self.gamma * P0 * T0**2) / np.abs(self.beta2)

        return np.sqrt(N_squared)

    def induce_loss(self, bend_radius_mm):
        """
        Simulates physical disturbance by increasing local attenuation.
        Converts dB loss to Nepers/meter.
        """

        # If bend is very sharp, induce a larger loss
        if bend_radius_mm < 15:
            added_loss_np_km = phys.db_to_neper_power(self.macro_bend_loss_db * 5)
        else:
            added_loss_np_km = phys.db_to_neper_power(self.macro_bend_loss_db)

        # km to m
        added_loss_np_m = added_loss_np_km / 1000.0

        self.alpha_np_m += added_loss_np_m

    def update_control_profile(self, control_beam, num_steps, tap_location_km=None, siphon_percentage=0.0):
        """
        Calculates and stores the control profile as an object attribute.
        Can be called mid-flight by main.py to simulate dynamic environmental changes.
        """
        self.control_profile = self.calculate_control_beam_profile(control_beam["power_w"], num_steps,  tap_location_km, siphon_percentage)

        delta_lambda_nm = abs(self.center_wavelength_nm - control_beam["wavelength_nm"])
        self.coupling_efficiency = np.exp(-(delta_lambda_nm / 5.0)**2)

    def calculate_control_beam_profile(self, rx_power_w, num_steps, tap_location_km=None, siphon_percentage=0.0):
        """
        Calculates the backward-propagating control beam power profile.
        The beam starts at the Receiver (end of the array) and attenuates as it travels backward to the Tx.
        """
        dz = self.length_m / num_steps
        control_profile = np.zeros(num_steps)
        self.xpm_efficiency_profile = np.full(num_steps, 2.0) # profile starts with full, clean parallel polarization
        
        for step in range(num_steps):
            z_m = step * dz
            # Calculate distance from the Receiver
            distance_from_rx = self.length_m - z_m
            
            # Attenuate the Rx power based on distance traveled
            control_profile[step] = rx_power_w * np.exp(-self.alpha_np_m * distance_from_rx)

            # Update the XPM profile with random noise from tap location forward to transmitter
            if tap_location_km is not None and (z_m / 1000.0) <= tap_location_km:
                control_profile[step] = control_profile[step] * (1.0 - siphon_percentage)
                self.xpm_efficiency_profile[step] = np.random.uniform(0.67, 2.0)
            
        return control_profile

