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

    def propagate_signal(self, signal: Signal, num_steps):
        """
        Uses the Split-Step Fourier Method to propagate the signal, yielding after every step.
        """
        dz = self.length_m / num_steps

        # Calculate angular frequency
        A = signal.complex_amplitude_x
        omega = 2 * np.pi * fftfreq(len(A), d=signal.time_step)

        for step in range(num_steps):
            current_distance_m = step * dz

            # Calculate linear operator
            linear_operator = np.exp( (-self.alpha_np_m/2 - 1j*(self.beta2/2)*omega**2 - 1j*(self.beta3/6)*omega**3) * dz )

            # Nonlinear step (time domain)
            A = A * np.exp(1j * self.gamma * np.abs(A)**2 * dz)

            # Linear step (frequency domain)
            A_f = fft(A)
            A_f = A_f * linear_operator
            A = ifft(A_f)

            # Update signal with new pulse condition
            signal.complex_amplitude_x = A
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
            added_loss_np = phys.db_to_neper_power(self.macro_bend_loss_db * 5)
        else:
            added_loss_np = phys.db_to_neper_power(self.macro_bend_loss_db)

        self.alpha_np_m += added_loss_np
