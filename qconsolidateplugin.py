# -*- coding: utf-8 -*-

"""
***************************************************************************
    qconsolidateplugin.py
    ---------------------
    Date                 : February 2012
    Copyright            : (C) 2012-2018 by Alexander Bruy
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
__date__ = 'February 2012'
__copyright__ = '(C) 2012-2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsApplication

from qconsolidate.gui.qconsolidatedialog import QConsolidateDialog
from qconsolidate.gui.aboutdialog import AboutDialog

pluginPath = os.path.dirname(__file__)


class QConsolidatePlugin:
    def __init__(self, iface):
        self.iface = iface

        locale = QgsApplication.locale()
        qmPath = '{}/i18n/qconsolidate_{}.qm'.format(pluginPath, locale)

        if os.path.exists(qmPath):
            self.translator = QTranslator()
            self.translator.load(qmPath)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        self.actionRun = QAction(self.tr('QConsolidate'), self.iface.mainWindow())
        self.actionRun.setIcon(QIcon(os.path.join(pluginPath, 'icons', 'qconsolidate.svg')))
        self.actionRun.setObjectName('runQConsolidate')

        self.actionAbout = QAction(self.tr('About QConsolidate...'), self.iface.mainWindow())
        self.actionAbout.setIcon(QgsApplication.getThemeIcon('/mActionHelpContents.svg'))
        self.actionRun.setObjectName('aboutQConsolidate')

        self.iface.addPluginToMenu(self.tr('QConsolidate'), self.actionRun)
        self.iface.addPluginToMenu(self.tr('QConsolidate'), self.actionAbout)
        self.iface.addToolBarIcon(self.actionRun)

        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

        self.taskManager = QgsApplication.taskManager()

    def unload(self):
        self.iface.removePluginMenu(self.tr('QConsolidate'), self.actionRun)
        self.iface.removePluginMenu(self.tr('QConsolidate'), self.actionAbout)
        self.iface.removeToolBarIcon(self.actionRun)

    def run(self):
        dlg = QConsolidateDialog()
        if dlg.exec_():
            task = dlg.task()
            task.consolidateComplete.connect(self.completed)
            task.errorOccurred.connect(self.errored)

            self.taskManager.addTask(task)

    def about(self):
        d = AboutDialog()
        d.exec_()

    def tr(self, text):
        return QCoreApplication.translate('QConsolidatePlugin', text)

    def completed(self):
        self.iface.messageBar().pushSuccess(self.tr('QConsolidate'), self.tr('Project consolidated successfully.'))

    def errored(self, error):
        self.iface.messageBar().pushWarning(self.tr('QConsolidate'), error)
