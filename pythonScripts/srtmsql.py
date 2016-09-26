#!/usr/bin/python
# -*- mode: python -*-
# Looks up in database for nearby srtm files.

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

url = "wget -P {geodataDir} https://dds.cr.usgs.gov/srtm/version2_1/SRTM1/Region_0{region}/{filename}"
filename = "N%02dW%03d.hgt.zip"
geodataDir = '/home/justin/Documents/ucmi/geodata/zip'
radius = 3.7 #degrees (circle in which to look for other srtms
SRID = 4326
query = """
        SELECT lat , lon , region FROM srtm
                WHERE 
        ST_DWithin(geom,
        ST_SetSRID(ST_MakePoint({lon},{lat}) , {SRID}),{radius});
        """




#class Users(Base):
 #   __table__ = Base.metadata.tables['srtm']

# Queries databse for nearby lat , lon SRTMs
def lookupSRTM(lat , lon):
    # connect to database
    engine = create_engine("postgresql://justin:bobo24@localhost/gisdb", convert_unicode=True, echo=False)
    connection = engine.connect()
    Base = declarative_base()
    Base.metadata.reflect(engine)
    
    #query
    result = connection.execute(query.format(lon = lon , lat = lat , SRID = SRID , radius = radius))
    
    # if file not downloaded, then downloaded it
    for row in result:
        intLat = row['lat']
        intLon = row['lon']
        region = row['region']
        if not isDownloaded( lat ,-1 *lon):
            os.system(url.format(geodataDir = geodataDir , region = region , filename = filename % (lat , -1 *  lon)))


# checks if file has alread been downloaded
def isDownloaded(lat , lon):
    return filename % (lat , lon) in os.listdir(geodataDir)


if __name__ == '__main__':
    print lookupSRTM(41 , -105)
    

