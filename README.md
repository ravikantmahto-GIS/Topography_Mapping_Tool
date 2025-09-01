# Topography Mapping Tool (QGIS Plugin)

The **Topography Mapping Tool** is a QGIS plugin that streamlines the process of downloading, mosaicking, clipping, and hillshade generation from Copernicus DEM (30m) data. Designed with researchers and GIS professionals in mind, it enables rapid creation of **publication-ready topographic maps** for reports and scientific papers. The plugin integrates **DEM processing, hillshade visualization, color ramp symbology, cartographic map layouts, grid/coordinates,** making it especially useful for **geomorphology, geology, hydrology, disaster mitigation and environmental studies**. Its intuitive interface allows users to efficiently generate high-quality terrain visualization products that support spatial analysis, research communication, and decision-making.

---

##  Features
-  **Automatic DEM download** from Copernicus (30m COG).  
-  **Mosaicing & clipping** DEM tiles by latitude/longitude extent.  
-  **Hillshade generation** with 50% transparency overlay.  
-  **Customizable color ramps** for DEM visualization.  
-  **Map layout creation** (legend and coordinates).  
-  **Progress bar & cancel option** during processing.  

---

##  Installation
1. Download this repository or clone it:
   ```bash
   git clone https://github.com/ravikantmahto-GIS/topography_mapping_tool.git

2. Copy the plugin folder (topography_mapping_tool) into your QGIS profile’s plugin directory:

Windows:
C:\Users\<User>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins

Linux/Mac:
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins

3. Restart QGIS → Enable plugin in Plugins > Manage and Install Plugins.

---

##  Usage

1. Open Topography Mapping Tool from the QGIS plugin menu.

2. Enter bounding box coordinates (lat_min, lat_max, lon_min, lon_max).

3. Choose whether to use current map canvas extent.

4. Set output DEM and hillshade name & select a DEM color ramp.

5. Click Run → The DEM tiles will be downloaded, mosaiced, hillshaded, and loaded into QGIS.

6. A printable map layout (PDF/PNG) will also be generated automatically.

---   

##  Example Output

<img width="2407" height="1210" alt="Example_topography_map" src="https://github.com/user-attachments/assets/a4edd1b6-0238-4d1f-acb3-b1c1e81b324a" />

---  

##  Author : Ravikant
Email: ravikant.mahto@gmail.com

##  License 
This plugin is released under the GNU GPL v2 license




