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
                  n2_nonlinear_idx, macro_bend_loss_db):
        
        # Speed of light constant
        self.c = 299792458

        # Raw parameters
        self.length_m = length_km * 1000
        self.center_wavelength_nm = center_wavelength_nm
        self.center_lambda_m = center_wavelength_nm * 1e-9
        self.pmd_coefficient = pmd_coefficient
        self.n_linear_idx = n_linear_idx
        self.macro_bend_loss_db = macro_bend_loss_db

        # Effective area
        self.A_eff_m2 = np.pi * ((mode_field_diameter_um * 1e-6) / 2)**2

        # Gamma
        self.gamma = (2 * np.pi * n2_nonlinear_idx) / (self.center_lambda_m * self.A_eff_m2)

        # Alpha/loss
        self.alpha_np_m = (attenuation_db_km / (10 * np.log10(np.exp(1)))) / 1000

        # Chromatic dispersion
        l0 = lambda_0_max_nm
        l = center_wavelength_nm
        self.D = (S_0_max / 4) * (l - (l0**4 / l**3))

        # Beta2
        self.beta2 = -(self.center_lambda_m**2 / (2 * np.pi * self.c)) * (self.D * 1e-6)

        # Beta3
        self.beta3 = ((self.center_lambda_m / (2 * np.pi * self.c))**2 * (self.center_lambda_m**2 * S_0_max * 1e-3 + 2 * self.center_lambda_m * self.D * 1e-6))     

    def calculate_control_beam_profile(self, rx_power_w, num_steps):
            """
            Calculates the backward-propagating control beam power profile.
            The beam starts at the Receiver (end of the array) and attenuates as it travels backward to the Tx.
            """
            dz = self.length_m / num_steps
            control_profile = np.zeros(num_steps)
            
            for step in range(num_steps):
                # Calculate distance from the Receiver
                distance_from_rx = self.length_m - (step * dz)
                
                # Attenuate the Rx power based on distance traveled
                control_profile[step] = rx_power_w * np.exp(-self.alpha_np_m * distance_from_rx)
                
            return control_profile

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
        if control_beam is not None:
            control_profile = self.calculate_control_beam_profile(control_beam["power_w"], num_steps)
            delta_lambda_nm = abs(self.center_wavelength_nm - control_beam["wavelength_nm"])
            
            # The walk-off penalty reduces interference if wavelengths are too far apart
            coupling_efficiency = np.exp(-(delta_lambda_nm / 5.0)**2)
        else:
            # Fallback for baseline testing without the lock
            control_profile = np.zeros(num_steps)
            coupling_efficiency = 0.0

        for step in range(num_steps):
            current_distance_m = step * dz

            if control_beam is not None:
                # DISTRIBUTED RAMAN AMPLIFICATION (DRA)
                # Calculate how much power the control beam has lost to the attacker's tap
                distance_to_rx = self.length_m - current_distance_m
                healthy_baseline_power = control_beam["power_w"] * np.exp(-self.alpha_np_m * distance_to_rx)
                survival_ratio = control_profile[step] / healthy_baseline_power
                
                # Apply the Symbiotic Gain to counter natural attenuation
                effective_alpha = self.alpha_np_m * (1.0 - survival_ratio)
                
                # CROSS-PHASE MODULATION (XPM)
                # Apply the walk-off penalty to calculate the effective interference power
                P_control = control_profile[step] * coupling_efficiency
            else:
                effective_alpha = self.alpha_np_m
                P_control = 0.0

            # Linear operator calculated every loop for dynamic events (i.e., tap occurs)
            linear_operator = np.exp( (-effective_alpha/2 - 1j*(self.beta2/2)*omega**2 - 1j*(self.beta3/6)*omega**3) * dz )

            # Nonlinear step (time domain)
            # The pulse is squeezed by its combined power (SPM) plus the Control Beam (XPM)
            total_pulse_power = np.abs(A_x)**2 + np.abs(A_y)**2
            
            # Calculate the shared phase shift
            nonlinear_phase_shift = np.exp(1j * self.gamma * (total_pulse_power + 2 * P_control) * dz)
            
            # Apply shift to both polarizations
            A_x = A_x * nonlinear_phase_shift
            A_y = A_y * nonlinear_phase_shift

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
