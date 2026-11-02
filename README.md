# 6-DOF Gesture-Controlled Robotic Hand
Real-time 6-DOF gesture-controlled robotic hand using OpenCV (Python) and ESP32 (C) via USB serial communication. 1st Place Winner at Dr. RMLAU University Project Competition.

## 📌 Technical Overview
* **Hardware:** ESP32 Microcontroller, 6x Servo Motors, Robotic Hand Chassis
* **Software (Laptop):** Python, OpenCV (Custom image processing and contour/gesture tracking)
* **Software (Microcontroller):** C (Arduino IDE compatible), ESP32Servo library
* **Communication:** Wired Serial Communication via USB Cable (Baud rate: 115200)

## ⚙️ How It Works
1. **Vision Processing:** The laptop webcam captures hand movements in real-time. A Python script processes the frames using OpenCV algorithms (such as thresholding and contour analysis) to calculate positional coordinates or finger states.
2. **Serial Transmission:** The calculated angle values are streamed continuously over the **USB serial cable** to the ESP32.
3. **Execution:** The ESP32 parses the incoming C-style data buffer, applies safety constraints, and smoothly drives the 6 servo motors to mirror the hand gestures instantly.

## 📁 Code Structure
* `python hand.py` – Real-time OpenCV vision tracking script
* `Ccode2handesp.c.ino` – ESP32 firmware for driving 6 servo motors
  
## 🏆 Achievements
* **1st Place Winner** – University Project Competition, Dr. RMLAU Ayodhya.

