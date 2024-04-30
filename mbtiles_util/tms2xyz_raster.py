#!/usr/bin/env python
import os, fnmatch, shutil, sys, argparse

#get the command line arguments and get some variables set up
parser = argparse.ArgumentParser(description='Convert a TMS directory structure (like one created with gdal2tiles) to a XYZ structure')
parser.add_argument('inDIR', type=str, nargs=1, help='The directory containing the TMS files')
parser.add_argument('outDIR', type=str, nargs=1, help='The output directory for the XYZ files')
args = parser.parse_args()
inDIR = args.inDIR[0]
copyDIR = args.outDIR[0]
# pattern = '*png' #only looking for png images and will skip the rest later on
pattern = '*pbf' #only looking for png images and will skip the rest later on
fileList = []

#check to see if output directory exists, die if it does
if os.path.exists(copyDIR):
    sys.exit("ERROR: The output directory already exists!") #exit the script if the output already exists

#move into the directory you want to copy
os.chdir(inDIR)

# Walk through directory and get the files listed
for rVal, dName, fList in os.walk("."):
    #make the directory structure to put the new tiles into
    newpath = os.path.join("..", copyDIR, rVal)
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    
    for fileName in fList: #loop through all the files
        if fnmatch.fnmatch(fileName, pattern): # Match search string
            if rVal.find("/") > -1:
                 zxParts = rVal.split("/")
            else:
                 zxParts = rVal.split("\\")
            yParts = fileName.split(".")
            # newY = str(2**int(zxParts[1])-int(yParts[0])-1) + ".png"
            newY = str(2**int(zxParts[1])-int(yParts[0])-1) + ".pbf"
            shutil.copyfile((os.path.join(rVal, fileName)), (os.path.join(newpath, newY)))
        else:
            print ("skipping file:" , fileName)