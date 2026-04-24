import copy
import numpy as np
from utils.config_helper import ConfigHelper
from core.fiber import Fiber
from hardware.transmitter import Transmitter
from hardware.receiver import Receiver
from experiments.attacker import Attacker
from hardware.instruments import OpticalBackscatterReflectometer
from pathlib import Path
from experiments.scenarios import Scenario

def main():

    Scenario.run_scenario(attack_enabled=False)

if __name__ == "__main__":
    main()