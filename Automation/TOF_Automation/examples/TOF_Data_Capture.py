#! /usr/bin/python

from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *
import o3d3xx
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pypcd
import pdb
from datetime import datetime
import tzlocal


imageWidth = 352
imageHeight = 264

num = imageWidth * imageHeight


class GrabO3D300():
    def __init__(self,data):
        self.data = data
        self.X = np.zeros(num)
        self.Y = np.zeros(num)
        self.Z = np.zeros(num)
        self.Amplitude = np.zeros((imageHeight,imageWidth))
        self.Distance = np.zeros((imageHeight,imageWidth))


    def readNextFrame(self):
        result = self.data.readNextFrame()

        self.Amplitude = np.frombuffer(result['amplitude'],dtype='uint16')
        self.Amplitude = self.Amplitude.reshape(imageHeight,imageWidth)
        self.Distance = np.frombuffer(result['distance'],dtype='uint16')
        self.Distance = self.Distance.reshape(imageHeight,imageWidth)
        self.illuTemp = 20.0
        
        # page 23 of manual, 
        # xyz data is 16-bit signed ints
        # [mm]
        self.X = np.frombuffer(result['x'], dtype='int16')
        self.Y = np.frombuffer(result['y'], dtype='int16')
        self.Z = np.frombuffer(result['z'], dtype='int16')
        self.L = [self.X,self.Y,self.Z]
        self.L = np.transpose(self.L)

        self.pc = pypcd.make_xyz_point_cloud(self.L)
       
        # IF YOU HAVE SET UP NTP SYNCING ON THE ToF camera, then the
        # framegrabber will return the synced unix epoch time. so convert it
        # back to UTC and bamarooni you got time
        #
        # if you encounter a "year is out of range" error the timestamp
        # may be in milliseconds, try `ts /= 1000` in that case
        unix_timestamp = result['timeStamp']
        
        # get the local timezone
        local_timezone = tzlocal.get_localzone()
        local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)

        fmt = '%Y_%m_%d_%H_%M_%S.%f'
        timestampTOF = local_time.strftime(fmt)

        return self.pc, timestampTOF


def updatefig(*args):
    g = args[1]
    g.readNextFrame(args[4]);
    imAmp = args[2]
    amp_max = float(max(np.max(g.Amplitude),1));
    imAmp.set_array(g.Amplitude/ amp_max)


    imDist = args[3]
    dist_max = float(max(np.max(g.Distance),1));
    imDist.set_array(g.Distance/ dist_max)
    
    return imAmp,imDist,
       

def main():
    address = '169.254.145.24'

    camData = o3d3xx.ImageClient(address, 50010)
    grabber = GrabO3D300(camData)

    frameCount = 100
    pointCloudStorage = []
    timeStamps = []
    for x in range(0, frameCount):
        (pc, timeStamp) = grabber.readNextFrame()
    	pointCloudStorage.append(pc)
        timeStamps.append(timeStamp)
        print(timeStamp)

    #This format of directory is necessary to communicate with MATLAB
    fileDirectory = '/home/vantage/Documents/githere/VANTAGE/Data/TOF_Automated/pointcloud_'
    for pc, timeStamp in zip(pointCloudStorage, timeStamps):
        pypcd.save_point_cloud(pc, fileDirectory + str(timeStamp) + ".pcd")


if __name__ == '__main__':
    main()

