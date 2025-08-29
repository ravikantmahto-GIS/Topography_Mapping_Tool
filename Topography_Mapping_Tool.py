from . import resources
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.core import Qgis
from qgis.PyQt.QtGui import QPixmap, QPainter
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSize
from qgis.core import QgsRasterBandStats
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import (
    QgsApplication,
    QgsTask,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsStyle,
    QgsRasterShader,
    QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer,
    QgsSingleBandGrayRenderer,
    QgsPrintLayout,
    QgsLayoutItemMap,
    QgsLayoutExporter,
    QgsUnitTypes,
    QgsLayoutItemScaleBar,
    QgsLayoutItemPicture,
    QgsLayoutSize,
    QgsLayoutPoint,
    QgsLayoutItemMapGrid
)

import os
import math
import requests
from osgeo import gdal
import rasterio
from rasterio.fill import fillnodata
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from rasterio.plot import show
from matplotlib import colors
import numpy as np


class TopographyMapper:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u'&Topography_Mapping_Tool')
        self.first_start = None
        self._current_task = None
        self.output_dir = os.path.join(self.plugin_dir, "outputs")
        os.makedirs(self.output_dir, exist_ok=True)

    def tr(self, message):
        return QCoreApplication.translate('TopographyMapper', message)

    def add_action(
        self, icon_path, text, callback, parent=None
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        self.iface.addToolBarIcon(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = ':/plugins/Topography_Mapping_Tool/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Topography Mapping Tool'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )
        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def reset_dialog(self):
        """Reset dialog inputs when plugin is re-opened"""
        self.dlg.lat_min.setValue(0.0)
        self.dlg.lat_max.setValue(0.0)
        self.dlg.lon_min.setValue(0.0)
        self.dlg.lon_max.setValue(0.0)
        self.dlg.txt_output_name.setText("")
        self.dlg.progress_bar.setValue(0)
        self.dlg.lbl_progress.setText("Progress")

    def run(self):
        from .Topography_Mapping_Tool_dialog import TopographyMapperDialog
        if self.first_start:
            self.first_start = False
            self.dlg = TopographyMapperDialog()

            # Connect buttons
            self.dlg.btn_run.clicked.connect(self.on_run_clicked)
            self.dlg.btn_cancel.clicked.connect(self.on_cancel_clicked)

        style = QgsStyle().defaultStyle()
        ramps = style.colorRampNames()

        self.dlg.cmb_colormap.clear()

        for ramp_name in ramps:
            ramp = style.colorRamp(ramp_name)

            # Create preview pixmap
            w, h = 250, 30
            pixmap = QPixmap(w, h)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)

            # Draw gradient strip
            for x in range(w):
                val = x / (w - 1)
                color = ramp.color(val)
                painter.setPen(color)
                painter.drawLine(x, 0, x, h)

            painter.end()

            # Add item with icon + text
            self.dlg.cmb_colormap.addItem(QIcon(pixmap), ramp_name)
            self.dlg.cmb_colormap.setIconSize(QSize(250, 30))
        # Reset fields each time plugin opens
        self.reset_dialog()

        self.dlg.show()

    def on_run_clicked(self):
        lat_min = self.dlg.lat_min.value()
        lat_max = self.dlg.lat_max.value()
        lon_min = self.dlg.lon_min.value()
        lon_max = self.dlg.lon_max.value()
        output_name = self.dlg.txt_output_name.text().strip()
        if not output_name:
            output_name = "hillshade_map"

        tile_dir = os.path.join(self.plugin_dir, "dem_tiles")
        os.makedirs(tile_dir, exist_ok=True)

        output_dem = os.path.join(self.output_dir, f"{output_name}_dem.tif")
        output_hs = os.path.join(self.output_dir, f"{output_name}_hillshade.tif")

        # Start task
        self._current_task = DEMProcessTask(
            plugin=self,
            description="Download, mosaic, clip & hillshade",
            lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max,
            tile_dir=tile_dir, output_dem=output_dem, output_hs=output_hs
        )

        self._current_task.progressChanged.connect(
            lambda p: self.dlg.progress_bar.setValue(int(p))
        )
        QgsApplication.taskManager().addTask(self._current_task)
        self.lbl_progress = self.dlg.lbl_progress

    def on_cancel_clicked(self):
        if self._current_task:
            try:
                if self._current_task.isActive():
                    self._current_task.cancel()
                    self.lbl_progress.setText("Cancelled")
            except RuntimeError:
                self.lbl_progress.setText("Task already finished")
        self.dlg.close()

