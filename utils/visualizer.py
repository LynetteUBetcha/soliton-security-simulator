from __future__ import annotations
from typing import TYPE_CHECKING
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

if TYPE_CHECKING:
    from core.signal_model import Signal
    from core.fiber import Fiber

class Plotter():
    """
    Generates vizualizations for the simulation
    """
    def __init__(self, save_plots=False, output_dir="results"):
        self.save_plots = save_plots
        self.output_dir = output_dir
        
        if self.save_plots and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        plt.rcParams.update({
            'font.size': 12,
            'axes.labelsize': 14,
            'axes.titlesize': 16,
            'legend.fontsize': 12,
            'lines.linewidth': 2.0,
            'figure.dpi': 200
        })

    def plot_time_domain(self, signal: Signal, title="Time Domain Pulse Envelope"):
        """
        Plots the absolute power of the DP-QPSK pulse train over time.
        """
        # Calculate combined power from complex amplitudes
        power_x = np.abs(signal.complex_amplitude_x)**2
        power_y = np.abs(signal.complex_amplitude_y)**2
        total_power_mw = (power_x + power_y) * 1000 # Convert Watts to mW

        # Time array in picoseconds for readability
        time_ps = signal.time_array * 1e12 

        plt.figure(figsize=(10, 5))
        plt.plot(time_ps, total_power_mw, color='#1f77b4', label='Total Envelope Power')
        
        plt.title(title)
        plt.xlabel("Time (ps)")
        plt.ylabel("Power (mW)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        self._handle_output("time_domain")

    def plot_constellation(self, signal: Signal, title="QPSK Constellation"):
        """
        Plots the I/Q complex phase diagram to show symbol integrity.
        """
        plt.figure(figsize=(6, 6))
        
        # Scatter X and Y polarizations
        plt.scatter(signal.complex_amplitude_x.real, signal.complex_amplitude_x.imag, 
                    alpha=0.5, s=10, color='blue', label='X-Pol')
        plt.scatter(signal.complex_amplitude_y.real, signal.complex_amplitude_y.imag, 
                    alpha=0.5, s=10, color='orange', label='Y-Pol')
        
        # Draw axes
        plt.axhline(0, color='black', linewidth=1, alpha=0.5)
        plt.axvline(0, color='black', linewidth=1, alpha=0.5)
        
        plt.title(title)
        plt.xlabel("In-Phase (I)")
        plt.ylabel("Quadrature (Q)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.axis('equal')
        plt.tight_layout()
        
        self._handle_output("constellation")

    def plot_spatial_profile(self, fiber: Fiber, baseline_profile, attacked_profile=None):
        """
        Plots the Bidirectional Pump profile over the length of the fiber.
        Shows the baseline vs. the collapsed state if a tap is present.
        """
        # Create distance array in km
        num_steps = len(baseline_profile)
        distance_km = np.linspace(0, fiber.length_m / 1000, num_steps)
        
        # Convert profile Watts to mW
        baseline_mw = baseline_profile * 1000

        plt.figure(figsize=(10, 5))
        plt.plot(distance_km, baseline_mw, color='green', linestyle='--', label='Baseline Symbiotic Support')
        
        if attacked_profile is not None:
            attacked_mw = attacked_profile * 1000
            plt.plot(distance_km, attacked_mw, color='red', label='Attacked Support (Tap Loss)')
            
            # Fill the difference to highlight the "siphon"
            plt.fill_between(distance_km, attacked_mw, baseline_mw, color='red', alpha=0.1)

        plt.title("Symbiotic Pump Power Distribution")
        plt.xlabel("Fiber Distance (km)")
        plt.ylabel("Control Beam Power (mW)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        
        self._handle_output("spatial_profile")

    def _handle_output(self, filename_base):
        """Helper to either show or save the plot."""
        current_time = datetime.now()
        formatted_time = current_time.strftime("%d-%m-%Y_%H:%M:%S")
        if self.save_plots:
            filepath = os.path.join(self.output_dir, f"{filename_base}{formatted_time}.png")
            plt.savefig(filepath)
            print(f"Plot saved to: {filepath}")
        else:
            plt.show()
        plt.close()