#!/usr/bin/env python
import imp
import os
import sys
import subprocess
import json
from PIL import Image
from pyproj import Proj, transform
viewshedDir = '../static/viewsheds/{0}/{1}'


# connects to Grass GIS 6.4
def connect2grass64(userid):       
    gisbase = os.environ['GISBASE'] = "/home/justin/grass/grass-6.4.6svn"
    gisdbase = os.path.join(os.environ['HOME'], "grassdata64")
    location = "grass64location"
    mapset   = "grass64"
    sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "python"))
    import grass.script as g
    import grass.script.setup as gsetup
    gsetup.init(gisbase,
                gisdbase, location, mapset)
                
    mapsets = g.parse_command('g.mapset',
                    flags = 'l')
    mapsets = mapsets.keys()[0].split(' ')
    if userid not in mapsets:
        # create mapset
        g.parse_command('g.mapset',
                        mapset = str(userid),
                        flags = 'c')
    else:
        # don't create mapset sinceit already exists
        g.parse_command('g.mapset',
                mapset = str(userid),
                )
    mapset   =  userid
    gsetup.init(gisbase,
            gisdbase, location, mapset)

    return g


# Finds the highest neighbor. Currently using r.what but that might be inneficient
def highestNeighbor(x , y , g , userid):

    cell_res = 35.18111132 # meters. hard coded for now
    # r.what --v -f -n input=tile@grass64 east_north=-11796467.922180,4637784.666290
    maxElevation = -1000
    for i in range(- int(500 / cell_res) , int(500 / cell_res)):
        for j in range(- int(500 / cell_res) , int(500 / cell_res)):
            x_coor = x + i * cell_res
            y_coor = y + j * cell_res
            info = g.parse_command('r.what' , 
                            input = 'tile@' + str(userid),
                            east_north= str(x_coor) + ',' + str(y_coor))
            elevation = int(info.keys()[0].split('||')[1])
            if maxElevation < elevation:
                maxElevation = elevation
                max_x = x_coor
                max_y = y_coor
    return max_x , max_y

# def mapcalc(exp, quiet = False, verbose = False, overwrite = False, **kwargs):
#     >>> expr1 = '"%s" = "%s" * 10' % (output, input)
# r.cuda.viewshed --overwrite input=n38_w106_1arc_v3@grass64 output=fastviewshed coordinate=1,1

def initGrassSetup(gdalwarpDir, userid,  filename = 'tile.tif'):
    # redudant conections to grass
    g = connect2grass64(userid)
    # r.in.gdal input=/home/justin/Documents/ucmi/geodata/zip/tempEPSG3857/tile.tif output=tile
    g.parse_command(
        'r.in.gdal',
        input = gdalwarpDir + filename,
        output = filename[:-4] ,
        overwrite = True, 
        )
        
    g.parse_command('g.region' ,
                    rast = filename[:-4] + '@' + str(userid))
    
    # remove old viewsheds
    viewsheds = [viewshed for viewshed in g.list_strings(type = 'rast') if 'viewshed' in viewshed and userid in viewshed]
    # g.remove -f rast=fastviewshed34@grass64,fastviewshed@grass64                    
    g.parse_command('g.remove' ,
        flags ='f',
        rast=','.join(viewsheds))                                    

def grassViewshed(lat , lng, pointNum , userid, outputDir = '/home/justin/Documents/ucmi/UCMI/static/viewsheds/'):
    # redudant conections to grass
    g = connect2grass64(userid)
    
    outProj = Proj(init='epsg:3857')
    inProj = Proj(init='epsg:4326')
    x , y = transform(inProj , outProj , lng , lat)
    x , y = highestNeighbor(x , y , g , userid)
    rasters = g.list_strings(type = 'rast')
    print rasters
    srtm = [raster for raster in rasters if 'tile' in raster and userid in raster][0]
    viewName = "viewshed{0}".format(pointNum )
    print 'r.cuda.viewshed' , (x , y)
    g.parse_command('r.cuda.viewshed',
                        input = srtm ,
                        output= viewName ,
                        coordinate = (x , y) ,
                        max_dist = '50000',
                        overwrite = True)
    print 'r.out.png'
    if pointNum == 1:
        # make a world file
        pngflags = 'w' # t makes null cells transparent and w outputs world file
    else:
        pngflags = ''
    g.parse_command('r.out.png',
        flags = pngflags, 
        input = viewName + '@' + str(userid),
        output = viewshedDir.format(userid , 'viewsheds/') + viewName + '.png',
        overwrite = True)
    if pointNum == 1:
        wld2Json(viewshedDir.format(userid , 'viewsheds/') , 'viewshed1' , userid )
                        
    
    
def grassCommonViewpoints(viewNum , greaterthan , altitude , userid , dateStamp):
    g = connect2grass64(userid)

    filename = str(dateStamp)

    rasters = g.list_strings(type = 'rast')
    print rasters
    viewshedRasters = [raster for raster in rasters if 'viewshed' in raster and userid in raster and '_H' not in raster]
    if greaterthan:
        sign = '>'
    else:
        sign = '<'

    # No viewsheds exists, so display area above/below altitude filter
    if viewNum == -1:
        expression = "'combined = "  +  "(tile@{0}   {1}  {2})'".format(userid, sign , altitude)
    else:
        expression = "'combined = " + ' * '.join(viewshedRasters) +  "* (tile@{0}   {1}  {2})'".format(userid, sign , altitude)
    print "map calc"
    print expression
    #info = g.mapcalc(exp = expression, overwrite = True , verbose=True)   
    g.parse_command('r.mapcalc' , expression)
    # make 0 cells null
    print "r.null"
    g.parse_command('r.null',
                    map='combined@' + str(userid),
                    setnull = 0)
    #r.out.png -t -w --overwrite input=my_viewshed@ucmiGeoData output=/home/justin/Documents/ucmi/geodata/viewsheds/viewshed.png
    #not sure why I can't call as r.out.png(...)
    print "r.out"
    print 'making directory ' + viewshedDir.format(userid)
    if not os.path.isdir(viewshedDir.format(userid)):
        os.mkdir(viewshedDir.format(userid))
    g.parse_command('r.out.png',
        flags = 'wt', # makes null cells transparent and w outputs world file
        input = 'combined@' + str(userid),
        output = viewshedDir.format(userid) + filename + '.png',
        overwrite = True)
        
    # convert world file to json file with east, west, north, south bounds    
    wld2Json(viewshedDir.format(userid) , filename , userid)
    
# reads a world file and converts calculates east, west, north, south bounds. Writes out in JSON format
def wld2Json(outputDir , filename , userid ):
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
    g = open( outputDir + filename + '.json','w')
    g.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
    g.close()
    
 


def main(args):
    pass

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
