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


## Journal Day 2 - PCB Almost Done? (Hours: 3)


Today was very productive yet exhausting. I made the big step to creating my first ever PCB -- however, a huge roadblock occured around my OLED screen, the wiring led to the 3.3v line on both components R4 and R5 opposed to the SLC and SDA Line, so I had to rewire my schematic's components all over again which took me a couple hours until I ran a successful check. Eventually, I got to my PCB and modelled how I want wazza to be -- from the USB-C to the OLED screen. 

<img width="1071" height="853" alt="image" src="https://github.com/user-attachments/assets/6b969f1c-960b-40bd-b3f9-83a89c678b7d" />
<img width="492" height="397" alt="image" src="https://github.com/user-attachments/assets/6811b899-7b8a-4f35-92b5-3d110f4a0ca5" />

Doing so made me realize I might have to rework my ESP32 as I may have used the wrong module -- though it's not much of a hard fix I just have to redesignate the pins to the correct wiring. Additionally, I NEED to add Net Lists to make my Schematic much more smoother. 

I am a bit unsure on what to do, but I will get most of this done tomorrow, and of course, jobs not finished, all thats left is to submit the CAD, then we can ship, and HOPEFULLY get it accepted. 

