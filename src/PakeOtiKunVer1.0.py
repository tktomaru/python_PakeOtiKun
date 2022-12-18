# -*- coding: utf-8 -*-
#!/usr/bin/env python

import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
#import Adafruit_SSD1306
import ST7789
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

SPI_SS_AD = 7
SPI_SS_LCD = 8

# SPI speed (hz)
SPI_SPEED = 4000000

# GPIO number
PIN_LED = 17
PIN_SW  = 26
SW_ON   = 0

PIN_RS1 = 12
PIN_RS2 = 6
PIN_RS4 = 5
PIN_RS8 = 0

VOLUME_DELAY=7
VOLUME_LOSS =6
VOLUME_DUP=5
VOLUME_CORRUPT=4
VOLUME_REORDER1=3
VOLUME_REORDER2=2

####################################
before_delay = 0

####################################
# Raspberry Pi pin configuration
RST = 24
spi0 = SPI.SpiDev( 1, 2, max_speed_hz=SPI_SPEED)
spi0.set_mode(2)
#disp = Adafruit_SSD1306.SSD1306_128_64(rst=13, dc=25, spi=spi0)
#disp = ST7789.ST7789( 1,2, rst=13, dc=19)
disp = ST7789.ST7789( spi=spi0,mode=2, dc=19, rst=13)

# Initialize library.
disp.begin()
 
# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
 
draw = ImageDraw.Draw(image)

# Misaki Font, awesome 8x8 pixel Japanese font, can be downloaded from the following URL.
# $ wget http://www.geocities.jp/littlimi/arc/misaki/misaki_ttf_2015-04-10.zip
#font = ImageFont.truetype('/home/pi/font/misakifont/misaki_gothic.ttf', 12, encoding='unic')

# Un-comment out the following line if you want to use the default font instead of Misaki Font
font = ImageFont.load_default()

def tc_set (dev, delay, loss, dup, corrupt, reorder1, reorder2, rs):
    if rs == 1:
        if delay == 0:
           delay = 1
        cmd="sudo tc qdisc change dev %s root netem delay %dms loss %d%% reorder %d%% %d%% "%(dev, delay, loss, dup, corrupt)
    else:
        if delay == 0 and (reorder1 != 0 or reorder2 != 0):
            delay = 1
        cmd="sudo tc qdisc change dev %s root netem delay %dms loss %d%% duplicate %d%% corrupt %d%% reorder %d%% %d%%"%(dev, delay, loss, dup, corrupt, reorder1, reorder2)
    subprocess.call(cmd.split())

def tc_init (dev):
    cmd="sudo tc qdisc del dev %s root >/dev/null 2>&1"%(dev)
    subprocess.call(cmd.split())
    cmd="sudo tc qdisc add dev %s root netem delay 0ms loss 0%%"%(dev)
    subprocess.call(cmd.split())


def lcd_clear():
    # Clear display.
    #GPIO.output( SPI_SS_LCD, GPIO.LOW) 
    # disp.clear()
    #disp.display()
    #GPIO.output( SPI_SS_LCD, GPIO.HIGH) 
    pass

def lcd_write (delay, loss, dup, corrupt, select, reorder1, reorder2, rs):
    t1="delay %3d ms %3d %%"%(delay, reorder1)
    t2="loss  %3d %%  %3d %%"%(loss, reorder2)
    if rs == 0:
        t3="dup     %3d %%"%(dup)
    elif rs == 1:
        t3="reorder %3d %%"%(dup)
    else:
        t3="dup     %3d %%"%(dup)

    if rs == 0:
        t4="corrup  %3d %%"%(corrupt)
    elif rs == 1:
        t4="reorder %3d %%"%(corrupt)
    else:
        t4="corrup  %3d %%"%(corrupt)


    if select == 0:
        t1="delay %3d ms %3d %%"%(delay, reorder1)
    if select == 1:
        t2="loss  %3d %%  %3d %%"%(loss, reorder2)
    if select == 2:
        if rs == 0:
            t3="dup     %3d %%"%(dup)
        elif rs == 1:
            t3="reorder %3d %%"%(dup)
        else:
            t3="dup     %3d %%"%(dup)
    if select == 3:
        if rs == 0:
            t4="corrup  %3d %%"%(corrupt)
        elif rs == 1:
            t4="reorder %3d %%"%(corrupt)
        else:
            t4="corrup  %3d %%"%(corrupt)

    #GPIO.output( SPI_SS_LCD, GPIO.LOW) 
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

    #disp.image(image)
    disp.display(image)
    #GPIO.output( SPI_SS_LCD, GPIO.HIGH) 

