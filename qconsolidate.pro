SOURCES = __init__.py \
          qconsolidateplugin.py \
          gui/qconsolidatedialog.py \
          gui/aboutdialog.py \
          gui/directorywriterwidget.py \
          writers/writerbase.py \
          writers/copywriter.py \
          writers/exportwriter.py \
          writers/geopackagewriter.py \
          writers/spatialitewriter.py \
          writers/zipwriter.py

FORMS = ui/qconsolidatedialogbase.ui \
        ui/aboutdialogbase.ui \
        ui/directorywriterwidgetbase.ui

TRANSLATIONS = i18n/qconsolidate_fr.ts \
               i18n/qconsolidate_uk.ts
