## Installation Guide – Topography Mapping Tool

**1. System Requirements**
- QGIS: Version 3.22 LTR or higher (tested on QGIS 3.40.x)

- Python: Comes bundled with QGIS (no need for separate installation)

- Internet Connection: Required for downloading Copernicus DEM tiles

**2. Install Plugin from Source**

1. Clone the repository (or download ZIP):

      git clone https://github.com/your-username/Topography_Mapping_Tool.git

2. Copy the plugin folder into your local QGIS plugins directory:

**Windows:**

    C:\Users\<YourUser>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\

**Linux:**

    ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

**MacOS:**

    ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/


**Restart QGIS.**
 - Go to Plugins → Manage and Install Plugins → Installed → check Topography Mapping Tool.

**3. Python Dependencies**

The plugin depends on a few Python libraries. Install them using:

- pip install -r requirements.txt

This installs:

    numpy

    matplotlib

    requests

    rasterio

    rioxarray

    boto3

    gdal

⚠️ Note: Some of these (e.g., GDAL) are already bundled with QGIS, but keeping them in requirements ensures compatibility.
