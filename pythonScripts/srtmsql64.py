#!/usr/bin/python
# -*- mode: python -*-
# Looks up in database for nearby srtm files.

import os
import psycopg2
from viewsheds64 import initGrassSetup , grassViewshed , grassCommonViewpoints


# commands
unzipCmd = 'unzip -n -d {unzipDir} {files};'
url = "wget -P {geodataDir} https://dds.cr.usgs.gov/srtm/version2_1/SRTM1/Region_0{region}/{filename};"
gdalwarp = 'gdalwarp -t_srs EPSG:3857 -r cubic {filename} {gdalwarpDir}/{tifFilename};'
gdal_merge = 'gdal_merge.py -o {tilename} {directory}*.tif;'


# directories
geodataDir = '../geodata/cached_dems/'
user_temp_dir = '../geodata/user_temp/'

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



# Queries databse for nearby lat , lon SRTMs
def lookupSRTM(lat , lon , userid):
    # Makes directories if it doesn't already exist
    def makeDir(path):
        if not os.path.isdir(path):
            os.mkdir(path)
    # set up directories for user
    makeDir(user_temp_dir + userid)
    unzipDir = user_temp_dir + userid + '/tempEPSG4326/'
    gdalwarpDir = user_temp_dir + userid + '/tempEPSG3857/'
    makeDir(gdalwarpDir)
    makeDir(unzipDir)

    # connect to database"dbname=test user=postgres password=secret"
    conn = psycopg2.connect("dbname=gisdb user=justin password=bobo24")
    
    # Open a cursor to perform database operations
    cur = conn.cursor()
        
    #query
    cur.execute(query.format(lon = lon , lat = lat , SRID = SRID , radius = radius))
    result = cur.fetchall()
    
    # if file not downloaded, then downloaded it
    commandList = ''
    filenames = []
    for row in result:
        intLat = row[0]
        intLon = row[1]
        region = row[2]
        filenames.append(filename % (intLat , -1 *  intLon))
        # if file has not been downloaded already add to commadn list
        if filenames[-1] not in os.listdir(geodataDir):
            commandList += url.format(geodataDir = geodataDir , region = region , filename = filenames[-1])
    # Execute wget
    os.system(commandList)
    
    # unzip
    print "unzipping...."
    commandList = ''
    for name in filenames:
        commandList += unzipCmd.format(files = geodataDir + name , unzipDir = unzipDir)
    os.system(commandList)
    
    # convert to 3857
    print "converting to EPSG:3857...."
    commandList = ''
    for name in filenames:
        commandList += gdalwarp.format(filename = unzipDir + name[:-4] , gdalwarpDir = gdalwarpDir , tifFilename =  name[:-7]+'tif' )
    os.system(commandList)
    
    # merge tiles
    print "merging tiles"
    os.system(gdal_merge.format(tilename = gdalwarpDir + tilename , directory = gdalwarpDir))


    
    #deleting files in EPSG4326 folder
    os.system('rm {0}/*'.format(unzipDir))
    # load file into grassgis
    # order is in this way, so final merget tiled is deleted last
    initGrassSetup(gdalwarpDir)
    #deleting all files in EPSG3857
    os.system('rm {0}/*'.format(gdalwarpDir))


def pointQuery(lat , lon , pointNum, firstMarker , viewNum , greaterthan , altitude , userid):
    if firstMarker:
        lookupSRTM(lat , lon , userid)
    # run viewshed on point
    grassViewshed(lat ,lon , pointNum)
    # use mapcalc to find common viewpoints
    grassCommonViewpoints(viewNum , greaterthan , altitude , userid)



def main(args):
    lookupSRTM(39 , -110)
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
    

