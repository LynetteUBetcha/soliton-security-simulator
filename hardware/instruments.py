import numpy as np
import hashlib
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.fiber import Fiber

class OpticalBackscatterReflectometer():
    """
    Simulates an OBR to generate a physical fingerprint of the fiber link.
    """
    def __init__(self, spatial_resolution_m=10):
        self.spatial_resolution_m = spatial_resolution_m

    def scan_fiber(self, fiber: Fiber):
        """
        Scans the fiber and returns a distributed array of its attenuation profile.
        """
        num_points = int(fiber.length_m / self.spatial_resolution_m)
        
        # In a perfectly undisturbed fiber, this is a flat line of the baseline attenuation.
        # If there's a bend, this array will have a spike at the bend location.
        backscatter_profile = np.full(num_points, fiber.alpha_np_m)
        
        return backscatter_profile

    def generate_fingerprint_hash(self, backscatter_profile):
        """
        Converts the physical analog profile into a digital cryptographic seed.
        """
        # Convert the numpy array to bytes and hash it (e.g., SHA-256)
        profile_bytes = backscatter_profile.tobytes()
        return hashlib.sha256(profile_bytes).hexdigest()