import numpy as np
from scipy.stats import entropy as scipy_entropy

def calculate_spectral_entropy(complex_amplitude):
    """
    Calculates the Shannon entropy of the signal's power distribution.
    A perfect soliton has low entropy. A collapsed pulse has high entropy.
    """
    # Get the power profile
    power = np.abs(complex_amplitude)**2
    
    # Normalize to create a probability mass function (PMF)
    pmf = power / np.sum(power)
    
    # Calculate Shannon entropy (base 2 for bits)
    return scipy_entropy(pmf, base=2)

def db_to_neper_power(db_val):
    """Converts optical power loss from dB to Nepers."""
    return db_val / (10 * np.log10(np.exp(1)))

def neper_to_db_power(np_val):
    """Converts optical power loss from Nepers to dB."""
    return np_val * (10 * np.log10(np.exp(1)))

def watts_to_dbm(watts):
    """Converts absolute power in Watts to dBm (telecom standard)."""
    # Add a tiny offset to avoid log(0) errors if power drops to absolute zero
    return 10 * np.log10(watts * 1000 + 1e-20)

def add_awgn_noise(complex_amplitude, snr_db):
    """
    Additive White Gaussian Noise to simulate background thermal 
    and amplifier noise in the fiber link.
    """
    signal_power = np.mean(np.abs(complex_amplitude)**2)
    snr_linear = 10**(snr_db / 10)
    noise_power = signal_power / snr_linear
    
    # Generate complex noise
    noise = np.sqrt(noise_power / 2) * (np.random.randn(len(complex_amplitude)) + 1j * np.random.randn(len(complex_amplitude)))
    
    return complex_amplitude + noise

def add_distributed_noise(complex_amplitude, noise_power_per_step):
    """
    Adds a fixed amount of physical noise to the channel.
    """
    noise = np.sqrt(noise_power_per_step / 2) * (
        np.random.randn(len(complex_amplitude)) + 1j * np.random.randn(len(complex_amplitude))
    )
    
    return complex_amplitude + noise

def calculate_evm(received_symbols, ideal_symbols):
    """
    Calculates the Error Vector Magnitude (EVM) as a percentage for a QPSK signal.
    """
    # Ensure arrays match
    if len(received_symbols) != len(ideal_symbols):
        raise ValueError("Symbol arrays must be the same length.")

    # The 'Error Vector' is the physical distance between the ideal point and received point
    error_vectors = received_symbols - ideal_symbols
    
    # Calculate the Root Mean Square (RMS) power of the error
    rms_error_power = np.mean(np.abs(error_vectors)**2)
    
    # Calculate the reference power (usually the peak ideal symbol magnitude)
    reference_power = np.max(np.abs(ideal_symbols)**2)
    
    # Calculate EVM as a percentage
    evm_pct = np.sqrt(rms_error_power / reference_power) * 100
    
    return evm_pct

def calculate_coupling_efficiency(center_wavelength_nm, control_beam_wavelength_nm):
    """
    Calculates coupling efficiency based on the fiber's center wavelength and control beam wavelength
    """
    delta_lambda_nm = abs(center_wavelength_nm - control_beam_wavelength_nm)
    coupling_efficiency = np.exp(-(delta_lambda_nm / 5.0)**2)
    
    return coupling_efficiency