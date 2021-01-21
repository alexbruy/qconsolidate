# -*- coding: utf-8 -*-

"""
***************************************************************************
    copywriter.py
    ---------------------
    Date                 : April 2018
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
__date__ = 'April 2018'
__copyright__ = '(C) 2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import re
import glob
import shutil

from qgis.core import Qgis, QgsMessageLog, QgsDataSourceUri

from qconsolidate.writers.writerbase import WriterBase, WriterTaskBase
from qconsolidate.gui.directorywriterwidget import DirectoryWriterWidget

GDAL_VSI = re.compile(r'(\/vsi.*?\/)(\/?.*(\.zip|\.t?gz|\.tar))\/?(.*)')


class CopyWriter(WriterBase):

    def __init__(self):
        super(CopyWriter, self).__init__()

    def name(self):
        return 'copydirectory'

    def displayName(self):
        return self.tr('Copy to directory')

    def widget(self):
        return DirectoryWriterWidget()

    def task(self, settings):
        return CopyWriterTask(settings)


class CopyWriterTask(WriterTaskBase):

    def __init__(self, settings):
        super(CopyWriterTask, self).__init__(settings)

    def consolidateVectorLayer(self, layer):
        newPath = self.layerTreePath(layer)
        if not os.path.isdir(newPath):
            os.makedirs(newPath)

        exportLayer = False

        providerType = layer.providerType()
        if providerType == 'ogr':
            self._processGdalDatasource(layer, newPath)
        elif providerType in ('gpx', 'delimitedtext'):
            layerFile, layerName = self._filePathFromUri(layer.source())
            self._copyLayerFiles(layerFile, newPath)
            newDirectory = newPath.replace(self.baseDirectory, '.')
            newSource = '{dirName}/{fileName}?{layer}'.format(dirName=newDirectory, fileName=os.path.split(layerFile)[1], layer=layerName)
            self.updateLayerSource(layer.id(), newSource)
        elif providerType == 'spatialite':
            uri = QgsDataSourceUri(layer.source())
            layerFile = uri.database()
            self._copyLayerFiles(layerFile, newPath)
            newDirectory = newPath.replace(self.baseDirectory, '.')
            uri.setDatabase('./{dirName}/{fileName}'.format(dirName=newDirectory, fileName=os.path.split(layerFile)[1]))
            self.updateLayerSource(layer.id(), uri.uri())
        elif providerType == 'memory':
            exportLayer = True
        elif providerType in ('DB2', 'mssql', 'oracle', 'postgres', 'wfs'):
            if 'exportRemote' in self.settings and self.settings['exportRemote']:
                exportLayer = True
        else:
            QgsMessageLog.logMessage(self.tr('Layers from the "{provider}" provider are currently not supported.').format(provider=providerType), 'QConsolidate', Qgis.Info)

        if exportLayer:
            filePath = os.path.join(newPath, self.safeName(layer.name()))
            ok, filePath = self.exportVectorLayer(layer, filePath)
            if ok:
                newSource = filePath.replace(self.baseDirectory, '.')
                self.updateLayerSource(layer.id(), newSource, 'ogr')

    def consolidateRasterLayer(self, layer):
        newPath = self.layerTreePath(layer)
        if not os.path.isdir(newPath):
            os.makedirs(newPath)

        providerType = layer.providerType()
        if providerType == 'gdal':
            self._processGdalDatasource(layer, newPath)
        elif providerType in ('wms'):
            if 'exportRemote' in self.settings and self.settings['exportRemote']:
                filePath = os.path.join(newPath, self.safeName(layer.name()))
                ok, filePath = self.exportRasterLayer(layer, filePath)
                if ok:
                    newSource = filePath.replace(self.baseDirectory, '.')
                    self.updateLayerSource(layer.id(), newSource, 'gdal')
        else:
            QgsMessageLog.logMessage(self.tr('Layers from the "{provider}" provider are currently not supported.').format(provider=providerType), 'QConsolidate', Qgis.Info)

    def consolidatePluginLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Plugin layers are currently not supported.'), 'QConsolidate', Qgis.Info)

    def consolidateMeshLayer(self, layer):
        QgsMessageLog.logMessage(self.tr('Mesh layers are currently not supported.'), 'QConsolidate', Qgis.Info)

    def _processGdalDatasource(self, layer, destDirectory):
        uri = layer.source()
        filePath = layer.source()
        newDirectory = destDirectory.replace(self.baseDirectory, '.')
        newSource = '{dirName}/{fileName}'.format(dirName=newDirectory, fileName=os.path.split(filePath)[1])
        if uri.startswith(('/vsizip/', '/vsigzip/', '/vsitar/')):
            m = GDAL_VSI.search(uri)
            if m is not None:
                prefix = m.group(1)
                filePath = m.group(2)
                layerPath = m.group(4)
                newSource = '{vsi}{dirName}/{fileName}/{layer}'.format(vsi=prefix, dirName=newDirectory, fileName=os.path.split(filePath)[1], layer=layerPath)
            else:
                QgsMessageLog.logMessage(self.tr('Failed to parse URI: "{uri}"').format(uri=uri), 'QConsolidate', Qgis.Warning)
                return
        else:
            # ignore other virtual filesystems
            if uri.startswith('/vsi'):
                prefix = uri.slit('/')[0]
                QgsMessageLog.logMessage(self.tr('Not supported GDAL virtual filesystem layer "{layerType}"').format(layerType=prefix), 'QConsolidate', Qgis.Info)
                return

            # handle multiple layers in the single dataset
            if '|' in uri:
                filePath = uri.split('|')[0]
                layerPath = uri.split('|')[1]
                newSource = '{dirName}/{fileName}|{layer}'.format(dirName=newDirectory, fileName=os.path.split(filePath)[1], layer=layerPath)

        self._copyLayerFiles(filePath, destDirectory)
        self.updateLayerSource(layer.id(), newSource)

    def _copyLayerFiles(self, layerPath, destDirectory):
        ''' Copy all files that belongs to the layer to the given directory
        '''
        wildcard = '{}.*'.format(os.path.splitext(layerPath)[0])
        for fileName in glob.iglob(wildcard):
            shutil.copy2(fileName, destDirectory)

    def _filePathFromUri(self, uri):
        filePath = uri.split('?')[0]
        layerPath = uri.split('?')[1]
        if os.name == 'nt':
            # on Windows strip 'file:///' prefix from the path
            # FIXME: need to handle special case — LAN URI
            return (filePath[8:], layerPath) if filePath.startswith('file://') else (filePath, layerPath)
        else:
            # on Linux strip 'file://' prefix from the path
            return (filePath[7:], layerPath) if filePath.startswith('file://') else (filePath, layerPath)
