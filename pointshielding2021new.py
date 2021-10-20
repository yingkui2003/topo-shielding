# ---------------------------------------------------------------------------
# PointShielding.py
# Rewroten on: 2020-03-05
# Usage: PointShielding <Input_DEM> <Input_Point> <StrikeField> <DipField> <HeightField> <ShieldField> <Output_Point>  
#
# Description: 
#
# This is the python-only code to run the topographic shielding calculation for multiple points with the consideration
# of the strike, dip, and height info for each sample. The strike and dip are considered in the calculation following
# the method described by Balco on the Cosmogenic online Calculator. Note that strike is 90 degree less that the dip
# direction (aspect) of the sample slope. The shielding calulation is based on the skyline and skyline graph functions.
# This python tool allows for the Strike, Dip, Height, and new shielding fields as optional parameters. This tools also
# delete all intermidiate datasets created during the calculation processes.
# 
# One major thing for the skyline analysis is the map projection of the point and the DEM should be the same.
# Otherwise, the error will occur during the skyline calculation.
# 
# Yingkui Li
# Department of Geography
# University of Tennessee
# Knoxville, TN 37996
# 
# 03/05/2020
# Revised 10/20/2021
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy, os, sys
from arcpy.sa import *
from math import *

#Define a function for shielding calculation 
def shieldfunction (angle, dipEle):
    ele = max( (90 - angle), dipEle)
    if ele >= 0:
        return sin (ele * 3.14159 / 180.0 ) ** 3.3
    else:
        return 0.0

#Setup the overwrite
overwrite = arcpy.env.overwriteOutput
arcpy.env.overwriteOutput = True

arcpy.Delete_management("in_memory") ### Empty the in_memory

ArcGISPro = 0
arcpy.AddMessage("The current python version is: " + str(sys.version_info[0]))
if sys.version_info[0] == 2:  ##For ArcGIS 10, need to check the 3D and Spatial Extensions
    try:
        if arcpy.CheckExtension("Spatial")=="Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            raise Exception ("not extension available")
            #print "not extension available"
    except:
        raise Exception ("unable to check out extension")
        #print "unable to check out extension"

    try:
        if arcpy.CheckExtension("3D")=="Available":
            arcpy.CheckOutExtension("3D")
        else:
            raise Exception ("not extension available")
            #print "not extension available"
    except:
        raise Exception ("unable to check out extension")
        #print "unable to check out extension"
elif sys.version_info[0] == 3:  ##For ArcGIS Pro
    ArcGISPro = 1
    #pass ##No need to Check
else:
    raise Exception("Must be using Python 2.x or 3.x")
    exit()   
    
# Script arguments
Input_DEM = arcpy.GetParameterAsText(0)    #Input DEM, suggest UTM projection
Input_Point = arcpy.GetParameterAsText(1)  #Input sample points
StrikeField = arcpy.GetParameterAsText(2)  #Strike field
DipField = arcpy.GetParameterAsText(3)     #Dip field
HeightField = arcpy.GetParameterAsText(4)  #Height above surface field 
ShieldField = arcpy.GetParameterAsText(5)  #The new Shield Field that will be created in the output file
Output_Point = arcpy.GetParameterAsText(6) #Output feature class, shapefile

# Local variables:
#determine a temp path for temp datasets. This temp path is the path where the python file and models are saved
#in this way, the potential error can be avioded due to the use of geodatabase feature classes
#the DEM raster may still require the simple folder name without the space
#tmppath = os.path.split(sys.argv[0])[0]
Inputpointcopy = "in_memory\\Inputpointcopy"
Extractpoints = "in_memory\\Extractpoints"
point3d = "in_memory\\point3d"
singlePoint3d = "in_memory\\singlePoint3d"
skylinefeature = "in_memory\\skylinefeature"
skytable = "in_memory\\skytable"
sumtable = "in_memory\\sumtable"
output_layer = "output_layer"

#Make a copy of the Input Point data to Output
arcpy.CopyFeatures_management(Input_Point, Inputpointcopy)
arcpy.MakeFeatureLayer_management(Inputpointcopy, output_layer)

