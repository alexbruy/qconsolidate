# -*- coding: utf-8 -*-

"""
***************************************************************************
    zipwriter.py
    ---------------------
    Date                 : July 2018
    Copyright            : (C) 2018 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'July 2018'
__copyright__ = '(C) 2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import shutil
import tempfile

from osgeo import ogr

from qgis.PyQt.QtWidgets import QWidget

from qgis.core import Qgis, QgsMessageLog, QgsArchive

from qconsolidate.writers.writerbase import WriterBase, WriterTaskBase


class ZipWriterWidget(QWidget):

    def __init__(self):
        super(ZipWriterWidget, self).__init__()

    def settings(self):
        config = dict()
        config['vectorFormat'] = 'GPKG'
        config['rasterFormat'] = 'GPKG'

        return config


class ZipWriter(WriterBase):

    def __init__(self):
        super(ZipWriter, self).__init__()

    def name(self):
        return 'zip'

    def displayName(self):
        return self.tr('ZIP archive')

    def widget(self):
        return ZipWriterWidget()

    def task(self, settings):
        return ZipWriterTask(settings)


class ZipWriterTask(WriterTaskBase):

    def __init__(self, settings):
        super(ZipWriterTask, self).__init__(settings)

        self.filePath = os.path.join(self.dataDirectory, 'layers.zip')
        self.tempDir = os.path.join(tempfile.gettempdir(), 'qconsolidate')

    def prepare(self):
        self.archive = QgsArchive()

        if not os.path.isdir(self.tempDir):
            os.mkdir(self.tempDir)

    def cleanup(self):
        if not self.archive.zip(self.filePath):
            QgsMessageLog.logMessage(self.tr('Failed to zip layers.'), 'QConsolidate', Qgis.Warning)
            return False

        shutil.rmtree(self.tempDir)

        return True

    def consolidateVectorLayer(self, layer):
        exportLayer = False

        providerType = layer.providerType()
        if providerType in ('ogr', 'memory', 'gpx', 'delimitedtext', 'spatialite', 'grass'):
            exportLayer = True
        elif providerType in ('DB2', 'mssql', 'oracle', 'postgres', 'wfs'):
            if 'exportRemote' in self.settings and self.settings['exportRemote']:
                exportLayer = True
        else:
            QgsMessageLog.logMessage(self.tr('Layers from the "{provider}" provider are currently not supported.').format(provider=providerType), 'QConsolidate', Qgis.Info)

        if exportLayer:
            layerName = self.safeName(layer.name())
            tmpFile = os.path.join(self.tempDir, layerName)
            ok, filePath = self.exportVectorLayer(layer, tmpFile)
            if ok:
                newSource = '/vsizip/{filePath}/{layer}'.format(filePath=self.filePath.replace(self.baseDirectory, '.'), layer=os.path.split(filePath)[1])
                self.updateLayerSource(layer.id(), newSource, 'ogr')
                QgsMessageLog.logMessage('Add file {}'.format(filePath), 'QConsolidate')
                if filePath not in self.archive.files():
                    self.archive.addFile(filePath)

    def consolidateRasterLayer(self, layer):
        exportLayer = False

        providerType = layer.providerType()
        if providerType in ('gdal', 'grass'):
            exportLayer = True
        elif providerType in ('wms'):
            if 'exportRemote' in self.settings and self.settings['exportRemote']:
                exportLayer = True
        else:
            QgsMessageLog.logMessage(self.tr('Layers from the "{provider}" provider are currently not supported.').format(provider=providerType), 'QConsolidate', Qgis.Info)

        if exportLayer:
            layerName = self.safeName(layer.name())
            tmpFile = os.path.join(self.tempDir, layerName)
            ok, filePath = self.exportRasterLayer(layer, tmpFile)
            if ok:
                newSource = '/vsizip/{filePath}/{layer}'.format(filePath=self.filePath.replace(self.baseDirectory, '.'), layer=os.path.split(filePath)[1])
                self.updateLayerSource(layer.id(), newSource, 'gdal')
                QgsMessageLog.logMessage('Add file {}'.format(filePath), 'QConsolidate')
                if filePath not in self.archive.files():
                    self.archive.addFile(filePath)

    def consolidatePluginLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Plugin layers are currently not supported.'), 'QConsolidate', Qgis.Info)

    def consolidateMeshLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Mesh layers are currently not supported.'), 'QConsolidate', Qgis.Info)
