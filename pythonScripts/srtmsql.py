#!/usr/bin/python
# -*- mode: python -*-
'''
Looks up in database for nearby srtm files. Downloads if necessary and 
then processes them with GDAL
'''

import os , shutil , psycopg2 , configparser , inspect
from viewsheds import initGrassSetup , grassViewshed , grassCommonViewpoints
from subprocess import call
from pyproj import Proj, transform

config = configparser.ConfigParser()
config.read('../config.ini')
this_file = os.path.split(inspect.getfile(inspect.currentframe()))[-1]
options = config._sections[this_file]
options_ucmi = config._sections['ucmi.py']
options_viewsheds = config._sections['viewsheds.py']



# commands
unzipCmd = 'unzip -n -d {unzipDir} {files};'
url = "wget -P {geodataDir} https://dds.cr.usgs.gov/srtm/version2_1/SRTM1/Region_0{region}/{filename};"
gdalwarp = 'gdalwarp -overwrite -t_srs EPSG:3857 -r cubic {filename} {gdalwarpDir}/{tifFilename};'
gdal_merge = 'gdal_merge.py -o {tilename} {directory}*.tif;'


# directories
geodataDir = options['geodatadir']
user_temp_dir = options['user_temp_dir']
userFolder = '/'.join(['..' , options_ucmi['viewsheddir'] , '{0}']) + '/'
userDemDir = userFolder + options_ucmi['demdir'] + '/'

filename = "N%02dW%03d.hgt.zip"
tilename = 'x{0}.tif'.format(options_viewsheds['demname'])

radius = config.getfloat(this_file, "radius") #degrees (circle in which to look for other srtms)
query = """
        SELECT lat , lon , region FROM srtm
                WHERE 
        ST_DWithin(geom,
        ST_SetSRID(ST_MakePoint({lon},{lat}) , 4326),{radius});
        """



# Queries databse for nearby lat , lon SRTMs
def lookupSRTM(lat , lon , userid):
    # Makes directories if it doesn't already exist
    def makeDir(path):
        if not os.path.isdir(path):
            os.mkdir(path)
    # set up directories for user
    makeDir(user_temp_dir + userid)
    unzipDir = '/'.join([user_temp_dir , userid , options['tempepsg4326']]) + '/'
    gdalwarpDir = '/'.join([user_temp_dir , userid , options['tempepsg3857']]) + '/'
    makeDir(gdalwarpDir)
    makeDir(unzipDir)

    # connect to database"dbname=test user=postgres password=secret"
    conn = psycopg2.connect("dbname={0} user={1} password={2}".format(options['dbname'] , options['user'] , options['password']))
    
    # Open a cursor to perform database operations
    cur = conn.cursor()
        
    #query
    cur.execute(query.format(lon = lon , lat = lat , radius = radius))
    result = cur.fetchall()
    if result == []:
        print "No maps found"
        return False
    else:
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
        # delete tile first
        os.system("rm -f " + userDemDir.format(userid) + tilename)
        # merge tiles
        print "merging tiles"
        os.system(gdal_merge.format(tilename = userDemDir.format(userid) + tilename , directory = gdalwarpDir))
        
        print "Crop tiles to smaller area"
        # -te xmin ymin xmax ymax
        # The extent should be 25 km from initial point
        # Convert from 4326 to 3857
        padding = 25000
        inProj = Proj(init='epsg:4326')
        outProj = Proj(init='epsg:3857')
        x , y = transform(inProj,outProj, lon , lat)
        ymax = y + padding
        ymin = y - padding
        xmax = x + padding
        xmin = x - padding
        extent = "{xmin} {ymin} {xmax} {ymax}".format(ymax = ymax, ymin = ymin, xmax = xmax , xmin = xmin)
        cmd = 'gdalwarp -overwrite -t_srs EPSG:3857 -te {0} {1} {2}'.format(extent,userDemDir.format(userid) + tilename, userDemDir.format(userid) + tilename[1:])
        print cmd

        os.system(cmd)
        
        #deleting files in EPSG4326 folder
        os.system('rm {0}/*'.format(unzipDir))
        # load file into grassgis
        # order is in this way, so final merged tiled is deleted last
        initGrassSetup(userDemDir.format(userid) , userid , lat , lon)
        #deleting all files in EPSG3857
        os.system('rm {0}/*'.format(gdalwarpDir))
        return True


def pointQuery(lat , lon , pointNum, firstMarker , viewNum , greaterthan , altitude , userid , dateStamp):
    if firstMarker:
        result = lookupSRTM(lat , lon , userid)
        if not result:
            # map not found break
            return None
    # run viewshed on point
    grassViewshed(lat ,lon , pointNum , userid)
    # use mapcalc to find common viewpoints
    grassCommonViewpoints(viewNum , greaterthan , altitude , userid , dateStamp)
    makeTransparent(userid)

# makes the image transparent
def makeTransparent(userid):
    inputFile = userFolder.format(userid) + options_viewsheds['combinedname'] + '.png'
    outputFile = userFolder.format(userid) + options_ucmi['locationpng']
    # Make transparent
    #convert viewshed1.png -fill red -opaque black -alpha copy -channel alpha -negate -channel alpha -evaluate multiply 0.5 output.png
    cmd = 'convert {0} -fill red -opaque black -alpha copy -channel alpha -negate -channel alpha -evaluate multiply 0.5  {1}'.format(inputFile,outputFile)
    print cmd
    os.system(cmd)



def main(args):
    lookupSRTM(36.95430926,-84.22389407, "343434")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
    