class MCP3208:
        def __init__(self, spi_channel=0):
                self.spi_channel = spi_channel
                self.conn = SPI.SpiDev(0, spi_channel, SPI_SPEED)
                self.conn.set_mode(0)
                self.conn.set_bit_order(SPI.MSBFIRST)
                #self.conn.max_speed_hz = SPI_SPEED # 1MHz

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
                cmd += ((adc_channel & 0x07) << 3)
                #if adc_channel % 2 == 1:
                #        cmd += 8
                #if (adc_channel/2) % 2 == 1:
                #        cmd += 16
                #if (adc_channel/4) % 2 == 1:
                #        cmd += 32

                # send & receive data
                #reply_bytes = self.conn.xfer2([cmd, 0, 0, 0])
                reply_bytes = self.conn.transfer([cmd, 0, 0, 0])

                #
                reply_bitstring = ''.join(self.bitstring(n) for n in reply_bytes)
                # print reply_bitstring

                # see also... http://akizukidenshi.com/download/MCP3204.pdf (page.20)
                #reply = reply_bitstring[5:19]
                #return int(reply, 2)
                reply = (reply_bytes[0] & 0x01) << 11
                reply |= reply_bytes[1] << 3
                reply |= reply_bytes[2] >> 5
                return (reply & 0x0FFF)

def RS_Analysis( rs1, rs2, rs4, rs8 ):
        rs = 0
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
        return rs

def hosei100( l ):
        l = round(++l / 2 / 20.47)
        if l < 3:
            l=0
        if l >= 98:
            l = 100
        return l

def hosei2000( l ):
        global before_delay
        l = round(++l / 2.048 ) # 4096
        # if ( l >= 3 and ((before_delay - 10) <= l) and (l <= (before_delay + 10 ))):
        # l = before_delay
        # else:
        #     before_delay = l
        if l < 3:
            l=0
        if l >= 1990:
            l=2000
        return l

def hosei2048( l ):
        l = round(++l / 2 )
        if l < 3:
            l=0
        return l

def burst_mode():
    for n in range(devnum):
        tc_set( devices[n], 0, 100, 0, 0, 0, 0, 0)
    lcd_clear()
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.text((0,0), "burst  mode  ", font=font,  fill=255)
    #disp.image(image)
    disp.display(image)
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

    # rotate 180
    disp.command(0xa0)
    disp.command(0xc0)

    devices = ["eth0", "eth1"];
    devnum  = 2;
    for dev in devices:
        tc_init(dev)
    delay =  -1 # for display out
    loss = 0
    dup  = 0
    corrupt = 0
    grs = 0
    reorder1 = 0
    reorder2 = 0
    print("GPIO.setup LED")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup( PIN_LED , GPIO.OUT )
    print("GPIO.setup SW")
    GPIO.setup( PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP )
    GPIO.setup( PIN_RS1, GPIO.IN )
    GPIO.setup( PIN_RS2, GPIO.IN )
    GPIO.setup( PIN_RS4, GPIO.IN )
    GPIO.setup( PIN_RS8, GPIO.IN )

    #time.sleep(2)

    while (1):
        sw=GPIO.input( PIN_SW )
        if sw == SW_ON:
            burst_mode()
            delay = -1 # for display out
        rs1=GPIO.input( PIN_RS1 )
        rs2=GPIO.input( PIN_RS2 )
        rs4=GPIO.input( PIN_RS4 )
        rs8=GPIO.input( PIN_RS8 )

        rs = RS_Analysis( rs1, rs2, rs4, rs8 )
        #print(rs)

        #print("delay >>")

        d = hosei2000( spi.read(VOLUME_DELAY)  )
        l = hosei100( spi.read(VOLUME_LOSS) )
        c = hosei100( spi.read(VOLUME_CORRUPT) )
        p = hosei100( spi.read(VOLUME_DUP) )
        r1 = hosei100( spi.read(VOLUME_REORDER1) )
        r2 = hosei100( spi.read(VOLUME_REORDER2) )

        if (d != delay):
           gselect = 0
        if (l != loss):
           gselect = 1
        if (p != dup):
           gselect = 2
        if (c != corrupt):
           gselect = 3

        if (d != delay or l != loss or p != dup or c != corrupt or r1 != reorder1 or r2 != reorder2 or rs != grs):
            delay = d
            loss = l
            dup = p
            corrupt = c
            grs = rs
            reorder1 = r1
            reorder2 = r2

            print( "delay %3d %%"%(delay) )
            print( "loss %3d %%"%(loss))
            print( "dup %3d %%"%(dup))
            print( "corrupt %3d %%"%(corrupt))
            print( "reorder1 %3d %%"%(reorder1))
            print( "reorder2 %3d %%"%(reorder2))
            print( "rs %3d %%"%(grs))

            for n in range(devnum):
                tc_set(devices[n], delay, loss, dup, corrupt, reorder1, reorder2, grs)
            lcd_clear()
            lcd_write (delay, loss, dup, corrupt, gselect, reorder1, reorder2, grs)
        if delay != 0 or loss != 0 or dup != 0 or corrupt != 0 or reorder1 != 0 or reorder2 != 0:
            GPIO.output(PIN_LED,  1 )
        else:
            GPIO.output(PIN_LED,  0 )

       # time.sleep(2)


