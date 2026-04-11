import numpy as np

class fiber():
    
    def __init__(self, length_km, attenuation_db_km, mode_field_diameter_um, lambda_0_min_nm,
                  lambda_0_max_nm, S_0_max, center_wavelength_nm, pmd_coefficient, n_linear_idx,
                  n2_nonlinear_idx, bend_radius_mm, macro_bend_loss_db):
        self.length_km = length_km
        self.attenuation_db_km = attenuation_db_km
        self.mode_field_diameter_um = mode_field_diameter_um
        self.lambda_0_min_nm = lambda_0_min_nm
        self.lambda_0_max_nm = lambda_0_max_nm
        self.S_0_max = S_0_max
        self.center_wavelength_nm = center_wavelength_nm
        self.pmd_coefficient = pmd_coefficient
        self.n_linear_idx = n_linear_idx
        self.n2_nonlinear_idx = n2_nonlinear_idx
        self.bend_radius_mm = bend_radius_mm
        self.macro_bend_loss_db = macro_bend_loss_db
        
        # calculate other parameters
        A_eff = np.pi * (self.mode_field_diameter_um / 2)**2
        self.gamma_km = ((2 * np.pi * self.n2_nonlinear_idx) / ((self.center_wavelength_nm * 10**-9) * A_eff)) * 1000

    # methods
    def propagate_signal():

    def bend_fiber():
