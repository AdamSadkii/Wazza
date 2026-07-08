## Schematic Complete - Day 6/28/26 (5h58min)

### Overview
Finally finished the schematic! Coming into this schematic, I knew I wanted to focus on one thing: the microcontroller as the main component. However, in hopes of organization, I thought otherwise and considered splitting things up.

### Design Decisions

At first, I originally wanted to split my schematic into different pages, each serving their own purpose. I planned one page for the sensor interface, another for the audio interface, and so on and so forth. However, due to redundancy (I tried to add a connections page combining everything) and time constraints, I realized the easier pathway led to one single schematic instead.

### Architecture

The basis of my schematic focuses on, as said before, my microcontroller: the ESP32. The ESP32 served as the central component of my project, with everything else orbiting around it:

- **ESP32**: The brain of the operation, handling all processing and coordination
- **OLED Display**: Provides the user with basic info and feedback
- **MPU-6050**: Tracks the user's gestures and movements (literally one of the most important parts of my wand LOL)
- **Supporting Components**: Battery management, audio I/O, LED control, all centralized around the microcontroller

### What I Learned

Keeping everything on a single page actually made more sense than I initially thought. The redundancy of multiple connection pages would have just added complexity without clarity. Sometimes simpler is better, and this schematic proves that point.

### Next Steps

Tomorrow, I will get to the PCB and hopefully get most of it done. Although it's an impending doom, I am really excited to work on that aspect of my project! The schematic is solid, so the layout should flow naturally from here.

### Reflection

This feels like a major milestone. The schematic is the blueprint for everything that comes next. Seeing all the connections laid out clearly gives me confidence that the hardware design is sound. Time to bring it to life on the PCB.







## Organizing PCB - Day 6/29/26 (Hour 1)

I'm organizing the PCB! Currently splitting each component on its own but we're figuring it out, though the components are a little hard to figure out, it's okay! 

<img width="773" height="580" alt="image" src="https://github.com/user-attachments/assets/0136daff-c0d4-490e-9324-004016972512" />

## Schematic Fix - Day 6/29/26 (Hours 2-3)

I discovered a major error on the PCB layout where resistors R4 and R5 were both connected directly to the 3.3V line, which would have broken the communication loop. After two hours of troubleshooting, I corrected the wiring paths and utilized several pins that were previously ignored. This process exposed a widespread series of errors throughout the schematic, requiring another two hours of focused adjustments. While the rework was incredibly tedious, tracking down and correcting those design flaws was deeply rewarding.

<img width="1046" height="726" alt="image" src="https://github.com/user-attachments/assets/cbf04ef8-8eba-41d3-afd4-e83758417d50" />
<img width="846" height="903" alt="image" src="https://github.com/user-attachments/assets/432b5a6e-e436-469c-a594-33069c1733a3" />
<img width="1204" height="617" alt="image" src="https://github.com/user-attachments/assets/ba185da1-e040-45e8-b859-ee668cf3fa19" />


## Journal Day 6/29/26 - PCB Almost Done? (Hours: 3)

PCB Layout Started - Day 6/30/26

## Overview

Today was incredibly productive yet absolutely exhausting. I took the massive leap into creating my first-ever physical PCB layout! Moving from the abstract schematic canvas to actual component footprints makes the wand feel real, though it definitely brought some brutal troubleshooting with it.

## Design Decisions & Troubleshooting

I hit a major roadblock early on regarding the OLED screen and the IMU pull-up resistors. During my initial layout check, I realized my wiring accidentally tied both sides of $R4$ and $R5$ directly to the +3.3V line, completely missing the actual SCL and SDA lines!Instead of moving forward with a broken bus, I paused and forced myself to rewire those schematic components properly. It took a couple of hours of careful tracing, but I finally re-ran the check successfully. Once the schematic was cleared, I imported it into the PCB editor and successfully modeled the initial physical flow of the wand—stretching all the way from the USB-C port to the OLED screen placement.

## Architecture

