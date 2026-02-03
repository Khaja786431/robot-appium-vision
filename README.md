# Robot Appium Vision Library

Advanced Robot Framework keyword library for Appium automation with:
- OCR-based text detection
- Image-based verification and clicking
- Coordinate tapping
- Safe scroll & swipe
- Android shell commands
- Screen recording with video embedding

## Installation

pip install robot-appium-vision


## Installation

*** Settings ***
Library    AppiumKeywords

*** Test Cases ***
Verify Text
    Verify Text Appium Full    Settings    Phone

## OCR Setup (Windows)
set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe


## Dependencies
- Appium Server
- Android device / emulator
- OpenCV
- Tesseract OCR