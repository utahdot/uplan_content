import arcpy

arcpy.management.CreateRelationshipClass(r"C:\Users\agilvarry.UTAH\Documents\ATOM Assets\assetmgmt@gisassetmgmt@Default.sde\gisassetmgmt.assetmgmt.assetmgmt.Asset_PT",
                                         r"C:\Users\agilvarry.UTAH\Documents\ATOM Assets\assetmgmt@gisassetmgmt@Default.sde\gisassetmgmt.assetmgmt.AS_Sign_Face",
                                         r"C:\Users\agilvarry.UTAH\Documents\ATOM Assets\assetmgmt@gisassetmgmt@Default.sde\gisassetmgmt.assetmgmt.SignsHaveLocations",
                                         "SIMPLE", "AS_Sign_Face", "Asset_PT", "NONE", "MANY_TO_MANY", "NONE", "globalid", "globalid", "geometryid", "geometryid")
