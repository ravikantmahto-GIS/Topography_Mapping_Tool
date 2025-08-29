# 🌍 Topography Mapping Tool (QGIS Plugin)

The **Topography Mapping Tool** is a QGIS plugin that automates downloading, mosaicing, clipping, and hillshade generation of **Copernicus DEM (30m)** data. It provides a simple interface to generate topographic maps with color ramps, hillshade overlays, and automatic map layouts.

---

## ✨ Features
- 📥 **Automatic DEM download** from Copernicus (30m COG).  
- 🗺️ **Mosaicing & clipping** DEM tiles by latitude/longitude extent.  
- ⛰️ **Hillshade generation** with 50% transparency overlay.  
- 🎨 **Customizable color ramps** for DEM visualization.  
- 🧭 **Map layout creation** (legend, north arrow, scale bar, coordinates).  
- ⏳ **Progress bar & cancel option** during processing.  

---

## 🛠️ Installation
1. Download this repository or clone it:
   ```bash
   git clone https://github.com/ravikantmahto-GIS/topography-mapping-tool.git

2. Copy the plugin folder (topography_mapping_tool) into your QGIS profile’s plugin directory:

Windows:
C:\Users\<User>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins

Linux/Mac:
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins

3. Restart QGIS → Enable plugin in Plugins > Manage and Install Plugins.

---

## 🚀 Usage

1. Open Topography Mapping Tool from the QGIS plugin menu.

2. Enter bounding box coordinates (lat_min, lat_max, lon_min, lon_max).

3. Choose whether to use current map canvas extent.

4. Set output DEM and hillshade name & select a DEM color ramp.

5. Click Run → The DEM tiles will be downloaded, mosaiced, hillshaded, and loaded into QGIS.

6. A printable map layout (PDF/PNG) will also be generated automatically.

---   

## 📸 Example Output
