#!/usr/bin/env python
import imp
import os
import sys
import subprocess
import json
from PIL import Image
from pyproj import Proj, transform



MODULE_EXTENSIONS = ('.py', '.pyc', '.pyo')

def package_contents(package_name):
    file, pathname, description = imp.find_module(package_name)
    if file:
        raise ImportError('Not a package: %r', package_name)
    # Use a set because some may be both source and compiled.
    return set([os.path.splitext(module)[0]
        for module in os.listdir(pathname)
        if module.endswith(MODULE_EXTENSIONS)])
 
def grassViewshed(lat , lng,outputDir = '/home/justin/Documents/ucmi/UCMI/static/viewsheds/' , filename = 'viewshed'):
    # path to the GRASS GIS launch script
    # MS Windows
    grass7bin_win = r'C:\OSGeo4W\bin\grass70svn.bat'
    # uncomment when using standalone WinGRASS installer
    # grass7bin_win = r'C:\Program Files (x86)\GRASS GIS 7.0.0beta3\grass70.bat'
    # Linux
    grass7bin_lin = 'grass70'
    # Mac OS X
    # this is TODO
    grass7bin_mac = '/Applications/GRASS/GRASS-7.0.app/'
     
    # DATA
    # define GRASS DATABASE
    # add your path to grassdata (GRASS GIS database) directory
    gisdb = os.path.join(os.path.expanduser("~"), "grassdata")
    # the following path is the default path on MS Windows
    # gisdb = os.path.join(os.path.expanduser("~"), "Documents/grassdata")
     
    # specify (existing) location and mapset
    location = "ucmi"
    mapset   = "ucmiGeoData"
     
     
    ########### SOFTWARE
    if sys.platform.startswith('linux'):
        # we assume that the GRASS GIS start script is available and in the PATH
        # query GRASS 7 itself for its GISBASE
        grass7bin = grass7bin_lin
    elif sys.platform.startswith('win'):
        grass7bin = grass7bin_win
    else:
        raise OSError('Platform not configured.')
     
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
     
    ###########
    # launch session
    gsetup.init(gisbase,
                gisdb, location, mapset)
     
    gscript.message('Current GRASS GIS 7 environment:')
    print gscript.gisenv()
     
    gscript.message('Available raster maps:')
    for rast in gscript.list_strings(type = 'rast'):
        print rast
     
    gscript.message('Available vector maps:')
    for vect in gscript.list_strings(type = 'vect'):
        print vect
    
    from grass.pygrass.modules.shortcuts import general as g
    from grass.pygrass.modules.shortcuts import raster as r

    #r.viewshed --overwrite input=n38w106@ucmiGeoData output=my_viewshed coordinates=-11761109.3167,4671226.49836 max_distance=5000
    outProj = Proj(init='epsg:3857')
    inProj = Proj(init='epsg:4326')
    x , y = transform(inProj , outProj , lng , lat)
    
    
    r.viewshed(
        input = 'n38w106@ucmiGeoData' ,
        output= 'my_viewshed' ,
        coordinates = (x , y) ,
        max_distance = '50000',
        overwrite = True)
    
    # TODO: Find minimum area to reduce file size. Should be max_distance in a circle around view point
    g.region(raster = 'my_viewshed@ucmiGeoData')
    #r.out.png -t -w --overwrite input=my_viewshed@ucmiGeoData output=/home/justin/Documents/ucmi/geodata/viewsheds/viewshed.png
    #not sure why I can't call as r.out.png(...)
    gscript.run_command('r.out.png',
        flags = 'wt', # makes null cells transparent and w outputs world file
        input = 'my_viewshed@ucmiGeoData',
        output = outputDir + filename,
        overwrite = True)
        
    # convert world file to json file with east, west, north, south bounds    
    wld2Json(outputDir , filename)


# reads a world file and converts calculates east, west, north, south bounds. Writes out in JSON format
def wld2Json(outputDir , filename):

    inProj = Proj(init='epsg:3857')
    outProj = Proj(init='epsg:4326')

    
    
    im=Image.open(outputDir + filename + '.png')
    im.size # (width,height) tuple
    im.close()
    
    f = open(outputDir + filename + '.wld' , 'r')
    lines = f.readlines()
    xPixelRes = float(lines[0])
    yPixelRes = float(lines[3])
    data = {}
    x = float(lines[4].strip())
    y = float(lines[5].strip())
    data['south'] = y + yPixelRes * im.size[1] 
    data['north'] = y 
    data['west'] = x
    data['east'] = x + im.size[0] * xPixelRes
    
    
    # convert to 4326
    data['west'] , data['south']  =  transform(inProj,outProj,data['west'] , data['south'])
    data['east'], data['north'] =  transform(inProj,outProj,data['east'], data['north'])

    
    f.close()
    
    # write to JSON file
    g = open( outputDir + filename + '.json','w')
    g.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
    g.close()
    
    
    
        
def main(args):
    grass()

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
