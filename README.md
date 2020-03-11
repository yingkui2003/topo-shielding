# Point-based topographic shielding tool

Rewroten on: 2020-03-05
Usage: PointShielding <Input_DEM> <Input_Point> <StrikeField> <DipField> <HeightField> <ShieldField> <Output_Point>  

This is an updated python-only code to run the topographic shielding calculation for multiple points with the consideration of the strike, dip, and height info for each sample. The strike and dip are considered in the calculation following the method described by Balco on the Cosmogenic online Calculator. Note that strike is 90 degree less that the dip direction (aspect) of the sample slope. The shielding calulation is based on the skyline and skyline graph functions. This python tool allows for the Strike, Dip, Height, and new shielding fields as optional parameters. This tools also delete all intermidiate datasets created during the calculation processes. One major thing for the skyline analysis is the map projection of the point and the DEM should be the same. Otherwise, the error will occur during the skyline calculation. 

Input DEM
This is the input DEM to derived the topographic shielding

Input Points
This is the input point file. The map projection of the point and the DEM should be the same

Strike Field (optional)
This field stores the strike value of each point (0-360 degree). Note that strike is 90 degree less that the dip direction (aspect) of the sample slope. The default value is 0.

Dip Field (optional)
This field stores the dip value of each point (0-90 degree).The default value is 0.

Height Field (optional)
This field stores the height of each sample point above the ground. The default value is 0.

New Shield Field (optional)
The is the derived shielding field name that will be added to the attibute table. The default is defShed.

Output Points
Output point file with derived topographic shielding value for each point.
