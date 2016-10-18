#!/usr/bin/env python
''' Processes GIS data through GRASS GIS / python interface.'''

import imp , os, sys , json , subprocess , shutil , configparser , inspect
from PIL import Image
from pyproj import Proj, transform

config = configparser.ConfigParser()
config.read('../config.ini')
this_file = os.path.split(inspect.getfile(inspect.currentframe()))[-1]
options = config._sections[this_file]
options_ucmi = config._sections['ucmi.py']

script_dir = os.path.dirname(os.path.abspath(this_file)) 
viewshedDir = '/'.join(['..' , options_ucmi['viewsheddir'] , '{0}']) + '/'


# connects to Grass GIS 7.0
def connect2grass(userid):       
     # path to the GRASS GIS launch script
    # Linux 
    grass7bin = options['grass7bin']

    # DATA
    # define GRASS DATABASE
    # add your path to grassdata (GRASS GIS database) directory
    gisdb = os.path.join(os.path.expanduser("~"), "grassdata")
     
    # specify (existing) location and mapset
    location = options['location']
     
    # query GRASS 7 itself for its GISBASE
    startcmd = [grass7bin, '--config', 'path']
     
    p = subprocess.Popen(startcmd, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        print >>sys.stderr, "ERROR: Cannot find GRASS GIS 7 start script (%s)" % startcmd
        sys.exit(-1)
    gisbase = out.strip('\n\r')
     
    # Set GISBASE environment variable
    os.environ['GISBASE'] = gisbase
    # the following not needed with trunk
    os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
    # add path to GRASS addons
    home = os.path.expanduser("~")
    os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')
     
    # define GRASS-Python environment
    gpydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(gpydir)
     
    ########### DATA
    # Set GISDBASE environment variable
    os.environ['GISDBASE'] = gisdb

    # import GRASS Python bindings (see also pygrass)
    import grass.script as gscript
    import grass.script.setup as gsetup
     
    if not os.path.isdir('/'.join([gisdb,location,userid])):
        # Create new mapset by creating folder and WIND file
        # sloppy, but I'm not sure how to do it directly.
        print "mapset not found"
        print "creating mapset"
        os.mkdir('/'.join([gisdb,location,userid]))
        shutil.copyfile('/'.join([gisdb,location,'PERMANENT' , 'WIND']) , '/'.join([gisdb,location,userid , 'WIND'])) 
    
    mapset   = userid

    
    ###########
    # launch session
    gsetup.init(gisbase,
                gisdb, location, mapset)
    from grass.pygrass.modules.shortcuts import general as g
    from grass.pygrass.modules.shortcuts import raster as r
    
    # example calls
    gscript.message('Current GRASS GIS 7 environment:')
    print gscript.gisenv()
        
    
    return  r , g , gscript


# Finds the highest neighbor. Currently using r.what but that might be inneficient
def highestNeighbor(x , y , gscript , userid):
    # print out region for debugging purposes
    print "Finding points higher at " , x ,y
    cell_res = config.getfloat(this_file, "cell_res") # meters. hard coded for now
    # r.what --v -f -n input=tile@grass64 east_north=-11796467.922180,4637784.666290
    maxElevation = -1000
    max_x = x
    max_y = y
    bndry = config.getint(this_file, "high_point_bndry") # (meters)
    # size of square to search for the peak value
    for i in range(- int(bndry / cell_res) , int(bndry / cell_res)):
        for j in range(- int(bndry / cell_res) , int(bndry / cell_res)):
            x_coor = x + i * cell_res
            y_coor = y + j * cell_res
            info = gscript.raster_what(options['demname'] + '@' + str(userid), [[x_coor ,y_coor ]])
            info = info[0]
            info = info[info.keys()[0]]
            elevation = int(info['value'])
            if maxElevation < elevation:
                maxElevation = elevation
                max_x = x_coor
                max_y = y_coor
    return max_x , max_y

# Sets up conenction to GRASS GIS
def initGrassSetup(userDemDir , userid,  lat , lon , filename = options['demname'] + '.tif'):
    # redudant conections to grass
    r , g , gscript = connect2grass(userid)
    # r.in.gdal input=/home/justin/Documents/ucmi/geodata/zip/tempEPSG3857/tile.tif output=tile
    gscript.run_command(
        'r.in.gdal',
        input = userDemDir + filename,
        output = filename[:-4] ,
        overwrite = True, 
        )
    
    g.region(raster = filename[:-4] + '@' + str(userid))
    g.region(flags='p')
    
    # remove old viewsheds
    g.remove(
        flags ='fb',
        type='raster',
        pattern='viewshed*')                                     

# Performs viewshed calculation and then boolean adds resulting viewsheds
def grassViewshed(lat , lng, pointNum , userid, outputDir = '/'.join([script_dir , '..' , viewshedDir]) ):
    # redudant conections to grass
    r , g , gscript = connect2grass(userid)
    
    outProj = Proj(init='epsg:3857')
    inProj = Proj(init='epsg:4326')
    x , y = transform(inProj , outProj , lng , lat)
    x , y = highestNeighbor(x , y , gscript , userid)
    print "found higher neighbor at" , x, y
    rasters = gscript.list_strings(type = 'rast')
    print rasters
    srtm = [raster for raster in rasters if options['demname'] in raster and userid in raster][0]
    viewName = options['viewshedname'] + str(pointNum)
    print viewName
    r.viewshed(
        flags = 'b', #binary visible/invisible viewshed
        input = srtm ,
        output= viewName ,
        coordinates = (x , y) ,
        max_distance = -1,
        overwrite = True)
    
    combinedName = options['combinedname']
    if pointNum == 1:
        print "Overwriting existing map with copy"
        # copy existing viewshed to new combined map
        expression = combinedName + ' = {1}@{0}'.format(userid , viewName)
        print "r.mapcalc" , expression
        gscript.raster.mapcalc(expression, overwrite = True)
    else:
        # screen existing viewshed with new viewshed
        expression = '{0} = {0}@{1} * {2}@{1}'.format(combinedName , userid , viewName)
        print "r.mapcalc" , expression
        gscript.raster.mapcalc(expression, overwrite = True)

# Combines existing viewsheds and then filters out elevations. Outputs png image
def grassCommonViewpoints(viewNum , greaterthan , altitude , userid , dateStamp):
    r , g , gscript = connect2grass(userid)
    filename = str(dateStamp)
    combinedName = options['combinedname']

    # checking if user has asked for an elevation filter
    elevationFlag = (greaterthan and altitude > 3) or (not greaterthan and altitude < 29000)
    if not elevationFlag:
        # elevation filter is not asked for, so we can skip to directly exporting image
        pass
    else:
        if greaterthan:
            sign = '>'
        else:
            sign = '<'
        expression = "{0} = {0}@{1} * ({2}@{1} {3} {4})".format(combinedName , userid , options['demname'] , sign , altitude)
        print "map calc"
        print expression
        #info = g.mapcalc(exp = expression, overwrite = True , verbose=True)   
        gscript.raster.mapcalc(expression, overwrite = True)
        
    # make 0 cells null
    r.null(map= combinedName + '@' + str(userid) , setnull = 0)
    #r.out.png -t -w --overwrite input=my_viewshed@ucmiGeoData output=/home/justin/Documents/ucmi/geodata/viewsheds/viewshed.png
    #not sure why I can't call as r.out.png(...)
    print "r.out"    
    flags = ''
    if viewNum == 0:
        flags ='w' # makes null cells transparent and w outputs world file
    output =  viewshedDir.format(userid) + combinedName + '.png'
    gscript.run_command('r.out.png',
        flags = flags, 
        input = combinedName + '@' + str(userid),
        output = output,
        overwrite = True)
    if viewNum == 0:     
        # convert world file to json file with east, west, north, south bounds    
        wld2Json(output , userid)

# reads a world file and converts calculates east, west, north, south bounds. Writes out in JSON format
def wld2Json(output , userid):
    inProj = Proj(init='epsg:3857')
    outProj = Proj(init='epsg:4326')
    im=Image.open(output)
    im.size # (width,height) tuple
    im.close()
    
    f = open(output[:-4] + '.wld' , 'r')
    lines = f.readlines()
    xPixelRes = float(lines[0])
    yPixelRes = float(lines[3])
    data = {}
    x = float(lines[4].strip())
    y = float(lines[5].strip())
    data['userid'] = userid
    data['south'] = y + yPixelRes * im.size[1] 
    data['north'] = y 
    data['west'] = x
    data['east'] = x + im.size[0] * xPixelRes
    
    # convert to 4326
    data['west'] , data['south']  =  transform(inProj,outProj,data['west'] , data['south'])
    data['east'], data['north'] =  transform(inProj,outProj,data['east'], data['north'])
    f.close()
    
    # write to JSON file
    g = open( output[:-4] + '.json','w')
    g.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
    g.close()
    
 


def main(args):
    pass

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
