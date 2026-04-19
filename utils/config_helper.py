import yaml

class ConfigHelper():

    def __init__(self, config_path = "config.yml"):
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        # --- Fiber Parameters ---
        self.length_km = config['fiber']['length_km']
        self.attenuation_db_km = config['fiber']['attenuation_db_km']
        self.mode_field_diameter_um = config['fiber']['mode_field_diameter_um']
        
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

        # --- Transmitter Parameters ---
        self.tx_wavelength_nm = config['transmitter']['wavelength_nm']
        self.tx_repetition_rate_ghz = config['transmitter']['repetition_rate_ghz']
        self.tx_power_mw = config['transmitter']['power_mw']

        # --- DSP & Security Parameters ---
        self.stability_threshold = config['security']['stability_threshold']
        self.feedback_latency_ms = config['security']['feedback_latency_ms']
        self.noise_seed = config['security']['noise_seed']

        # --- Attacker Scenario Parameters ---
        self.tap_enabled = config['attacker']['tap_enabled']
        self.siphon_percentage = config['attacker']['siphon_percentage']

        # Reciever
        self.receiver_power_mw = config['receiver']['base_power_mw']


