import numpy as np
from core.fiber import Fiber
from core.signal_model import Signal

def run_security_test():
    print("--- Initializing Soliton Security Simulation ---")

    # 1. Instantiate the Fiber (The "Environment")
    # Using the standard G.652 telecom specs we mapped out
    fiber = Fiber(
        length_km=50,
        attenuation_db_km=0.2,       # Standard background loss
        mode_field_diameter_um=9.2,
        lambda_0_max_nm=1324,
        S_0_max=0.092,
        center_wavelength_nm=1550,
        pmd_coefficient=0.1,
        n_linear_idx=1.467,
        n2_nonlinear_idx=2.6e-20,
        macro_bend_loss_db=3.0       # The attacker's tap strength (3dB drop)
    )

    # 2. Automatically calibrate the required laser power for N=1
    pulse_width_ps = 10
    T0_s = pulse_width_ps * 1e-12
    
    # Calculate perfect P0 using the fiber's actual beta2 and gamma
    perfect_p0_w = np.abs(fiber.beta2) / (fiber.gamma * T0_s**2)
    
    print(f"Calibrated Laser Power for N=1 Lock: {perfect_p0_w * 1000:.2f} mW")

    # Instantiate the Signal with the calibrated power
    signal = Signal(
        num_samples=2048,            
        time_window_ps=100,
        peak_power_w=perfect_p0_w,   # Pass the mathematically derived power here      
        pulse_width_ps=pulse_width_ps
    )

    # 3. Test Sequence Variables
    num_steps = 500
    stability_threshold = 0.85       # The point where Entropic Dispersal occurs
    attack_distance_km = 25.0
    attack_triggered = False

    print(f"Propagating signal over {fiber.length_m} km...\n")

    # 4. The Instrumentation Loop (Real-Time SSFM Execution)
    for current_signal, distance_m in fiber.propagate_signal(signal, num_steps):
        distance_km = distance_m / 1000

        # Measure telemetry using the updated DP-QPSK compatible stability method
        current_N = fiber.calculate_stability(current_signal)

        # Log periodically to the console (e.g., every 5 km)
        if distance_km % 5 == 0 or distance_km == 0:
            print(f"[Z: {distance_km:05.1f} km] Soliton Order (N) = {current_N:.4f}")

        # Trigger the Attacker Event
        if distance_km >= attack_distance_km and not attack_triggered:
            print(f"\n[!] ALERT: Physical disturbance detected at {distance_km:.1f} km!")
            fiber.induce_loss(bend_radius_mm=10) # 10mm represents a sharp macro-bend
            attack_triggered = True

        # Check for Symbiotic Lock failure
        if current_N < stability_threshold:
            print(f"\n[CRITICAL FAIL] Entropic Dispersal triggered at {distance_km:.2f} km.")
            print(f"Final Soliton Order: {current_N:.4f} (Below {stability_threshold} threshold)")
            print("Symbiotic lock broken. Halting simulation.")
            break

    # If the loop finishes without breaking
    if current_N >= stability_threshold:
        print("\nSimulation complete: Soliton lock maintained across entire length.")

if __name__ == "__main__":
    run_security_test()