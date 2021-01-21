# -*- coding: utf-8 -*-

"""
***************************************************************************
    exportwriter.py
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

from qgis.core import Qgis, QgsMessageLog

from qconsolidate.writers.writerbase import WriterBase, WriterTaskBase
from qconsolidate.gui.directorywriterwidget import DirectoryWriterWidget


class ExportWriter(WriterBase):

    def __init__(self):
        super(ExportWriter, self).__init__()

    def name(self):
        return 'exportdirectory'

    def displayName(self):
        return self.tr('Export to directory')

    def widget(self):
        return DirectoryWriterWidget()

    def task(self, settings):
        return ExportWriterTask(settings)


class ExportWriterTask(WriterTaskBase):

    def __init__(self, settings):
        super(ExportWriterTask, self).__init__(settings)

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
            newPath = self.layerTreePath(layer)
            if not os.path.isdir(newPath):
                os.makedirs(newPath)

            filePath = os.path.join(newPath, self.safeName(layer.name()))

            ok, filePath = self.exportVectorLayer(layer, filePath)
            if ok:
                newSource = filePath.replace(self.baseDirectory, '.')
                self.updateLayerSource(layer.id(), newSource, 'ogr')

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
            newPath = self.layerTreePath(layer)
            if not os.path.isdir(newPath):
                os.makedirs(newPath)

            filePath = os.path.join(newPath, self.safeName(layer.name()))

            ok, filePath = self.exportRasterLayer(layer, filePath)
            if ok:
                newSource = filePath.replace(self.baseDirectory, '.')
                self.updateLayerSource(layer.id(), newSource, 'gdal')

    def consolidatePluginLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Plugin layers are currently not supported.'), 'QConsolidate', Qgis.Info)

    def consolidateMeshLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Mesh layers are currently not supported.'), 'QConsolidate', Qgis.Info)
