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