As the layout began coming together, the physical constraints forced me to re-evaluate my component choices:

- ESP32 Module: Looking at the footprint placement, I realized I might have utilized the wrong specific module variant. Thankfully, it's not a catastrophic fix—I just need to swap the symbol/footprint and re-designate the pins to match my existing wiring routing.
- Net Labels: Moving forward, I need to heavily integrate net labels rather than drawing raw local wires. It will make updating the schematic and updating the PCB track layout infinitely smoother.What I LearnedCatching a massive I2C pull-up mistake now instead of after fabrication taught me why electrical checks are so critical. A few hours of frustration today saved weeks of waiting on a broken, un-fixable board later.

## Next Steps

Tomorrow is all about fixing that ESP32 module variant, cleaning up the routing, and finalizing the board outline. There is still a bit of uncertainty about the tight layout, but the goal is to get the CAD fully submitted so we can ship the design files out for manufacturing. Job's not finished—let's get this accepted!

<img width="1071" height="853" alt="image" src="https://github.com/user-attachments/assets/6b969f1c-960b-40bd-b3f9-83a89c678b7d" />
<img width="492" height="397" alt="image" src="https://github.com/user-attachments/assets/6811b899-7b8a-4f35-92b5-3d110f4a0ca5" />

## Schematic Rewire WE ALMOST DONE - Day 6/30/26 (Hours 1-2)

Decided to rewire my schematic as I realized I was using the Chip version of the ESP32-S3 and not the actual module version (I chose the ESP32-S3 Mini). Both my sensor interface and power management is done. 

<img width="993" height="776" alt="image" src="https://github.com/user-attachments/assets/c7d27f3a-9e25-431a-a3e0-d09b8278279f" />
<img width="1069" height="477" alt="image" src="https://github.com/user-attachments/assets/2577eb53-1cc0-46ed-8b8c-29fd74fbe153" />

## Schematic Rewire So close - Day 6/30/26 (Hours 3-4)

I decided for a neater version so I resorted to different page sheets and made it simpler. This solved my rewiring issue entirely and made it much more simpler. Additionally, I resorted to the ESP32-S3 Mini and was able to complete a successful rewire towards the microcontroller connecting everything at once. 

<img width="850" height="807" alt="image" src="https://github.com/user-attachments/assets/6df10024-a6bf-439e-b84b-19ac6f012a18" />
<img width="822" height="405" alt="image" src="https://github.com/user-attachments/assets/b78ec270-6ca7-4f70-bac3-0b2b4c59ed3d" />
<img width="1397" height="628" alt="image" src="https://github.com/user-attachments/assets/b5b1da4e-8f59-4ae5-a1c7-1d574171fe0c" />

## Schematic Rewire - Day 6/30/26 (Hours 4-5)
To end the Schematic Rewire (finally..) I finished my OLED and Audio Interface, two important components connecting to my ESP32. The OLED will display info and will later be programmed to do so, meanwhile the Audio Interface will do the same in an audio format. 

<img width="925" height="706" alt="image" src="https://github.com/user-attachments/assets/58ebe590-3e1b-46ac-b8a0-e10366c60dbe" />
<img width="830" height="665" alt="image" src="https://github.com/user-attachments/assets/8885cc1e-0c6c-4af7-bfda-38c51fddb81e" />


## Day 6/30/26 (4hrs 48 min)

### Devlog – June 30, 2026

**Focus:** Complete Schematic Overhaul, Hierarchical Sheets, & Peripheral Integration

Massive milestone hit today. Realized a fundamental mismatch in the central microcontroller component selection and completely overhauled the schematic architecture to transition from a messy, single-page layout to a clean, production-ready multi-sheet design.

#### Accomplishments:

* **Microcontroller Core Correction (Hours 1–2):**
* Identified a critical error: the schematic originally used the raw ESP32-S3 IC (chip-down) instead of the actual integrated module (**ESP32-S3-MINI-1**).
* Swapped out the component block, completely saving the project from massive PCB routing headaches later, as the mini module integrates the flash, RAM, and antenna circuitry automatically.
* Verified that the completed Sensor Interface and Power Management blocks survived the migration.