################################# DEM EXPORT - TOPOGRAPHY MAP ################################################

    def export_dem_map(self, dem_path, output_path):

        # --- Load DEM ---
        with rasterio.open(dem_path) as src:
            dem = src.read(1, masked=True)  # masked DEM
            profile = src.profile
            extent = [src.bounds.left, src.bounds.right,
                    src.bounds.bottom, src.bounds.top]
            height, width = src.height, src.width

        # --- Convert to plain array + build mask ---
        arr = np.array(dem.filled(0), dtype="float32")

        if dem.mask.shape == ():  # scalar mask
            mask = np.zeros_like(arr, dtype="uint8")
            if dem.mask:
                mask[:] = 1
        else:
            mask = dem.mask.astype("uint8")

        # --- Fill NoData robustly ---
        dem_filled = fillnodata(arr, mask=mask,
                                max_search_distance=100,
                                smoothing_iterations=2)

        # --- Save filled DEM as GeoTIFF ---
        filled_tif = output_path.replace("_topography_map.png", "_Dem_filled.tif")
        profile.update(dtype="float32", nodata=None)

        with rasterio.open(filled_tif, "w", **profile) as dst:
            dst.write(dem_filled, 1)

        self.iface.messageBar().pushMessage(
            "Info", f"Saved filled DEM: {filled_tif}", level=Qgis.Info
        )

        # --- Compute min/max from filled DEM ---
        dem_min = float(np.nanmin(dem_filled[dem_filled > 0]))
        dem_max = float(np.nanmax(dem_filled))

        # --- Build colormap from QGIS ramp ---
        selected_ramp = self.dlg.cmb_colormap.currentText()
        style = QgsStyle().defaultStyle()
        ramp = style.colorRamp(selected_ramp)

        steps = 100
        qgis_colors = [ramp.color(i / steps) for i in range(steps + 1)]
        cmap = colors.ListedColormap(
            [(c.redF(), c.greenF(), c.blueF()) for c in qgis_colors]
        )

        norm = colors.Normalize(vmin=dem_min, vmax=dem_max)

        # --- Plot DEM ---
        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(dem_filled, cmap=cmap, norm=norm, extent=extent, origin="upper")

        # --- Hillshade overlay ---
        ls = LightSource(azdeg=315, altdeg=45)
        shaded = ls.shade(dem_filled, cmap=cmap, blend_mode="overlay", fraction=0.6)
        ax.imshow(shaded, extent=extent, origin="upper")

        # --- Legend ---
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("Elevation (m)")
        cbar.set_ticks(np.linspace(dem_min, dem_max, num=6))

        # --- Save PNG ---
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

#########################################################################################

# ------------------ DEMProcessTask CLASS ------------------

