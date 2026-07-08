# Wazza - Magic in The Air

## Project Overview

Stardance is a gesture-controlled AI wand that responds to hand motions in the air. By waving the wand with specific gestures, users trigger real-time API calls to AI Agents, enabling voice and motion-based interaction with large language models. The wand combines hardware gesture recognition with cloud AI to create an intuitive, futuristic interface for accessing AI capabilities on the fly.

## How It Works

The wand is held in the user's hand and moved through the air to perform gestures. An accelerometer and gyroscope sensor inside the wand detect the motion patterns in real time. When the ESP32 microcontroller recognizes a gesture (like a swipe, circle, or tap), it sends a query to the Claude API. Claude responds with text or audio, which is played through a built-in speaker. LEDs on the wand provide visual feedback for recognized gestures and incoming responses. An optional built-in microphone allows users to speak commands directly to the wand as well.

## Hardware Architecture

### Microcontroller: ESP32-S3 WROOM

The brain of the wand is an ESP32-S3 WROOM, a dual-core processor running at 240MHz with integrated WiFi and Bluetooth connectivity. It features 8MB of PSRAM for real-time gesture processing and 4MB of internal flash for code storage. The chip handles sensor data collection, gesture recognition algorithms, API communication, and peripheral control all simultaneously.

### Power Management: 18650 LiPo Battery and TP4056 Charger

An 18650 lithium polymer battery cell provides 3.7V nominal power to the entire system. The battery is charged via a TP4056 USB-C charging module, which handles all protection, current limiting, and charging termination automatically. A 100 microfarad bypass capacitor on the 3.3V rail filters noise and stabilizes the power supply for sensitive analog components.

### Motion Sensing: MPU-6050 6-Axis IMU

The MPU-6050 inertial measurement unit contains a three-axis accelerometer and three-axis gyroscope. These sensors measure linear acceleration and rotational velocity, allowing the ESP32 to detect complex hand movements. The sensor communicates with the microcontroller over I2C at 400kHz clock speed with 4.7k ohm pull-up resistors on both the data and clock lines. The sensor is addressable at I2C address 0x68.

### User Input: Tactile Button

A momentary push button on the wand allows the user to manually trigger actions without gestures. The button connects to GPIO25 and uses a 10k ohm pull-down resistor, making it active-low logic. When pressed, it creates a clear interrupt that the firmware can use to immediately stop playback, reset state, or trigger an emergency action.

### Visual Feedback: WS2812B LED Strip

An addressable LED strip with twenty WS2812B RGB LEDs wraps around the wand shaft. These LEDs communicate with the ESP32 via a single GPIO16 data line and can be individually controlled in real time. The LEDs indicate gesture recognition status, provide visual feedback while listening or processing, and display playback status during audio responses.

### Audio Output: MAX98357A Amplifier and Speaker

A MAX98357A Class D audio amplifier receives I2S digital audio from the ESP32 and drives a 2-watt speaker. The amplifier operates at 3.3V and communicates with the microcontroller on the I2S bus using a bit clock, left-right clock, and data-in line. This allows high-quality audio streaming of Claude's responses in real time.

### Audio Input: SPH0645 MEMS Microphone

An SPH0645 MEMS microphone captures ambient sound for voice command input. The microphone outputs a PDM digital signal at 64kHz sample rate, which the ESP32 can decode in real time. The microphone shares the I2S bus clock lines with the amplifier, requiring only an additional data-out line to the microcontroller.

## Software Architecture

### Gesture Recognition Engine

The firmware running on the ESP32 continuously reads raw accelerometer and gyroscope data from the MPU-6050 at high frequency. These readings are buffered and compared against a library of known gesture templates using pattern matching algorithms. When a gesture matches a template with sufficient confidence, an interrupt is triggered to initiate an API call.

### Cloud API Integration

Upon gesture recognition, the ESP32 connects to the Claude API over WiFi using HTTPS. It sends the recognized gesture type as context to Claude, which generates a contextually appropriate response. The response is streamed back to the wand and immediately sent to the audio codec for playback without requiring the entire response to download first.

