# -*- coding: utf-8 -*-
#!/usr/bin/env python

import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image, ImageDraw, ImageFont

import subprocess
import os,sys
import struct

import spidev
import time

# pip install Adafruit_GPIO  Adafruit_SSD1306 

###################################3

# SPI channel (0 or 1)
SPI_CH = 0

# SPI speed (hz)
SPI_SPEED = 1000000

# GPIO number
PIN_LED = 17
PIN_SW  = 22
SW_ON   = 0

PIN_RS1 = 5
PIN_RS2 = 6
PIN_RS4 = 13
PIN_RS8 = 19

VOLUME_DELAY=0
VOLUME_LOSS =1
VOLUME_DUP=3
VOLUME_CORRUPT=2

####################################
# Raspberry Pi pin configuration
RST = 24

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
#disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Initialize library.
disp.begin()
 
# Clear display.
disp.clear()
disp.display()
  
 
# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
 
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
 
# Misaki Font, awesome 8x8 pixel Japanese font, can be downloaded from the following URL.
# $ wget http://www.geocities.jp/littlimi/arc/misaki/misaki_ttf_2015-04-10.zip
#font = ImageFont.truetype('/home/pi/font/misakifont/misaki_gothic.ttf', 12, encoding='unic')

# Un-comment out the following line if you want to use the default font instead of Misaki Font
font = ImageFont.load_default()

def tc_set (dev, delay, loss, dup, corrupt, rs):
    if rs == 1:
        if delay == 0:
           delay = 10
        cmd="sudo tc qdisc change dev %s root netem delay %dms loss %d%% reorder %d%% %d%% "%(dev, delay, loss, dup, corrupt)
    else:
        cmd="sudo tc qdisc change dev %s root netem delay %dms loss %d%% duplicate %d%% corrupt %d%%"%(dev, delay, loss, dup, corrupt)
    subprocess.call(cmd.split())

def tc_init (dev):
    cmd="sudo tc qdisc del dev %s root >/dev/null 2>&1"%(dev)
    subprocess.call(cmd.split())
    cmd="sudo tc qdisc add dev %s root netem delay 0ms loss 0%%"%(dev)
    subprocess.call(cmd.split())


def lcd_clear():
    # Clear display.
    disp.clear()
    disp.display()

def lcd_write (delay, loss, dup, corrupt, select, rs):
    t1="delay       %3d ms"%(delay)
    t2="loss        %3d %%"%(loss)
    t3="dup         %3d %%"%(dup)
    if rs == 0:
        t3="dup    ->   %3d %%"%(dup)
    elif rs == 1:
        t3="reorder-> i %3d %%"%(dup)
    else:
        t3="dup    ->   %3d %%"%(dup)

    if rs == 0:
        t4="corrup      %3d %%"%(corrupt)
    elif rs == 1:
        t4="reorder     %3d %%"%(corrupt)
    else:
        t4="corrup      %3d %%"%(corrupt)


    if select == 0:
        t1="delay  ->   %3d ms"%(delay)
    if select == 1:
        t2="loss   ->   %3d %%"%(loss)
        t4="corrup      %3d %%"%(corrupt)
    if select == 2:
        if rs == 0:
            t3="dup    ->   %3d %%"%(dup)
        elif rs == 1:
            t3="reorder-> i %3d %%"%(dup)
        else:
            t3="dup    ->   %3d %%"%(dup)
    if select == 3:
        if rs == 0:
            t4="corrup ->   %3d %%"%(corrupt)
        elif rs == 1:
	    t4="reorder->   %3d %%"%(corrupt)
        else:
            t4="corrup ->   %3d %%"%(corrupt)

    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)

    x=0
    y=0
    draw.text((x,y), t1, font=font,  fill=255)
    y+=16
    draw.text((x,y), t2, font=font,  fill=255)
    y+=16
    draw.text((x,y), t3, font=font,  fill=255)
    y+=16
    draw.text((x,y), t4, font=font,  fill=255)

    disp.image(image)
    disp.display()

class MCP3208:
        def __init__(self, spi_channel=0):
                self.spi_channel = spi_channel
                self.conn = spidev.SpiDev(0, spi_channel)
                self.conn.max_speed_hz = 1000000 # 1MHz

        def __del__( self ):
                self.close

        def close(self):
                if self.conn != None:
                        self.conn.close
                        self.conn = None

        def bitstring(self, n):
                s = bin(n)[2:]
                return '0'*(8-len(s)) + s

        def read(self, adc_channel=0):
                # build command
                cmd  = 128 # start bit
                cmd +=  64 # single end / diff
                if adc_channel % 2 == 1:
                        cmd += 8
                if (adc_channel/2) % 2 == 1:
                        cmd += 16
                if (adc_channel/4) % 2 == 1:
                        cmd += 32

                # send & receive data
                reply_bytes = self.conn.xfer2([cmd, 0, 0, 0])

                #
                reply_bitstring = ''.join(self.bitstring(n) for n in reply_bytes)
                # print reply_bitstring

                # see also... http://akizukidenshi.com/download/MCP3204.pdf (page.20)
                reply = reply_bitstring[5:19]
                return int(reply, 2)

