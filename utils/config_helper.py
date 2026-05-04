import yaml
from pathlib import Path

config_path = Path(__file__).parent.parent / "config/config.yml"

class ConfigHelper():

    def __init__(self, config_path = config_path):
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        # --- Fiber Parameters ---
        self.length_km = config['fiber']['length_km']
        self.attenuation_db_km = config['fiber']['attenuation_db_km']
        self.mode_field_diameter_um = config['fiber']['mode_field_diameter_um']
        self.noise_per_km_w = config['fiber']['noise_per_km_w']
        
        # Dispersion Logic
        self.lambda_0_min_nm = config['fiber']['lambda_0_min_nm']
        self.lambda_0_max_nm = config['fiber']['lambda_0_max_nm']
        self.S_0_max = config['fiber']['S_0_max']
        self.center_wavelength_nm = config['fiber']['center_wavelength_nm']
        self.pmd_coefficient = config['fiber']['pmd_coefficient']
        
        # Nonlinearity
        self.n_linear_idx = config['fiber']['n_linear_idx']
        self.n2_nonlinear_m2_w = config['fiber']['n2_nonlinear_m2_w']
        
        # Physical Disturbance
        self.bend_radius_mm = config['fiber']['bend_radius_mm']
        self.macro_bend_loss_db = config['fiber']['macro_bend_loss_db']
        self.symbiotic_lock_tolerance = config['fiber']['symbiotic_lock_tolerance']

        # --- Transmitter Parameters ---
        self.tx_wavelength_nm = config['transmitter']['wavelength_nm']
        self.tx_repetition_rate_ps = config['transmitter']['repetition_rate_ps']
        self.tx_power_mw = config['transmitter']['power_mw']
        self.pulse_width_ps = config['transmitter']['pulse_width_ps']
        self.message = config['transmitter']['msg']

        # --- DSP & Security Parameters ---
        self.stability_threshold = config['security']['stability_threshold']
        self.feedback_latency_ms = config['security']['feedback_latency_ms']
        self.noise_seed = config['security']['noise_seed']

        # --- Attacker Scenario Parameters ---
        self.tap_enabled = config['attacker']['tap_enabled']
        self.siphon_percentage = config['attacker']['siphon_percentage']
        self.attack_location_km = config['attacker']['attack_location_km']
        self.km_until_attack_occurs = config['attacker']['km_until_attack_occurs']

        # Reciever
        self.receiver_power_mw = config['receiver']['base_power_mw']

        # --- Misc Settings ---
        self.total_steps = config['parameters']['total_steps']


