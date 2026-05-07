from experiments.scenarios import Scenario

def main():

    Scenario.run_scenario(attack_enabled=True, pre_bend=False, show_plts=False, save_plots=False)

if __name__ == "__main__":
    main()