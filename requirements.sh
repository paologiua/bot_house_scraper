#!/bin/bash

sudo apt-get remove chromium-browser
sudo apt-get remove chromium
sudo apt-get autoremove
sudo apt-get clean

sudo apt-get install chromium-driver
sudo apt-get install tesseract-ocr

sudo apt-get install libatlas-base-dev 
sudo apt-get install libjasper-dev 
sudo apt-get install libqtgui4 
sudo apt-get install python3-pyqt5 
sudo apt install libqt4-test

pip install pyTelegramBotAPI
pip install selenium

pip install opencv-python
pip install pytesseract
