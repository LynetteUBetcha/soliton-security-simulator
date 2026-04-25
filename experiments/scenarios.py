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

    def run_scenario(attack_enabled=True):

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
            macro_bend_loss_db=config.macro_bend_loss_db
        )

        rx = Receiver()
        tx = Transmitter(
            laser_power_w=config.tx_power_mw,
            pulse_width_ps=config.pulse_width_ps,
            repition_rate_ps=config.tx_repetition_rate_ps
        )
        attacker = Attacker(siphon_percentage=config.siphon_percentage)

        # 3. Define the Scenario Parameters
        secret_message = "TEST_SECURE_LINK"
        total_steps = 500  # Number of SSFM slices for the 50km run
        step_size_km = config.length_km / total_steps
        
        attack_location_km = 25.0
        steps_to_attack = int(attack_location_km / step_size_km)
        
        # --- PHASE 1: THE SYMBIOTIC HANDSHAKE ---
        print("\n--- PHASE 1: ESTABLISHING LOCK ---")
        # Rx turns on the backward-propagating control laser
        physical_seed = OpticalBackscatterReflectometer().generate_physical_seed(fiber)
        
        control_beam = rx.emit_symbiotic_control_beam(physical_seed=physical_seed)
        
        # Calculate what that beam looks like across the undisturbed fiber
        baseline_control_profile = fiber.calculate_control_beam_profile(
            control_beam["power_w"], total_steps
        )
        
        # Tx measures the beam arriving at z=0 and sets the exact deficit P0
        power_arriving_at_tx = baseline_control_profile[0]
        signal = tx.generate_optical_payload(secret_message, control_beam, fiber)
        print(f"[TX] Payload Generated. Target string: {secret_message}")

        # --- PHASE 2: PRE-ATTACK PROPAGATION ---
        print("\n--- PHASE 2: HEALTHY PROPAGATION ---")
        current_distance = 0.0
        
        if attack_enabled:
            # Propagate up to the exact attack location
            pre_attack_generator = fiber.propagate_signal(signal, steps_to_attack, control_beam)
            for current_signal, dist_m in pre_attack_generator:
                current_distance = dist_m / 1000.0 # Convert to km
                
                # Optional: Log stability at 10km intervals
                if int(current_distance) % 10 == 0 and int(current_distance) != 0:
                    print(f"[{current_distance:.1f} km] Signal stable. N=1.0")

            # --- PHASE 3: THE PHYSICAL ATTACK ---
            print("\n--- PHASE 3: BREACH DETECTED ---")
            # Attacker bends the fiber, instantly changing its physical attenuation
            attacker.tap_fiber(fiber, bend_radius_mm=config.bend_radius_mm)
            
            # Because the fiber changed, the Control Beam profile instantly degrades 
            # from the tap location backward. We must recalculate it.
            remaining_steps = total_steps - steps_to_attack
            compromised_control_profile = fiber.calculate_control_beam_profile(
                control_beam["power_w"], remaining_steps
            )

            # --- PHASE 4: POST-ATTACK COLLAPSE & INTERCEPTION ---
            print("\n--- PHASE 4: ENTROPIC DISPERSAL ---")
            # We resume propagation, but now feeding the compromised control beam into the engine
            post_attack_generator = fiber.propagate_signal(signal, remaining_steps, control_beam)
            
            interception_made = False
            
            for current_signal, dist_m in post_attack_generator:
                current_distance = (dist_m / 1000.0) + attack_location_km
                
                # Give the physics engine 5 km to let the unsupported solitons shatter
                if current_distance >= attack_location_km + 5.0 and not interception_made:
                    print(f"[{current_distance:.1f} km] [ATTACKER] Siphoning payload...")
                    
                    # Attacker pulls the light out of the fiber
                    stolen_string = attacker.intercept_payload(current_signal)
                    print(f"[ATTACKER] Intercepted String: {stolen_string}")
                    interception_made = True
        else:
            generator = fiber.propagate_signal(signal, total_steps, control_beam)

            for current_signal, dist_m in generator:
                current_distance = dist_m / 1000.0
                if int(current_distance) % 10 == 0 and int(current_distance) != 0:
                            rx_symbols_x, rx_symbols_y = rx.extract_symbols(current_signal)
                            final_string = rx.read_optical_payload(rx_symbols_x, rx_symbols_y)
                            print(f"Current string at {current_distance}: {final_string}")

        # --- PHASE 5: LEGITIMATE RECEIVER READOUT ---
        print("\n--- PHASE 5: LINK TERMINATION ---")
        # The surviving, highly entropic light reaches the Rx at 50.0 km
        rx_symbols_x, rx_symbols_y = rx.extract_symbols(current_signal)
        final_string = rx.read_optical_payload(rx_symbols_x, rx_symbols_y)
        
        print(f"[RX] Final Received String: {final_string}")
        print("=== SIMULATION COMPLETE ===")