* **Hierarchical Page Sheet Migration (Hours 3–4):**
* To solve the escalating "spaghetti wire" mess, abandoned the single-page layout and refactored the entire project into individual hierarchical page sheets.
* This modular approach completely cleared up the wiring bottlenecks and allowed for a seamless, successful master rewire back to the new ESP32-S3 Mini block using clean global labels.


* **OLED & Audio Interface Integration (Hours 4–5):**
* Finalized the schematic wiring for the dual feedback systems: the visual **OLED Display** block and the **I2S Audio Interface** block.
* Mapped out the display paths to handle future telemetry data readouts and stabilized the I2S audio channels (microphone input and amplifier output) to provide clean audio feedback down the line.



#### Project Status 6/30/26:

The schematic is officially **100% complete** and fully modularized. Every subsystem—Power, Sensors, OLED, Audio, and LEDs—is cleanly tied back to the ESP32-S3 Mini. Ready to lock it in and move to footprints!

<img width="830" height="665" alt="image" src="https://github.com/user-attachments/assets/8885cc1e-0c6c-4af7-bfda-38c51fddb81e" />
<img width="1069" height="477" alt="image" src="https://github.com/user-attachments/assets/2577eb53-1cc0-46ed-8b8c-29fd74fbe153" />

## PCB Organized - Time to Reroute! 7/3/26: (1-2 Hours)

The PCB is finally organized, it's time to reroute and make sure the chip is well done and suited. CADDING IS VERY SOON!!!
<img width="1202" height="774" alt="image" src="https://github.com/user-attachments/assets/14fcbcb0-96c0-40f7-b20c-ebf5b12b53b5" />

## Routing... 7/3/26 (2-3 hour)
It's taking a while but we're getting there. I am currently routing everything, PCB will be done by tonight.. 
<img width="1164" height="528" alt="image" src="https://github.com/user-attachments/assets/95cae7d1-e5fe-4551-b88b-c0cf5e242411" />
<img width="775" height="761" alt="image" src="https://github.com/user-attachments/assets/025e0868-9e07-4c6f-9ca2-81a403e31ce1" />

## Project Development Log: Routing Phase CompletionDate: 7/4/26 (5 hours)
I have successfully completed the routing phase for the entire printed circuit board layout.Managing the trace routing presented several structural challenges, particularly regarding the speaker interface strategy and component placement constraints. 

Despite these spatial complexities, all nets have been fully routed, and the connection matrix is complete. The board layout is clean, and the netlist is fully satisfied with zero remaining unrouted connections.The immediate next steps include performing a comprehensive Design Rule Check to verify electrical clearances, optimizing the silkscreen component designators for legibility, and generating the final copper ground pours. 

Once these verification steps are complete, the project will move into the manufacturing file generation phase.

<img width="252" height="715" alt="image" src="https://github.com/user-attachments/assets/98101731-d932-4a3a-8075-ab4e18bbcb39" />

## Routing Complete! 7/7 (Hours 1-4) 

Completed routing after reassembling 3 days ago. I was able to reroute everything with the correct net labels finally :sob: 

<img width="252" height="715" alt="image" src="https://github.com/user-attachments/assets/98101731-d932-4a3a-8075-ab4e18bbcb39" />
<img width="563" height="518" alt="image" src="https://github.com/user-attachments/assets/8eef65d9-d227-4f0e-83f3-e1ec219c3c9b" />
<img width="292" height="597" alt="image" src="https://github.com/user-attachments/assets/f123c024-9033-455a-aec6-b96e4a599f61" />

ENJOY WE MAKING HOLES NOW!!


## Holes Complete, onto CADDING! 7/7 (4-5)
<img width="627" height="650" alt="image" src="https://github.com/user-attachments/assets/3d8c44a6-004d-40eb-b242-1cb7b3e15775" />