#Define optional arguments for Strike, Dip, Base Height, and New Shield field
if StrikeField == '#' or not StrikeField:
    StrikeField = "defStrike" # provide a default value if unspecified and make sure to add a new field and assign values to 0
    arcpy.AddField_management(Inputpointcopy, StrikeField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(Inputpointcopy, StrikeField, "0", "", "")

if DipField == '#' or not DipField:
    DipField = "defDip" # provide a default value if unspecified
    arcpy.AddField_management(Inputpointcopy, DipField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(Inputpointcopy, DipField, "0", "", "")

if HeightField == '#' or not HeightField:
    HeightField = "defBaseH" # provide a default value if unspecified
    arcpy.AddField_management(Inputpointcopy, HeightField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(Inputpointcopy, HeightField, "0", "", "")

if ShieldField == '#' or not ShieldField:
    ShieldField = "defShed" # provide a default value if unspecified


# Process: Add Field
arcpy.AddField_management(Inputpointcopy, ShieldField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

####3/5/2020: Use the Interpolate Shape tool to extract DEM values to a 3D feature output
#### Need to consider the height for each points 10/20/2021
#arcpy.InterpolateShape_3d(Input_DEM, Output_Point, point3d)
AltField = "xxAltxx"
ExtractValuesToPoints(Inputpointcopy, Input_DEM, Extractpoints,"INTERPOLATE", "VALUE_ONLY")
arcpy.AddField_management(Extractpoints, AltField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
#arcpy.AddMessage("Calculated Function: " + expression)
if ArcGISPro == 0:
    expression = "["+HeightField + "] + [RASTERVALU] + 0.02"
    #arcpy.CalculateField_management(Extractpoints, AltField, expression, "VB", "")
else:
    expression = "!"+HeightField + "! + !RASTERVALU! + 0.02"
    #arcpy.CalculateField_management(Extractpoints, AltField, expression, "#", "#")
arcpy.CalculateField_management(Extractpoints, AltField, expression, "#", "#")
    
arcpy.FeatureTo3DByAttribute_3d(Extractpoints, point3d, AltField, '#')

# An interation of all points. Each point will be selected and run the skyline and skyline graph functions to calculate the shielding and
# then assign the shielding value to the output file. The corresponding output row is determined by Select by Attribute function 
nCount = arcpy.GetCount_management(point3d)
pntID = arcpy.Describe(point3d).OIDFieldName
for i in range(int(nCount[0])):  #Start from 0: only for shapefile
    #con_for_shp = "FID = " + str(i)  #if the output is a shapefile, FID starts from 0
    condition = pntID + " = " + str(i+1) #if the output is a feature class, FID starts from 1
    arcpy.AddMessage("Processing Point #" + str(i+1) +" of "+str(int(nCount[0])))
    #Select each feature for Skyline analysis
    arcpy.Select_analysis(point3d, singlePoint3d, condition)
    arcpy.SelectLayerByAttribute_management(output_layer, "NEW_SELECTION", condition)
        
    ##Save the dip and strick as the global variable
    with arcpy.da.SearchCursor(singlePoint3d, [DipField, StrikeField]) as cursor:
        for row in cursor:
            dip = row[0]
            strike = row[1]

    # Process: Skyline
    arcpy.Skyline_3d(singlePoint3d, skylinefeature, Input_DEM, "1000 Meters", "0 Meters", "", "FULL_DETAIL", "0", "360", "1", "0 Meters", "NO_SEGMENT_SKYLINE", "100", "VERTICAL_ANGLE", "SKYLINE_MAXIMUM", "NO_CURVATURE", "NO_REFRACTION", "0.13", "0", "NO_CREATE_SILHOUETTES")

    # Process: Skyline Graph
    arcpy.SkylineGraph_3d(singlePoint3d, skylinefeature, "0", "NO_ADDITIONAL_FIELDS", skytable, "")

    # Process: Add Field (2)
    arcpy.AddField_management(skytable, "DipElev", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(skytable, "TopoShield", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    # Calculate the DipElev in the skytable
    with arcpy.da.UpdateCursor(skytable, ["ZENITH_ANG","HORIZ_ANG", "DipElev", "TopoShield"] ) as cursor:
        for row in cursor:
            zenith = row[0]
            horiz = row[1]
            row[2] = atan(tan(dip*3.14159/180) * cos((90 - horiz - strike + 90)*3.14159/180))*180/3.14159
            row[3] = shieldfunction(zenith,row[2])
            cursor.updateRow(row)

    # Process: Summary Statistics
    arcpy.Statistics_analysis(skytable, sumtable, "TOPOSHIELD MEAN", "")

    # Process: Get Field Value
    with arcpy.da.SearchCursor(sumtable, ["MEAN_TOPOSHIELD"] ) as cursor:
        for row in cursor:
            meanshield = 1- row[0]

    # Process: Calculate Field (3) for the output dataset
    arcpy.CalculateField_management(output_layer, ShieldField, meanshield, "#", "#")

#Remove selection in output
arcpy.SelectLayerByAttribute_management(output_layer, "CLEAR_SELECTION")

##Copy to output
arcpy.CopyFeatures_management(output_layer, Output_Point)

#Delete all temp files
#arcpy.Delete_management(point3d)
#arcpy.Delete_management(singlePoint3d)
#arcpy.Delete_management(skylinefeature)
#arcpy.Delete_management(skytable)
#arcpy.Delete_management(sumtable)
#arcpy.Delete_management(output_layer)

##Delete intermidiate data
arcpy.Delete_management("in_memory") ### Empty the in_memory
arcpy.Delete_management(output_layer)

#Reset the default overwrite of the system
arcpy.env.overwriteOutput = overwrite











