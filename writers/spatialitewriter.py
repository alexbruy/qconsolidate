# -*- coding: utf-8 -*-

"""
***************************************************************************
    spatialitewriter.py
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

from osgeo import ogr

from qgis.PyQt.QtWidgets import QWidget

from qgis.core import Qgis, QgsMessageLog, QgsDataSourceUri

from qconsolidate.writers.writerbase import WriterBase, WriterTaskBase


class SpatialiteWriterWidget(QWidget):

    def __init__(self):
        super(SpatialiteWriterWidget, self).__init__()

    def settings(self):
        config = dict()
        config['vectorFormat'] = 'SQLite'
        config['rasterFormat'] = 'SQLite'

        return config


class SpatialiteWriter(WriterBase):

    def __init__(self):
        super(SpatialiteWriter, self).__init__()

    def name(self):
        return 'spatialite'

    def displayName(self):
        return self.tr('SpatiaLite')

    def widget(self):
        return SpatialiteWriterWidget()

    def task(self, settings):
        return SpatialiteWriterTask(settings)


class SpatialiteWriterTask(WriterTaskBase):

    def __init__(self, settings):
        super(SpatialiteWriterTask, self).__init__(settings)

        self.filePath = os.path.join(self.dataDirectory, 'layers.sqlite')

    def prepare(self):
        driver = ogr.GetDriverByName('SQLite')
        if driver is None:
            self.error = self.tr('"SQLite" driver not found.')
            return False

        ds = driver.CreateDataSource(self.filePath, options=['SPATIALITE=YES'])
        if ds is None:
            self.error = self.tr('Failed to create database: {message}').format(message=gdal.GetLastErrorMsg())
            return False

        ds = None

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
            ok, filePath = self.exportVectorLayer(layer, self.filePath, True)
            if ok:
                uri = QgsDataSourceUri()
                uri.setDatabase(self.filePath.replace(self.baseDirectory, '.'))
                uri.setDataSource('', self.safeName(layer.name()), 'geometry')
                self.updateLayerSource(layer.id(), uri.uri(), 'spatialite')

    def consolidateRasterLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Raster layers are currently not supported.'), 'QConsolidate', Qgis.Info)
        #~ exportLayer = False

        #~ providerType = layer.providerType()
        #~ if providerType in ('gdal', 'grass'):
            #~ exportLayer = True
        #~ elif providerType in ('wms'):
            #~ if 'exportRemote' in self.settings and self.settings['exportRemote']:
                #~ exportLayer = True
        #~ else:
            #~ QgsMessageLog.logMessage(self.tr('Layers from the "{provider}" provider are currently not supported.'.format(provider=providerType)), 'QConsolidate', Qgis.Info)

        #~ if exportLayer:
            #~ tableName = self.safeName(layer.name())
            #~ ok, filePath = self.exportRasterLayer(layer, self.filePath, ['APPEND_SUBDATASET=YES', 'COVERAGE={table}'.format(table=tableName)])
            #~ if ok:
                #~ newSource = 'RASTERLITE2:{filePath}:{layer}'.format(filePath=self.filePath, layer=tableName)
                #~ self.updateLayerSource(layer.id(), newSource, 'gdal')

    def consolidatePluginLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Plugin layers are currently not supported.'), 'QConsolidate', Qgis.Info)

    def consolidateMeshLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Mesh layers are currently not supported.'), 'QConsolidate', Qgis.Info)
