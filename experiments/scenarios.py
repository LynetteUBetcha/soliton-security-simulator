import copy
import numpy as np
from utils.config_helper import ConfigHelper
from core.fiber import Fiber
from hardware.transmitter import Transmitter
from hardware.receiver import Receiver
from experiments.attacker import Attacker
from hardware.instruments import OpticalBackscatterReflectometer
from pathlib import Path

class Scenario():
    def __init__(self):
        pass

    def run_scenario(attack_enabled=True, pre_bend=True):

        print("=== INITIALIZING SYMBIOTIC FIBER SIMULATION ===")
        
        config_path = Path(__file__).resolve().parent.parent / "config/config.yml"

        # 1. Load System Configuration
        config = ConfigHelper(config_path)
        
        # 2. Instantiate Hardware Modules
        fiber = Fiber(
            length_km=config.length_km,
            attenuation_db_km=config.attenuation_db_km,
            mode_field_diameter_um=config.mode_field_diameter_um,
            lambda_0_max_nm=config.lambda_0_max_nm,
            S_0_max=config.S_0_max,
            center_wavelength_nm=config.center_wavelength_nm,
            pmd_coefficient=config.pmd_coefficient,
            n_linear_idx=config.n_linear_idx,
            n2_nonlinear_idx=config.n2_nonlinear_m2_w,
            macro_bend_loss_db=config.macro_bend_loss_db,
            symbiotic_lock_tolerance=config.symbiotic_lock_tolerance,
            noise_per_km_w=config.noise_per_km_w
        )

        rx = Receiver()
        tx = Transmitter(
            laser_power_w=config.tx_power_mw,
            pulse_width_ps=config.pulse_width_ps,
            repition_rate_ps=config.tx_repetition_rate_ps
        )
        attacker = Attacker(siphon_percentage=config.siphon_percentage)

        # 3. Define the Scenario Parameters
        secret_message = config.message
        total_steps = config.total_steps     

        attack_location_km = config.attack_location_km
        time_to_attack = config.km_until_attack_occurs
        
        # --- PHASE 1: THE SYMBIOTIC HANDSHAKE ---
        print("\n--- PHASE 1: ESTABLISHING LOCK ---")
        # Rx turns on the backward-propagating control laser
        physical_seed = OpticalBackscatterReflectometer().generate_physical_seed(fiber)
        
        control_beam = rx.emit_symbiotic_control_beam(physical_seed=physical_seed)             
        
        signal = tx.generate_optical_payload(secret_message, control_beam, total_steps, fiber)
        print(f"[TX] Payload Generated. Target string: {secret_message}")

        # --- PHASE 2: PRE-ATTACK PROPAGATION ---
        print("\n--- PHASE 2: PROPAGATION ---")
        current_distance = 0.0
        
        if attack_enabled:
            # Propagate up to the exact attack location
            attack_generator = fiber.propagate_signal(signal, total_steps, control_beam)
            for current_signal, dist_m in attack_generator:
                current_distance = dist_m / 1000.0 # Convert to km
                
                # Log stability at 10km intervals
                if current_distance % 10 == 0 and int(current_distance) != 0:
                    rx_symbols_x, rx_symbols_y = rx.extract_symbols(current_signal)
                    final_string = rx.read_optical_payload(rx_symbols_x, rx_symbols_y)
                    print(f"\nSTRING AT {current_distance} KM: {final_string}")

                if current_distance == time_to_attack:
                     print("\n--- FIBER TAP ATTACK ---")
                     attacker.tap_fiber(fiber, bend_radius_mm=config.bend_radius_mm)

                     fiber.update_control_profile(control_beam, total_steps, attack_location_km, config.siphon_percentage)

                # Check for attack
                if current_distance == attack_location_km:

                     # Attacker pulls the light out of the fiber
                     stolen_string = attacker.intercept_payload(current_signal)
                     print(f"ATTACKER Intercepted String: {stolen_string}")
                     current_signal.apply_siphon_loss(config.siphon_percentage)

        else:
            generator = fiber.propagate_signal(signal, total_steps, control_beam)

            for current_signal, dist_m in generator:
                current_distance = dist_m / 1000.0
                if current_distance % 10 == 0 and int(current_distance) != 0:
                    rx_symbols_x, rx_symbols_y = rx.extract_symbols(current_signal)
                    final_string = rx.read_optical_payload(rx_symbols_x, rx_symbols_y)
                    print(f"\nSTRING AT {current_distance} KM: {final_string}")

        # --- PHASE 5: LEGITIMATE RECEIVER READOUT ---
        print("\n--- PHASE 5: LINK TERMINATION ---")
        # The surviving, highly entropic light reaches the Rx
        rx_symbols_x, rx_symbols_y = rx.extract_symbols(current_signal)
        final_string = rx.read_optical_payload(rx_symbols_x, rx_symbols_y)
        
        print(f"[RX] Final Received String: {final_string}")
        print("=== SIMULATION COMPLETE ===")