from utils.config_helper import ConfigHelper
from datetime import datetime

class Logger():
    def __init__(self):
        pass

    @staticmethod
    def log_config(filename="simulation.txt"):
        """
        Appends the current configuration to the log file.
        """
        config_path = ConfigHelper().config_path
        with open(config_path, 'r') as config_file:
            config_data = config_file.read()

        current_time = datetime.now()
        formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
        with open(filename, 'a') as results_file:
            results_file.write("\n\n--- SIMULATION CONFIGURATION ---\n")
            results_file.write(f"{formatted_time}\n")
            results_file.write(config_data)
            results_file.write("\n\n--------------------------------\n")

    @staticmethod  
    def log_results(atk_enabled, pre_bend, tx_msg, rx_msg, atk_msg=None, filename="simulation.txt"):
        """
        Append simulation results to the log file.
        """
        with open(filename, 'a') as results_file:
            results_file.write("\n--- SIMULATION RESULTS ---\n\n")
            results_file.write(f"Attack Enabled: {atk_enabled}\n")
            results_file.write(f"Cable Pre-Bent at Start: {pre_bend}\n")
            results_file.write(f"Original Message: {tx_msg}\n")
            results_file.write(f"Message at Receiver: {rx_msg}\n")
            if atk_msg is not None:
                results_file.write(f"Attacker Read Message: {atk_msg}\n")



        
