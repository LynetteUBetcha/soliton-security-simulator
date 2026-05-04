from utils.config_helper import ConfigHelper
from core.fiber import Fiber
from hardware.transmitter import Transmitter
from hardware.receiver import Receiver
from experiments.attacker import Attacker
from hardware.instruments import OpticalBackscatterReflectometer
from utils.logger import Logger
from utils.visualizer import Plotter

class Scenario():
    def __init__(self):
        pass

    def run_scenario(attack_enabled=True, pre_bend=True, save_plots=True):

        log = Logger()
        log.log_config()

        plotter = Plotter(save_plots)

        print("\n=== INITIALIZING SYMBIOTIC FIBER SIMULATION ===")

        # 1. Load System Configuration
        config = ConfigHelper()
        
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
        stolen_string = None     

        attack_location_km = config.attack_location_km
        time_to_attack = config.km_until_attack_occurs
        
        # 4. Symbiotic handshake
        print("\n--- ESTABLISHING LOCK ---")
        # Rx turns on the backward-propagating control laser
        physical_seed = OpticalBackscatterReflectometer().generate_physical_seed(fiber)
        
        control_beam = rx.emit_symbiotic_control_beam(physical_seed=physical_seed)             
        
        signal = tx.generate_optical_payload(secret_message, control_beam, total_steps, fiber)
        print(f"[TX] Payload Generated. Target string: {secret_message}")

        # Plot signal before propagation
        plotter.plot_time_domain(signal, title=f"TX: Ideal {config.pulse_width_ps}ps Soliton Train")
        plotter.plot_constellation(signal, title="TX: Pristine DP-QPSK Constellation")

        # 5. Propagate the signal through the fiber line
        print("\n--- PROPAGATION ---")
        current_distance = 0.0

        # Snapshot profile for plotting later
        baseline_profile = fiber.calculate_control_beam_profile(rx_power_w=control_beam["power_w"], num_steps=config.total_steps)

        if attack_enabled:

            # Propagate up to the exact attack location
            attack_generator = fiber.propagate_signal(signal, total_steps, control_beam)
            # if the fiber was already bent to begin with, tap the fiber now to induce changes beyond what the control profile should have
            if pre_bend:
                attacker.tap_fiber(fiber, bend_radius_mm=config.bend_radius_mm)
                fiber.update_control_profile(control_beam, total_steps, attack_location_km, config.siphon_percentage)

            for current_signal, dist_m in attack_generator:
                current_distance = dist_m / 1000.0 # Convert to km
                
                # Log stability at 10km intervals
                if current_distance % 10 == 0 and int(current_distance) != 0:
                    rx_symbols_x, rx_symbols_y = rx.extract_symbols(current_signal)
                    final_string = rx.read_optical_payload(rx_symbols_x, rx_symbols_y)
                    print(f"\nSTRING AT {current_distance} KM: {final_string}")

                # if attack occurs while the solitons are on their way to the receiver, bend the fiber now
                if not pre_bend and current_distance == time_to_attack: 
                     print("\n--- FIBER TAP ATTACK OCCURRED UPSTREAM ---")
                     attacker.tap_fiber(fiber, bend_radius_mm=config.bend_radius_mm)

                     fiber.update_control_profile(control_beam, total_steps, attack_location_km, config.siphon_percentage)

                # Check for attack
                if current_distance == attack_location_km:

                     # Attacker pulls small amount of light out of the fiber
                     stolen_string = attacker.intercept_payload(current_signal)
                     print("\n--- ATTACKER READING STRING ---")
                     print(f"\nIntercepted String: {stolen_string}")
                     current_signal.apply_siphon_loss(config.siphon_percentage)
            plotter.plot_time_domain(current_signal, title=f"Attacker: Received Envelope at {config.attack_location_km}km")
            plotter.plot_constellation(current_signal, title=f"Degraded Constellation at {config.attack_location_km}km")

            attacked_profile = fiber.calculate_control_beam_profile(rx_power_w=control_beam["power_w"], num_steps=config.total_steps, 
                                                                    tap_location_km=config.attack_location_km, siphon_percentage=config.siphon_percentage)

        else:
            generator = fiber.propagate_signal(signal, total_steps, control_beam)

            for current_signal, dist_m in generator:
                current_distance = dist_m / 1000.0
                if current_distance % 10 == 0 and int(current_distance) != 0:
                    rx_symbols_x, rx_symbols_y = rx.extract_symbols(current_signal)
                    final_string = rx.read_optical_payload(rx_symbols_x, rx_symbols_y)
                    print(f"\nSTRING AT {current_distance} KM: {final_string}")

        # 6. The receiver reads whatever is there
        print("\n--- LINK TERMINATION ---\n")
        # The surviving light makes it to the rx
        rx_symbols_x, rx_symbols_y = rx.extract_symbols(current_signal)
        final_string = rx.read_optical_payload(rx_symbols_x, rx_symbols_y)
        
        print(f"[RX] Final Received String: {final_string}")

        # Log and plot results
        log.log_results(attack_enabled, pre_bend, secret_message, final_string, stolen_string)
        
        if attack_enabled:
            plotter.plot_spatial_profile(fiber, baseline_profile, attacked_profile)
        else:
            plotter.plot_spatial_profile(fiber, baseline_profile)
            
        print("\n=== SIMULATION COMPLETE ===\n")