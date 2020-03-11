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
#
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

# Check out the ArcGIS Spatial Analyst and 3D extension license
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddMessage("Spatial Analyst license is unavailable")
    sys.exit()

if arcpy.CheckExtension("3D") == "Available":
    arcpy.CheckOutExtension("3D")
else:
    arcpy.AddMessage("3D Analyst license is unavailable")
    sys.exit()
    
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
tmppath = os.path.split(sys.argv[0])[0]
point3d = tmppath + "\\point3d.shp"
singlePoint3d = tmppath + "\\singlePoint3d.shp"
skylinefeature = tmppath + "\\skylinefeature.shp"
skytable = tmppath + "\\skytable"
sumtable = tmppath + "\\sumtable"
output_layer = "output_layer"

#Make a copy of the Input Point data to Output
arcpy.CopyFeatures_management(Input_Point, Output_Point)
arcpy.MakeFeatureLayer_management(Output_Point, output_layer)

#Determine is the output is a shapefile or feature class
desc = arcpy.Describe(Output_Point)
out_is_shapefile = 0
if (desc.extension == "shp"):
    out_is_shapefile = 1

#Define optional arguments for Strike, Dip, Base Height, and New Shield field
if StrikeField == '#' or not StrikeField:
    StrikeField = "defStrike" # provide a default value if unspecified and make sure to add a new field and assign values to 0
    arcpy.AddField_management(Output_Point, StrikeField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(Output_Point, StrikeField, "0", "VB", "")

if DipField == '#' or not DipField:
    DipField = "defDip" # provide a default value if unspecified
    arcpy.AddField_management(Output_Point, DipField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(Output_Point, DipField, "0", "VB", "")

if HeightField == '#' or not HeightField:
    HeightField = "defBaseH" # provide a default value if unspecified
    arcpy.AddField_management(Output_Point, HeightField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(Output_Point, HeightField, "0", "VB", "")

if ShieldField == '#' or not ShieldField:
    ShieldField = "defShed" # provide a default value if unspecified


# Process: Add Field
arcpy.AddField_management(Output_Point, ShieldField, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

####3/5/2020: Use the Interpolate Shape tool to extract DEM values to a 3D feature output
arcpy.InterpolateShape_3d(Input_DEM, Output_Point, point3d)

# An interation of all points. Each point will be selected and run the skyline and skyline graph functions to calculate the shielding and
# then assign the shielding value to the output file. The corresponding output row is determined by Select by Attribute function 
nCount = arcpy.GetCount_management(point3d)
for i in range(int(nCount[0])):  #Start from 0: only for shapefile
    con_for_shp = "FID = " + str(i)  #if the output is a shapefile, FID starts from 0
    con_for_fc = "ObjectID = " + str(i+1) #if the output is a feature class, FID starts from 1
    arcpy.AddMessage("Processing Point #" + str(i))
    #Select each feature for Skyline analysis
    arcpy.Select_analysis(point3d, singlePoint3d, con_for_shp)
    #Select by attribute for output for saving shielding result
    if (out_is_shapefile > 0):
        arcpy.SelectLayerByAttribute_management(output_layer, "NEW_SELECTION", con_for_shp)
    else:
        arcpy.SelectLayerByAttribute_management(output_layer, "NEW_SELECTION", con_for_fc)
        
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
    arcpy.CalculateField_management(output_layer, ShieldField, meanshield, "VB", "")

#Remove selection in output
arcpy.SelectLayerByAttribute_management(output_layer, "CLEAR_SELECTION")

#Delete all temp files
arcpy.Delete_management(point3d)
arcpy.Delete_management(singlePoint3d)
arcpy.Delete_management(skylinefeature)
arcpy.Delete_management(skytable)
arcpy.Delete_management(sumtable)
arcpy.Delete_management(output_layer)

#Reset the default overwrite of the system
arcpy.env.overwriteOutput = overwrite