class DEMProcessTask(QgsTask):
    def __init__(self, plugin, description, lat_min, lat_max, lon_min, lon_max, tile_dir, output_dem, output_hs):
        super().__init__(description, QgsTask.CanCancel)
        self.plugin = plugin
        self.lat_min = float(lat_min)
        self.lat_max = float(lat_max)
        self.lon_min = float(lon_min)
        self.lon_max = float(lon_max)
        self.tile_dir = tile_dir
        self.output_dem = output_dem
        self.output_hs = output_hs
        self.exception = None
        self.base_url = "https://copernicus-dem-30m.s3.amazonaws.com"

        self.plugin_dir = os.path.dirname(__file__)

    def _tiles_for_bbox(self):
        tiles = []
        for lat in range(math.floor(self.lat_min), math.ceil(self.lat_max)):
            for lon in range(math.floor(self.lon_min), math.ceil(self.lon_max)):
                lat_prefix = "N" if lat >= 0 else "S"
                lon_prefix = "E" if lon >= 0 else "W"
                tile = f"Copernicus_DSM_COG_10_{lat_prefix}{abs(lat):02d}_00_{lon_prefix}{abs(lon):03d}_00_DEM"
                tiles.append(tile)
        return tiles

    def _download_tiles(self, tiles):
        total = len(tiles)
        for i, t in enumerate(tiles, start=1):
            if self.isCanceled():
                return False
            tif_path = os.path.join(self.tile_dir, f"{t}.tif")
            if not os.path.exists(tif_path):
                url = f"{self.base_url}/{t}/{t}.tif"
                try:
                    with requests.get(url, stream=True, timeout=120) as r:
                        r.raise_for_status()
                        with open(tif_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=1024 * 1024):
                                if self.isCanceled():
                                    return False
                                if chunk:
                                    f.write(chunk)
                except Exception as e:
                    self.exception = Exception(f"Download failed for {t}: {e}")
                    return False
            self.setProgress(int(40 * i / total))
        return True

    def run(self):
        try:
            tiles = self._tiles_for_bbox()
            if not self._download_tiles(tiles):
                return False

            tif_files = [os.path.join(self.tile_dir, f"{t}.tif") for t in tiles if os.path.exists(os.path.join(self.tile_dir, f"{t}.tif"))]
            vrt_path = os.path.join(self.tile_dir, "merged.vrt")
            gdal.BuildVRT(vrt_path, tif_files)
            gdal.Translate(self.output_dem, vrt_path, projWin=[self.lon_min, self.lat_max, self.lon_max, self.lat_min])
            gdal.DEMProcessing(self.output_hs, self.output_dem, "hillshade", azimuth=315, altitude=45, scale=1.0, zFactor=1.0)
            self.setProgress(70)
            return True
        except Exception as e:
            self.exception = e
            return False


    def finished(self, result):
        if result:
            self.plugin.lbl_progress.setText("Completed successfully")
            hs_layer = QgsRasterLayer(self.output_hs, "Hillshade")
            dem_layer = QgsRasterLayer(self.output_dem, "DEM")

            if hs_layer.isValid() and dem_layer.isValid():

                # --- Apply color ramp to DEM before adding it ---
                style = QgsStyle().defaultStyle()
                selected_ramp = self.plugin.dlg.cmb_colormap.currentText()
                ramp = style.colorRamp(selected_ramp)

                shader = QgsColorRampShader()
                shader.setColorRampType(QgsColorRampShader.Interpolated)

                stats = dem_layer.dataProvider().bandStatistics(1)
                items = []
                for i in range(0, 101):
                    val = stats.minimumValue + (i / 100.0) * (stats.maximumValue - stats.minimumValue)
                    color = ramp.color(i / 100.0)
                    items.append(QgsColorRampShader.ColorRampItem(val, color))

                shader.setColorRampItemList(items)

                raster_shader = QgsRasterShader()
                raster_shader.setRasterShaderFunction(shader)

                renderer = QgsSingleBandPseudoColorRenderer(dem_layer.dataProvider(), 1, raster_shader)
                dem_layer.setRenderer(renderer)
                dem_layer.triggerRepaint()

                # --- Add DEM to project ---
                QgsProject.instance().addMapLayer(dem_layer)

                # --- Hillshade ---
                hs_layer.renderer().setOpacity(0.3)  # keep grayscale but transparent
                hs_layer.triggerRepaint()
                QgsProject.instance().addMapLayer(hs_layer)
                

                # --- Layer order: DEM below, Hillshade above ---
                root = QgsProject.instance().layerTreeRoot()
                QgsProject.instance().layerTreeRoot().setHasCustomLayerOrder(True)
                QgsProject.instance().layerTreeRoot().setCustomLayerOrder([hs_layer, dem_layer])

                # --- Export PNG ---

                # Get user-given base name (without extension)
                base_name = os.path.splitext(os.path.basename(self.output_dem))[0].replace("_dem", "")

                map_png = os.path.join(self.plugin_dir, "outputs", f"{base_name}_topography_map.png")
                self.plugin.export_dem_map(self.output_dem, map_png)
                

                self.plugin.iface.messageBar().pushMessage(
                    "Info", f"Map exported: {map_png}", level=Qgis.Info
                )
                
        else:
            self.plugin.lbl_progress.setText(f"FAILED: Wrong input or {self.exception}")
