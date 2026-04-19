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
        
        backscatter_profile = np.full(num_points, fiber.alpha_np_m)
        
        return backscatter_profile

    def generate_physical_seed(self, fiber: Fiber):
            """
            Scans the fiber and converts the analog profile into an integer seed.
            """
            # Analog Scan (Returns an array of local attenuation values)
            num_points = int(fiber.length_m / self.spatial_resolution_m)
            backscatter_profile = np.full(num_points, fiber.alpha_np_m)
            
            # Try finding a real backscatter profile to use?
            # and then: backscatter_profile += np.random.normal(0, 1e-6, num_points)

            # Cryptographic Hashing
            profile_bytes = backscatter_profile.tobytes()
            hash_hex = hashlib.sha256(profile_bytes).hexdigest()
            
            # Convert to seed integer using an arbitrary method
            seed_int = int(hash_hex, 16) % (2**32 - 1)
                        
            return seed_int