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
import shutil
import xml.etree.ElementTree as ET

from qgis.PyQt.QtCore import pyqtSignal, QCoreApplication
from qgis.PyQt.QtWidgets import QWidget

from qgis.core import (Qgis,
                       QgsProject,
                       QgsMapLayer,
                       QgsMessageLog,
                       QgsTask,
                       QgsRasterPipe,
                       QgsRasterRange,
                       QgsRasterNuller,
                       QgsRasterFileWriter,
                       QgsRasterDataProvider,
                       QgsVectorFileWriter,
                       QgsCoordinateTransformContext,
                      )

RASTER_SIZE = 2000
LAYERS_DIRECTORY = 'layers'
BAD_CHARS = re.compile(r'[&:\(\)\-\,\'\.\/ ]')


class WriterBase:

    def __init__(self):
        pass

    def name(self):
        return 'base'

    def displayName(self):
        return self.tr('Base')

    def widget(self):
        return QWidget()

    def task(self, settings):
        return WriterTaskBase(settings)

    def tr(self, text):
        return QCoreApplication.translate(self.__class__.__name__, text)


class WriterTaskBase(QgsTask):

    consolidateComplete = pyqtSignal()
    errorOccurred = pyqtSignal(str)

    def __init__(self, settings):
        QgsTask.__init__(self, 'QConsolidate')

        self.settings = settings

        self.project = None
        self.projectFile = None

        self.baseDirectory = self.settings['output']
        self.dataDirectory = os.path.join(self.baseDirectory, LAYERS_DIRECTORY)

        self.error = ''

    def run(self):
        if not os.path.isdir(self.dataDirectory):
            os.mkdir(self.dataDirectory)

        self.prepare()

        self.consolidateProject()

        layers = QgsProject.instance().mapLayers()
        total = 100.0 / len(layers)

        for count, layer in enumerate(layers.values()):
            QgsMessageLog.logMessage('Consolidating {layer}.'.format(layer=layer.name()), 'QConsolidate', Qgis.Info)
            if self.isCanceled():
                break

            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer:
                self.consolidateVectorLayer(layer)
            elif layerType == QgsMapLayer.RasterLayer:
                self.consolidateRasterLayer(layer)
            elif layerType == QgsMapLayer.PluginLayer:
                self.consolidatePluginLayer(layer)
            elif layerType == QgsMapLayer.MeshLayer:
                self.consolidateMeshLayer(layer)

            self.setProgress(int(count * total))

        self.project.write(self.projectFile)

        return self.cleanup()

    def finished(self, result):
        if result:
            self.consolidateComplete.emit()
        else:
            self.errorOccurred.emit(self.error)

    def prepare(self):
        pass

    def cleanup(self):
        return True

    def consolidateProject(self):
        projectFile = QgsProject.instance().fileName()
        fileName = os.path.basename(projectFile)
        if projectFile:
            shutil.copy(projectFile, self.baseDirectory)
            self.projectFile = os.path.join(self.baseDirectory, fileName)
        else:
            # FIXME: save project in temporary files?
            self.projectFile = os.path.join(self.baseDirectory, 'project.qgs')
            QgsProject.instance().write(self.projectFile)

        self.project = ET.parse(self.projectFile)

    def consolidateVectorLayer(self, layer):
        raise NotImplementedError('Needs to be implemented by subclasses.')

    def consolidateRasterLayer(self, layer):
        raise NotImplementedError('Needs to be implemented by subclasses.')

    def consolidatePluginLayer(self, layer):
        raise NotImplementedError('Needs to be implemented by subclasses.')

    def consolidateMeshLayer(self, layer):
        raise NotImplementedError('Needs to be implemented by subclasses.')

    def exportVectorLayer(self, layer, destinationFile, asLayer=False):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = self.settings['vectorFormat'] if 'vectorFormat' in self.settings else 'GPKG'
        options.fileEncoding = 'utf-8'
        if asLayer:
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            options.layerName = self.safeName(layer.name())
        else:
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

        if os.path.splitext(destinationFile)[1] == '':
            formats = QgsVectorFileWriter.supportedFiltersAndFormats()
            for f in formats:
                if f.driverName == options.driverName and len(f.globs) > 0:
                    destinationFile = '{}.{}'.format(destinationFile, f.globs[0][2:])

        success = True
        error, msg = QgsVectorFileWriter.writeAsVectorFormat(layer, destinationFile, options)
        if error != QgsVectorFileWriter.NoError:
            QgsMessageLog.logMessage(self.tr('Failed to export layer "{layer}": {message}.'.format(layer=layer.name(), message=msg)), 'QConsolidate', Qgis.Warning)
            success = False

        return success, destinationFile

    def exportRasterLayer(self, layer, destinationFile, options=None):
        outputFormat = self.settings['rasterFormat'] if 'rasterFormat' in self.settings else 'GTiff'

        if os.path.splitext(destinationFile)[1] == '':
            formats = QgsRasterFileWriter.extensionsForFormat(outputFormat)
            if len(formats) > 0:
                destinationFile = '{}.{}'.format(destinationFile, formats[0])

        provider = layer.dataProvider()

        cols = provider.xSize()
        rows = provider.ySize()
        if not provider.capabilities() & QgsRasterDataProvider.Size:
            k = float(provider.extent().width()) / float(provider.extent().height())
            cols = RASTER_SIZE * k
            rows = RASTER_SIZE

        pipe = QgsRasterPipe()
        if not pipe.set(provider.clone()):
            QgsMessageLog.logMessage(self.tr('Failed to export layer "{layer}": Cannot set pipe provider.'.format(layer=layer.name())), 'QConsolidate', Qgis.Warning)
            return False, None

        nodata = {}
        for i in range(1, provider.bandCount() + 1):
            if provider.sourceHasNoDataValue(i):
                value = provider.sourceNoDataValue(i)
                nodata[i] = QgsRasterRange(value, value)

        nuller = QgsRasterNuller()
        for band, value in nodata.items():
            nuller.setNoData(band, [value])

        if not pipe.insert(1, nuller):
            QgsMessageLog.logMessage(self.tr('Failed to export layer "{layer}": Cannot set pipe nuller.'.format(layer=layer.name())), 'QConsolidate', Qgis.Warning)
            return False, None

        writer = QgsRasterFileWriter(destinationFile)
        writer.setOutputFormat(outputFormat)

        if options is not None:
            writer.setCreateOptions(options)

        success = True
        error = writer.writeRaster(pipe, cols, rows, provider.extent(), provider.crs(), QgsCoordinateTransformContext())
        if error != QgsRasterFileWriter.NoError:
            QgsMessageLog.logMessage(self.tr('Failed to export layer "{layer}": {message}.'.format(layer=layer.name(), message=error)), 'QConsolidate', Qgis.Warning)
            success = False

        return success, destinationFile

    def exportStyle(self, layer, destination):
        layer.saveNamedStyle('{}.qml'.format(os.path.splitext(destination)[0]))

    def updateLayerSource(self, layerId, newSource, newProvider=None):
        # update layer source in the layer tree section.
        element = self.project.find('*//layer-tree-layer/[@id="{}"]'.format(layerId))
        element.set('source', newSource)
        if newProvider is not None:
            element.set('providerKey', newProvider)

        # update layer source in the project layers section
        element = self.project.find('./projectlayers/maplayer/[id="{}"]'.format(layerId))
        element.find('datasource').text = newSource
        if newProvider is not None:
            element.find('provider').text = newProvider

    def safeName(self, layerName):
        return BAD_CHARS.sub('', layerName).title().replace(' ', '')

    def layerTreePath(self, layer):
        layerPath = self.dataDirectory
        if 'groupLayers' in self.settings and self.settings['groupLayers']:
            groups = []
            root = QgsProject.instance().layerTreeRoot()
            node = root.findLayer(layer.id())
            while node.parent() is not None:
                groups.append(node.parent().name())
                node = node.parent()

            groups[-1] = LAYERS_DIRECTORY
            groups.reverse()

            layerPath = os.path.join(self.baseDirectory, *groups)

        return layerPath