def burst_mode():
    for n in range(devnum):
        tc_set( devices[n], 0, 100, 0, 0, 0)
    lcd_clear()
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.text((0,0), "burst  mode  ", font=font,  fill=255)
    disp.image(image)
    disp.display()
    GPIO.output(PIN_LED,  1 )
    while True:
        #print("burst mode")
        sw=GPIO.input( PIN_SW )
        if sw != SW_ON:
            break
        #time.sleep(1)

if __name__=="__main__":
    spi = MCP3208(SPI_CH)

    # Write two lines of text.
    x=0
    y=0
    for str in [ u'booting' ]:
        draw.text((x,y), str, font=font,  fill=255)
        y+=16

    disp.image(image)
    disp.display()

    #args = sys.argv

    devices = ["eth0", "eth1"];
    devnum  = 2;
    for dev in devices:
        tc_init(dev)
    delay =  -1 # for display out
    loss = 0
    dup  = 0
    corrupt = 0
    grs = 0
    print("GPIO.setup LED")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup( PIN_LED , GPIO.OUT )
    print("GPIO.setup SW")
    GPIO.setup( PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP )
    GPIO.setup( PIN_RS1, GPIO.IN )
    GPIO.setup( PIN_RS2, GPIO.IN )
    GPIO.setup( PIN_RS4, GPIO.IN )
    GPIO.setup( PIN_RS8, GPIO.IN )

    time.sleep(2)

    while (1):
        sw=GPIO.input( PIN_SW )
        if sw == SW_ON:
            burst_mode()
            delay = -1 # for display out
        rs1=GPIO.input( PIN_RS1 )
        rs2=GPIO.input( PIN_RS2 )
        rs4=GPIO.input( PIN_RS4 )
        rs8=GPIO.input( PIN_RS8 )

        if rs1 == 0 and rs2 == 0 and rs4 == 0 and rs8 == 0 :
            rs = 0
        if rs1 == 1 and rs2 == 0 and rs4 == 0 and rs8 == 0 :
            rs = 1
        if rs1 == 0 and rs2 == 1 and rs4 == 0 and rs8 == 0 :
            rs = 2
        if rs1 == 1 and rs2 == 1 and rs4 == 0 and rs8 == 0 :
            rs = 3
        if rs1 == 0 and rs2 == 0 and rs4 == 1 and rs8 == 0 :
            rs = 4
        if rs1 == 1 and rs2 == 0 and rs4 == 1 and rs8 == 0 :
            rs = 5
        if rs1 == 0 and rs2 == 1 and rs4 == 1 and rs8 == 0 :
            rs = 6
        if rs1 == 1 and rs2 == 1 and rs4 == 1 and rs8 == 0 :
            rs = 7
        if rs1 == 0 and rs2 == 0 and rs4 == 0 and rs8 == 1 :
            rs = 8
        if rs1 == 1 and rs2 == 0 and rs4 == 0 and rs8 == 1 :
            rs = 9
        #print("RW")
        #print(rs)

        d = 0
        l = 0
        p = 0
        c = 0

        #print("delay >>")
        d = spi.read(VOLUME_DELAY)
        d = round(++d / 2)
        if d < 3:
            d = 0
        #print( d )

        l = spi.read(VOLUME_LOSS)
        l = round(++l / 2 / 20.47)
        if l < 3:
            l=0
        if l >= 98:
            l = 100
        #print( l )

        p = spi.read(VOLUME_DUP)
        p = round(++p / 2 / 20.47)
        if p <= 2:
            p = 0
        if p >= 98:
            p = 100
        #print( p )

        c = spi.read(VOLUME_CORRUPT)
        c = round(++c / 2 / 20.47)
        if c <= 2:
            c = 0
        if c >= 98:
            c = 100
        #print( c )

        if (d != delay):
           gselect = 0
        if (l != loss):
           gselect = 1
        if (p != dup):
           gselect = 2
        if (c != corrupt):
           gselect = 3

        if (d != delay or l != loss or p != dup or c != corrupt or rs != grs):
            delay = d
            loss = l
            dup = p
            corrupt = c
            grs = rs
            for n in range(devnum):
                tc_set(devices[n], delay, loss, dup, corrupt, grs)
            lcd_clear()
            lcd_write (delay, loss, dup, corrupt, gselect, grs)
        if delay != 0 or loss != 0 or dup != 0 or corrupt != 0:
            GPIO.output(PIN_LED,  1 )
        else:
            GPIO.output(PIN_LED,  0 )

        #time.sleep(1)


