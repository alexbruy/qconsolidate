# -*- coding: utf-8 -*-

"""
***************************************************************************
    writerbase.py
    ---------------------
    Date                 : March 2018
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
__date__ = 'March 2018'
__copyright__ = '(C) 2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import re
import glob
import shutil
import xml.etree.ElementTree as ET

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QWidget

from qgis.core import Qgis, QgsProject, QgsMapLayer, QgsMessageLog, QgsTask, QgsVectorFileWriter

RASTER_SIZE = 2000


class WriterBase:

    def name(self):
        return 'base'

    def displayName(self):
        return 'Base'

    def widget(self):
        return QWidget()

    def task(self, settings):
        return WriterTaskBase(settings)


class WriterTaskBase(QgsTask):

    consolidateComplete = pyqtSignal()
    errorOccurred = pyqtSignal(str)

    badChars = re.compile(r'[&:\(\)\-\,\'\.\/ ]')
    gdalVsi = re.compile(r'(\/vsi.*?\/)(\/?.*(\.zip|\.t?gz|\.tar))\/?(.*)')

    LAYERS_DIRECTORY = 'layers'

    def __init__(self, settings):
        QgsTask.__init__(self, 'QConsolidate {}'.format(settings['output']))

        self.settings = settings

        self.project = None
        self.projectFile = None

        self.error = ''
        self.dstDirectory = os.path.join(self.settings['output'], self.LAYERS_DIRECTORY)

    def run(self):
        self.packageProject()

        if not os.path.isdir(self.dstDirectory):
            os.mkdir(self.dstDirectory)

        layers = QgsProject.instance().mapLayers()
        total = 100.0 / len(layers)

        for count, layer in enumerate(layers.values()):
            QgsMessageLog.logMessage('Consolidating {layer}.'.format(layer=layer.name()), 'QConsolidate', Qgis.Info)
            if self.isCanceled():
                break

            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                self.packageVectorLayer(layer)
            elif layerType == QgsMapLayer.RasterLayer:
                self.packageRasterLayer(layer)
            elif layerType == QgsMapLayer.PluginLayer:
                self.packagePluginLayer(layer)

            self.setProgress(int(count * total))

        self.project.write(self.projectFile)

        return True

    def finished(self, result):
        if result:
            self.consolidateComplete.emit()
        else:
            self.errorOccurred.emit(self.error)

    def packageProject(self):
        projectFile = QgsProject.instance().fileName()
        fileName = os.path.basename(projectFile)
        if projectFile:
            shutil.copy(projectFile, self.settings['output'])
            self.projectFile = os.path.join(self.settings['output'], fileName)
        else:
            # FIXME: save project in temporary files?
            self.projectFile = os.path.join(self.settings['output'], 'project.qgs')
            QgsProject.instance().write(self.projectFile)

        self.project = ET.parse(self.projectFile)

    def packageVectorLayer(self, layer):
        raise NotImplementedError('Needs to be implemented by subclasses.')

    def packageRasterLayer(self, layer):
        raise NotImplementedError('Needs to be implemented by subclasses.')

    def packagePluginLayer(self, layer):
        raise NotImplementedError('Needs to be implemented by subclasses.')

    def _updateLayerSource(self, layerId, newSource, oldFilePath=None):
        if oldFilePath is None:
            # update layer source in the layer tree section.
            element = self.project.find('*//layer-tree-layer/[@id="{}"]'.format(layerId))
            element.set('source', newSource)

            # update layer source in the project layers section
            element = self.project.find('./projectlayers/maplayer/[id="{}"]'.format(layerId))
            element.find('datasource').text = newSource
        else:
            # update layer source in the layer tree section
            element = self.project.find('*//layer-tree-layer/[@id="{}"]'.format(layerId))
            source = element.get('source').lstrip('./')
            element.set('source', source.replace(oldFilePath, newSource))

            # update layer source in the project layers section
            element = self.project.find('./projectlayers/maplayer/[id="{}"]'.format(layerId))
            source = element.find('datasource').text.lstrip('./')
            element.find('datasource').text = source.replace(oldFilePath, newSource)

    def _copyLayerFiles(self, layerSource, destination):
        wildcard = '{}.*'.format(os.path.splitext(layerSource)[0])
        for fileName in glob.iglob(wildcard):
            shutil.copy2(fileName, destination)

    def _safeName(self, layerName):
        return self.badChars.sub('', layerName).title().replace(' ', '')

    def _filePathFromUri(self, uri):
        filePath = uri.split('?')[0]
        layerPath = uri.split('?')[1]
        if os.name == 'nt':
            # on Windows strip 'file:///' prefix from the path
            # FIXME: need to handle special case — LAN URI
            return filePath[8:] if filePath.startswith('file://') else filePath, layerPath
        else:
            # on Linux strip 'file://' prefix from the path
            return filePath[7:] if filePath.startswith('file://') else filePath, layerPath

    def _exportVectorLayer(self, layer, fileName, driverName='ESRI Shapefile'):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = driverName
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        options.fileEncoding = 'utf-8'
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, fileName, options)
        if error != QgsVectorFileWriter.NoError:
            QgsMessageLog.logMessage('Failed to process layer "{layer}": {message}.'.format(layer=layer.name(), message=error), 'QConsolidate')
        else:
            self._updateLayerSource(layer.id(), fileName)

    def _exportRasterLayer(self, layer, fileName):
        provider = layer.dataProvider()
        k = float(provider.extent().width()) / float(provider.extent().height())

        pipe = QgsRasterPipe()
        if not pipe.set(provider.clone()):
            QgsMessageLog.logMessage('Failed to process layer "{layer}": Cannot set pipe provider.'.format(layer=layer.name()), 'QConsolidate')
            return

        writer = QgsRasterFileWriter(fileName)
        writer.setOutputFormat('GTiff')
        writer.writeRaster(pipe, RASTER_SIZE * k, RASTER_SIZE, provider.extent(), provider.crs())
        self._updateLayerSource(layer.id(), fileName)