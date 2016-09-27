#!/usr/bin/python
# -*- mode: python -*-
# Looks up in database for nearby srtm files.

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from viewsheds import initGrassSetup , grassViewshed , grassCommonViewpoints


# commands
unzipCmd = 'unzip -n -d {unzipDir} {files};'
url = "wget -P {geodataDir} https://dds.cr.usgs.gov/srtm/version2_1/SRTM1/Region_0{region}/{filename};"
gdalwarp = 'gdalwarp -t_srs EPSG:3857 -r cubic {filename} {gdalwarpDir}/{tifFilename};'
gdal_merge = 'gdal_merge.py -o {tilename} *.tif;'


# directories
unzipDir = '/home/justin/Documents/ucmi/geodata/zip/tempEPSG4326'
geodataDir = '/home/justin/Documents/ucmi/geodata/zip/'
gdalwarpDir = '/home/justin/Documents/ucmi/geodata/zip/tempEPSG3857'

filename = "N%02dW%03d.hgt.zip"
tilename = 'tile.tif'

radius = .7 #degrees (circle in which to look for other srtms)
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
    commandList = ''
    filenames = []
    for row in result:
        intLat = row['lat']
        intLon = row['lon']
        region = row['region']
        filenames.append(filename % (intLat , -1 *  intLon))
        # if file has not been downloaded already add to commadn list
        if filenames[-1] not in os.listdir(geodataDir):
            commandList += url.format(geodataDir = geodataDir , region = region , filename = filenames[-1])
    # Execute wget
    os.system(commandList)
    
    # unzip
    commandList = ''
    os.chdir(geodataDir)
    for name in filenames:
        commandList += unzipCmd.format(files = name , unzipDir = unzipDir)
    os.system(commandList)
    
    # convert to 3857
    commandList = ''
    os.chdir(unzipDir)
    for name in filenames:
        commandList += gdalwarp.format(filename = name[:-4] , gdalwarpDir = gdalwarpDir , tifFilename = name[:-7]+'tif' )
    os.system(commandList)
    
    # merge tiles
    os.chdir(gdalwarpDir)
    os.system(gdal_merge.format(tilename = tilename))
    
    
    #deleting files in EPSG4326 folder
    os.system('rm {0}/*'.format(unzipDir))
    
    # load file into grassgis
    initGrassSetup()

    #deleting all files in EPSG3857
    os.system('rm {0}/*'.format(gdalwarpDir))


def pointQuery(lat , lon , pointNum, firstPoint):
    if firstPoint:
        lookupSRTM(lat , lon)
    # run viewshed on point
    grassViewshed(lat ,lon , pointNum)
    
    # use mapcalc to find common viewpoints
    grassCommonViewpoints()

def main(args):
    lookupSRTM(39 , -110)
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
    
