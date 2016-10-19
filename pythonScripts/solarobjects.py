#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  solarObjects.py
# 
#  Returns information about the sun and moon

activate_this_file = "venv/bin/activate_this.py"
execfile(activate_this_file, dict(__file__ = activate_this_file))

import time , ephem , math , configparser , os , inspect

config = configparser.ConfigParser()
config.read('config.ini')
this_file = os.path.split(inspect.getfile(inspect.currentframe()))[-1]
options = config._sections[this_file]

# Generates a point given an initial point and bearing
# http://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
def pointAlongBrng(position , brng):
    lat1 , lon1 = position
    # brng is in radians
    R = 6378.1 #Radius of the Earth
    d = config.getfloat(this_file, "distance") #Distance in km



    lat1 = math.radians(lat1) #Current lat point converted to radians
    lon1 = math.radians(lon1) #Current long point converted to radians

    lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +
         math.cos(lat1)*math.sin(d/R)*math.cos(brng))

    lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),
                 math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

    return math.degrees(lat2) , math.degrees(lon2)


# generates two positions along a bearing-- in both positive and negative directions
def brngLine(position , brng):
    lat1 , lon1 = pointAlongBrng(position , brng)
    lat2 , lon2 = pointAlongBrng(position , brng + math.pi)
    return lat1 , lon1, lat2, lon2


# Returns boolean whether sun or moon is visible at given time and position
def isObjVisible(solarObject , latlon ):
    decimal2angle = lambda x : ephem.degrees(str(x))
    lat = decimal2angle(latlon[0])
    lon = decimal2angle(latlon[1])
    if solarObject == 'Sun':
        obj = ephem.Sun()
    elif solarObject == 'Moon':
        obj = ephem.Moon()
        
    assert(solarObject in ('Sun' , 'Moon')) , 'solarObject is neither Sun nor Moon, but something else.'
    
    lostPerson = ephem.Observer()
    lostPerson.lon = lon
    lostPerson.lat = lat
    
    obj.compute(lostPerson)
    alt = float(repr(obj.alt))
    az = float(repr(obj.az))
    assert(type(alt) == type(0.00))
    
    risen = alt > 0
    return  risen , az

def main(args):

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
