# soliton-security-simulator
 This system simulates a secure, encryption-less data transmission system using fiber optics. It operates on the principle of solitons' unique properties to be very stable over long distances, but easily unravel when their environment isn't conducive to their structure. Utilizing a backward propagating control beam based on the fiber's unique physical profile, solitons are formed to carry two bits of information a piece, enhancing transmission speeds. Since the solitons are 'locked' to the control beam, the slightest light leakage from a tapping attack or other physical disturbances completely unravels the solitons into a state of entropy.

## Uses
 While tapping attacks may seem improbable or pointless, many instances of tapping undersea fiber cables have been noted over the years (**1). With most data being robustly encrypted for transit, these attacks are likely aimed exclusively at stealing this data and preserving it until technology advances far enough to decrypt it. This is where the natural properties of solitons can play an important role. Instead of tapping attacks reading clean encrypted data, a locked soliton system would only provide meaningless blobs of light as their system is disturbed and they can no longer hold shape.

 This system would be most useful where the slight overhead of encryption and decryption times are best eliminated. A high-frequency trading system, for example. Naturally, utilizing existing network structures would expose unencrypted data to threats in other parts of the system, so this would be best implemented in an isolated network.

## Installation and Run Instructions
 To run this code on your device, ensure you create an environment based on the config/environment.yml file. To create an environment based on this file, try running the command "conda env create -f environment.yml" after cloning the repository. After configuring your environment, run main.py. There are three booleans to set here: attack_enabled, pre_bend, and save_plots. 

attack_enabled: Dictates whether a tap attack occurs during string transmission.
pre_bend: Dictates whether an attacker already had a fiber tap in place.
save_plots: Tells the program to save the auto-generated plots or not.

## Roadmap and Future Plans
 With the aforementioned distance limit from the uni-directional control beam, I plan on seeing how far a bi-directional pump can take the solitons. In order to meet deadlines for this project, I was unable to dedicate the time necessary to configure the system work with the new pump. In theory, a properly configured system with a bi-directional pump should not only transmit solitons further, but also with more physical sensitivity and security than the uni-directional beam. From there, I would love to build out a physical proof-of-concept, which I initially considered doing instead of a code simulation until I created a BOM and realized how cost-prohibitive it would be. Non-linear fiber or fiber alternatives are not cheap, nor are lasers capable of creating solitons. Alternatively, one could buy somewhere around 10 km of standard fiber cabling, but that is also cost-prohibitive and space-consuming.

## Author
 If you have stumbled upon this project and you have questions or comments, feel free to send me an email: soliton.security.sim@gmail.com