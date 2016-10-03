#!/usr/bin/env python
import imp
import os
import sys
import subprocess
import json
from PIL import Image
from pyproj import Proj, transform
viewshedDir = '/home/justin/Documents/ucmi/UCMI/static/viewsheds/'



# def mapcalc(exp, quiet = False, verbose = False, overwrite = False, **kwargs):
#     >>> expr1 = '"%s" = "%s" * 10' % (output, input)
# r.cuda.viewshed --overwrite input=n38_w106_1arc_v3@grass64 output=fastviewshed coordinate=1,1

def initGrassSetup(filename = 'tile.tif'):
    g = connect2grass64()
    # r.in.gdal input=/home/justin/Documents/ucmi/geodata/zip/tempEPSG3857/tile.tif output=tile
    g.parse_command(
        'r.in.gdal',
        input = '/home/justin/Documents/ucmi/geodata/zip/tempEPSG3857/' + filename,
        output = filename[:-4],
        overwrite = True, 
        )
        
    g.parse_command('g.region' ,
                    rast = filename[:-4] + '@grass64')
    
    # remove old viewsheds
    viewsheds = [viewshed for viewshed in g.list_strings(type = 'rast') if 'viewshed' in viewshed]
    # g.remove -f rast=fastviewshed34@grass64,fastviewshed@grass64                    
    g.parse_command('g.remove' ,
        flags ='f',
        rast=','.join(viewsheds))                                    

    
def grassViewshed(lat , lng, pointNum , outputDir = '/home/justin/Documents/ucmi/UCMI/static/viewsheds/'):
    # redudant conections to grass
    g = connect2grass64()
    
    outProj = Proj(init='epsg:3857')
    inProj = Proj(init='epsg:4326')
    x , y = transform(inProj , outProj , lng , lat)
    rasters = g.list_strings(type = 'rast')
    srtm = [raster for raster in rasters if 'tile' in raster][0]
    viewName = "viewshed{0}".format(pointNum)
    g.parse_command('r.cuda.viewshed',
                        input = srtm ,
                        output= viewName ,
                        coordinate = (x , y) ,
                        max_dist = '50000',
                        overwrite = True)
    

def grassCommonViewpoints(viewNum , greaterthan , altitude):
    filename = 'commonviewshed' + str(viewNum)
    # redudant conections to grass
    g = connect2grass64()
        
    rasters = g.list_strings(type = 'rast')
    viewshedRasters = [raster for raster in rasters if 'viewshed' in raster]
    # No viewsheds exists, so display area above/below altitude filter
    if viewNum == -1:
        expression = 'combined = '  +  '(tile@grass64   >  {0})'.format(altitude)
    elif greaterthan:
        expression = 'combined = ' + ' * '.join(viewshedRasters) +  '* (tile@grass64   >  {0})'.format(altitude)
    else:
        expression = 'combined = ' + ' * '.join(viewshedRasters) +  '* (tile@grass64   <  {0})'.format(altitude)
    g.mapcalc(exp = expression, overwrite = True)        
    
    # make 0 cells null
    g.parse_command('r.null',
                    map='combined@grass64',
                    setnull = 0)
    #r.out.png -t -w --overwrite input=my_viewshed@ucmiGeoData output=/home/justin/Documents/ucmi/geodata/viewsheds/viewshed.png
    #not sure why I can't call as r.out.png(...)
    g.parse_command('r.out.png',
        flags = 'wt', # makes null cells transparent and w outputs world file
        input = 'combined@grass64',
        output = viewshedDir + filename + '.png',
        overwrite = True)
        
    # convert world file to json file with east, west, north, south bounds    
    wld2Json(viewshedDir , filename)
    
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
    
 
# connects to Grass GIS 6.4
def connect2grass64():       
    gisbase = os.environ['GISBASE'] = "/home/justin/grass/grass-6.4.6svn"
    gisdbase = os.path.join(os.environ['HOME'], "grassdata64")
    location = "grass64location"
    mapset   = "grass64"
    sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "python"))
    import grass.script as g
    import grass.script.setup as gsetup
    gsetup.init(gisbase,
                gisdbase, location, mapset)
    return g

def main(args):
    connect2grass64()

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
