#!/bin/bash
# variables
echo "Initializing SocketCAN...."
BITRATE=125000
CHANNEL="can0"
echo "Bringing the driver down if Up"
sudo -S ip link set down $CHANNEL

#echo "Unloading all the kernel modules if on"
#sudo modprobe -r can_bcm
#sudo modprobe -r systec_can
#sudo modprobe -r can_raw
#sudo modprobe -r can
#sudo modprobe -r can_dev

# SocketCAN script
echo "CAN hardware OS drivers and config for" $CHANNEL
sudo -S modprobe can
sudo -S modprobe systec_can
sudo -S modprobe can-dev
sudo -S modprobe can-raw
sudo -S modprobe can-bcm
sudo -S modprobe kvaser-usb
sudo -S lsmod | grep can

echo "Configuring the SocketCAN interface to bitrate of" $BITRATE
sudo -S ip link set $CHANNEL type can bitrate $BITRATE

echo "Bringing the driver  up"
sudo -S ip link set up $CHANNEL
ifconfig $CHANNEL
