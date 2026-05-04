from experiments.scenarios import Scenario

def main():

    Scenario.run_scenario(attack_enabled=True, pre_bend=False, save_plots=True)

if __name__ == "__main__":
    main()