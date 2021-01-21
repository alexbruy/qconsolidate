# -*- coding: utf-8 -*-

"""
***************************************************************************
    aboutdialog.py
    ---------------------
    Date                 : January 2018
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
__date__ = 'January 2018'
__copyright__ = '(C) 2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import configparser

from qgis.PyQt import uic
from qgis.PyQt.QtGui import QPixmap, QDesktopServices
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog

from qgis.core import QgsApplication

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(os.path.join(pluginPath, 'ui', 'aboutdialogbase.ui'))


class AboutDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(pluginPath, 'metadata.txt'))
        name = cfg['general']['name']
        about = cfg['general']['about']
        version = cfg['general']['version']
        icon = cfg['general']['icon']
        author = cfg['general']['author']
        home = cfg['general']['homepage']
        bugs = cfg['general']['tracker']

        self.setWindowTitle(self.tr('About {}').format(name))
        self.lblName.setText('<h1>{}</h1>'.format(name))

        self.lblLogo.setPixmap(QPixmap(os.path.join(pluginPath, *icon.split('/'))))
        self.lblVersion.setText(self.tr('Version: {}').format(version))

        self.textBrowser.setHtml(self.tr(
            '<p>{description}</p>'
            '<p><strong>Developers</strong>: {developer}</p>'
            '<p><strong>Homepage</strong>: <a href="{homepage}">{homepage}</a></p>'
            '<p>Please report bugs at <a href="{bugtracker}">bugtracker</a>.</p>').format(description=about,
                                                                                          developer=author,
                                                                                          homepage=self.home,
                                                                                          bugtracker=bugs))

        self.buttonBox.helpRequested.connect(self.openHelp)

    def openHelp(self):
        locale = QgsApplication.locale()

        if locale in ['uk']:
            QDesktopServices.openUrl(
                QUrl(self.home))
        else:
            QDesktopServices.openUrl(
                QUrl(self.home))