### Real-Time Audio Synthesis

The firmware decodes incoming audio from the API and streams it directly to the I2S amplifier. This creates a low-latency experience where users hear Claude's response within seconds of making a gesture. The LED strip animates in sync with audio playback to provide additional visual feedback.

## Electrical Specifications

The entire system operates on 3.3V nominal voltage derived from the battery via the TP4056 charger module. The ESP32 consumes approximately 80 milliamps during active WiFi communication and 20 milliamps during idle listening. The amplifier consumes up to 500 milliamps during maximum volume playback. The microphone and motion sensor consume minimal power, typically under 20 milliamps combined. Total system power draw during normal operation is estimated at 200 to 300 milliamps, allowing several hours of continuous use per charge.

## Firmware Stack

The firmware is written in C++ using the Arduino framework and PlatformIO build system. Core libraries include the I2C driver for sensor communication, the I2S driver for audio streaming, WiFi connectivity libraries, and the Adafruit NeoPixel library for LED control. Gesture recognition uses a simple template-matching algorithm that compares incoming sensor data against pre-recorded gesture vectors.

## PCB Design

The circuit is organized into five functional modules: power management, microcontroller core, sensor interfaces, audio input/output, and connectivity. The PCB layout prioritizes short trace lengths for I2C and I2S buses to minimize noise and signal integrity issues. Power and ground planes provide low-impedance distribution of 3.3V and ground across all components. The design uses a two-layer PCB with surface-mount and through-hole components as needed for hand assembly.

## Enclosure and Mechanical Design

The wand enclosure is 3D printed from PLA or resin filament and designed to fit comfortably in the user's hand. The cylindrical shaft is 22 millimeters in diameter and approximately 80 millimeters long. The battery cell runs lengthwise down the center of the wand for balance. Other components are clustered in the grip area. The LED strip is mounted helically around the shaft for maximum visibility. The enclosure is finished with matte black paint and sanded smooth for a professional appearance.

## Schematic

<img width="711" height="301" alt="image" src="https://github.com/user-attachments/assets/1569244d-4e65-4fde-bfbe-05a0b9a3806f" />
<img width="802" height="427" alt="image" src="https://github.com/user-attachments/assets/81efa213-27a1-4943-a675-421c33ea0701" />
<img width="796" height="388" alt="image" src="https://github.com/user-attachments/assets/4ec49725-35b1-42b0-aa20-bc468c357368" />
<img width="586" height="562" alt="image" src="https://github.com/user-attachments/assets/37beaafb-b1b7-489d-b6e5-dee7d2ad6386" />
<img width="402" height="288" alt="image" src="https://github.com/user-attachments/assets/c82b7383-9072-4c87-ab0c-248d76ed9dbc" />
<img width="743" height="483" alt="image" src="https://github.com/user-attachments/assets/945cc301-dc71-436d-98f5-64e68c29ae68" />



## Future Enhancements

Potential improvements include on-device machine learning for gesture recognition to reduce API latency, integration with additional sensors like IMUs or proximity detectors, wireless charging capability, and support for custom gesture training. The modular design allows for easy hardware upgrades without redesigning the entire system.

## Files and Documentation

The project includes complete KiCAD schematic files organized by functional module, PCB layout files for fabrication, Arduino firmware source code with gesture templates, and assembly instructions with wiring diagrams. All code is open source and available for modification and redistribution.

<img width="252" height="715" alt="image" src="https://github.com/user-attachments/assets/2cc7b468-cb41-48ba-ac2d-ff27166d215c" />
<img width="563" height="518" alt="image" src="https://github.com/user-attachments/assets/8eef65d9-d227-4f0e-83f3-e1ec219c3c9b" />
<img width="1037" height="531" alt="image" src="https://github.com/user-attachments/assets/d108678b-4a3c-4225-8fda-f0c08227013a" />
<img width="1101" height="811" alt="image" src="https://github.com/user-attachments/assets/0a3cba86-37cb-4c0e-9bea-73647cb562b8" />

