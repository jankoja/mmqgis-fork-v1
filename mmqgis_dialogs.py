# --------------------------------------------------------
#    mmqgis_dialogs - Dialog classes for mmqgis
#
#    begin                : 10 May 2010
#    copyright            : (c) 2009 - 2015 by Michael Minn
#    email                : See michaelminn.com
#
#   MMQGIS is free software and is offered without guarantee
#   or warranty. You can redistribute it and/or modify it 
#   under the terms of version 2 of the GNU General Public 
#   License (GPL v2) as published by the Free Software 
#   Foundation (www.gnu.org).
# --------------------------------------------------------

import csv
import os.path
import operator

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from mmqgis_library import *

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# --------------------------------------------------------
#    MC JJA Utility Functions
#		Features added:
#			Default setback added (assuming metric system)
#			Field name "number" changed to "numero" for db compatibility
#			Field name "name" for street changed to "str_name" for db compatibility
#
# --------------------------------------------------------

# --------------------------------------------------------
#    mmqgis_animate_columns - Create animations by
#		interpolating offsets from attributes
# --------------------------------------------------------

from mmqgis_animate_columns_form import *

class mmqgis_animate_columns_dialog(QDialog, Ui_mmqgis_animate_columns_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)

		QObject.connect(self.browseoutfile, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		for layer in iface.mapCanvas().layers():
			self.layername.addItem(layer.name())

		QObject.connect(self.layername, SIGNAL("currentIndexChanged(QString)"), self.set_column_options)

		self.set_column_options()
		self.outdirname.setText(os.getcwd() + "/frames")

	def set_column_options(self):
		self.latoffsetcol.clear()
		self.longoffsetcol.clear()

		if self.layername.currentIndex() >= 0:
			#print str(self.layername.currentIndex())
			layer = self.iface.mapCanvas().layer(self.layername.currentIndex())
			if layer.type() == QgsMapLayer.VectorLayer:
				for field in layer.dataProvider().fields().toList():
					#print "fields: " + str(index) + str(field.type())
					if field.type() in [ QVariant.Int, QVariant.Double ]:
						self.latoffsetcol.addItem(field.name())
						self.longoffsetcol.addItem(field.name())
						#if ("lat" in field.name().toLower()) and ("off" in field.name().toLower()):
						#	self.latoffsetcol.setCurrentIndex(self.latoffsetcol.count() - 1)
						#if ("lon" in field.name().toLower()) and ("off" in field.name().toLower()):
						#	self.longoffsetcol.setCurrentIndex(self.longoffsetcol.count() - 1)
						if ("lat" in field.name().lower()) and ("off" in field.name().lower()):
							self.latoffsetcol.setCurrentIndex(self.latoffsetcol.count() - 1)
						if ("lon" in field.name().lower()) and ("off" in field.name().lower()):
							self.longoffsetcol.setCurrentIndex(self.longoffsetcol.count() - 1)
						

        def browse_outfile(self):
		newname = QFileDialog.getExistingDirectory(None, "Output Frames Directory",
			self.outdirname.displayText())

		if newname != None:
                	self.outdirname.setText(newname)

	def run(self):
		layer = unicode(self.layername.currentText())
		latcol = unicode(self.latoffsetcol.currentText())
		longcol = unicode(self.longoffsetcol.currentText())
		outdir = unicode(self.outdirname.displayText())
		frame_count = int(self.durationframes.displayText())

		message = mmqgis_animate_columns(self.iface, layer, longcol, latcol, outdir, frame_count)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Animate Columns", message)

# --------------------------------------------------------
#    mmqgis_animate_lines - Create animations by
#		interpolating offsets from attributes
# --------------------------------------------------------

from mmqgis_animate_lines_form import *

class mmqgis_animate_lines_dialog(QDialog, Ui_mmqgis_animate_lines_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)

		QObject.connect(self.browseoutfile, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if (layer.type() == QgsMapLayer.VectorLayer) and \
			   ((layer.dataProvider().geometryType() == QGis.WKBLineString) or \
			    (layer.dataProvider().geometryType() == QGis.WKBLineString25D) or \
			    (layer.dataProvider().geometryType() == QGis.WKBMultiLineString) or \
			    (layer.dataProvider().geometryType() == QGis.WKBMultiLineString25D)):
				self.layername.addItem(layer.name())

		self.outdirname.setText(os.getcwd() + "/frames")

        def browse_outfile(self):
		newname = QFileDialog.getExistingDirectory(None, "Output Frames Directory",
			self.outdirname.displayText())

		if newname != None:
                	self.outdirname.setText(newname)

	def run(self):
		layer = unicode(self.layername.currentText())		
		fixed_speed = unicode(self.timing.currentText()) == "One Line Speed Determined By Longest Line"
		frame_count = int(self.durationframes.displayText())
		outdir = unicode(self.outdirname.displayText())

		message = mmqgis_animate_lines(self.iface, layer, fixed_speed, frame_count, outdir)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Animate Columns", message)

# --------------------------------------------------------
#    mmqgis_animate_rows - Create animations by
#		displaying successive rows
# --------------------------------------------------------

from mmqgis_animate_rows_form import *

class mmqgis_animate_rows_dialog(QDialog, Ui_mmqgis_animate_rows_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)

		QObject.connect(self.browseoutfile, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if layer.type() == QgsMapLayer.VectorLayer:
				self.layernames.addItem(layer.name())

		self.outdirname.setText(os.getcwd() + "/frames")

        def browse_outfile(self):
		newname = QFileDialog.getExistingDirectory(None, "Output Frames Directory",
			self.outdirname.displayText())

		if newname != None:
                	self.outdirname.setText(newname)

	def run(self):
		layers = []
		for x in range(0, self.layernames.count()):
			if self.layernames.item(x).isSelected():
				layers.append(self.layernames.item(x).text())

		# cumulative = self.cumulative.isChecked()
		outdir = unicode(self.outdirname.displayText())

		message = mmqgis_animate_rows(self.iface, layers, outdir)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Animate Rows", message)



# ----------------------------------------------------------
#    mmqgis_attribute_export - Export attributes to CSV file
# ----------------------------------------------------------

from mmqgis_attribute_export_form import *

class mmqgis_attribute_export_dialog(QDialog, Ui_mmqgis_attribute_export_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browseoutfile, SIGNAL("clicked()"), self.browse_outfiles)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_attributes)
		self.set_attributes()

		self.outfilename.setText(mmqgis_temp_file_name(".csv"))

        def browse_outfiles(self):
		newname = QFileDialog.getSaveFileName(None, "Output CSV File", 
			self.outfilename.displayText(), "CSV File (*.csv *.txt)")
                if newname != None:
                	self.outfilename.setText(newname)

	def set_attributes(self):
		self.attributes.clear()
		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer == None):
			return

		for index, field in enumerate(layer.dataProvider().fields()):
			self.attributes.addItem(field.name())

		#print self.locale().name()
		# print QSettings().allKeys()

		#print "Configured locale", QSettings().value("locale/userLocale")
		#print "Self Qt locale", unicode(self.locale().countryToString(self.locale().country()))
		#print "Self Qt decimal point: ", unicode(self.locale().decimalPoint())
		
		# Decimal mark is dependent on locale (comma instead of decimal point in Europe)
		# This doesn't use local override in settings (although it should)
		# Idiot check to make sure it's either a period or comma

		# QGIS configured country codes (locale/userLocale) are not
		# usable with python locale, so just use QLocale from user interface

		if (self.locale().decimalPoint() == '.'):
			self.decimalmark.setCurrentIndex(self.decimalmark.findText("(period)"))
			self.delimiter.setCurrentIndex(self.delimiter.findText("(comma)"))

		else:
			self.decimalmark.setCurrentIndex(self.decimalmark.findText("(comma)"))
			self.delimiter.setCurrentIndex(self.delimiter.findText("(semicolon)"))


		#if (layername[0] != '/') and (layername[0] != '\\'):
		#	self.outfilename.setText(os.getcwd() + "/" + layername + ".csv")
		#else:
		#	self.outfilename.setText(layername + ".csv")

	def run(self):
		layername = unicode(self.sourcelayer.currentText())
		outfilename = unicode(self.outfilename.displayText())

		delimiter = ","
		if unicode(self.delimiter.currentText()) == "(bar)":
			delimiter = "|"
		elif unicode(self.delimiter.currentText()) == "(space)":
			delimiter = " "
		elif unicode(self.delimiter.currentText()) == "(semicolon)":
			delimiter = ";"

		lineterminator = "\r\n"
		if unicode(self.lineterminator.currentText()) == "LF":
			lineterminator = "\n"

		decimal_mark = '.'
		if unicode(self.decimalmark.currentText()) == "(comma)":
			decimal_mark = ','

		# Compile a list and header of selected attributes
		attribute_names = []
		for x in range(0, self.attributes.count()):
			list_item = self.attributes.item(x)
			if list_item.isSelected():
				attribute_names.append(unicode(list_item.text()))

		#if len(attribute_names) <= 0:
		#	QMessageBox.critical(self.iface.mainWindow(), "Attribute Export", "No attributes selected")
		#	return

		message = mmqgis_attribute_export(self.iface, outfilename, layername, \
			attribute_names, delimiter, lineterminator, decimal_mark)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Attribute Export", message)

# --------------------------------------------------------
#    mmqgis_attribute_join - Join attributes from a CSV
#                            file to a shapefile
# --------------------------------------------------------

from mmqgis_attribute_join_form import *

class mmqgis_attribute_join_dialog(QDialog, Ui_mmqgis_attribute_join_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse_infile, SIGNAL("clicked()"), self.browse_infiles)
		QObject.connect(self.browse_outfile, SIGNAL("clicked()"), self.browse_outfiles)
		QObject.connect(self.browse_notfound, SIGNAL("clicked()"), self.browse_notfoundfiles)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.joinlayer, True)

		QObject.connect(self.joinlayer, SIGNAL("currentIndexChanged(QString)"), self.set_join_attributes)
		self.set_join_attributes()

		self.outfilename.setText(mmqgis_temp_file_name(".shp"))
		self.notfoundfilename.setText(os.getcwd() + "/notfound.csv")

        def browse_infiles(self):
		newname = QFileDialog.getOpenFileName(None, "Input CSV File", 
			self.infilename.displayText(), "CSV File (*.csv *.txt)")

                if newname:
			header = mmqgis_read_csv_header(self.iface, newname)
			if not header:
				return

			self.csvfilefield.clear()
			for field in header:
				self.csvfilefield.addItem(field)

			self.infilename.setText(newname)

        def browse_outfiles(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.outfilename.displayText(), "Shapefile (*.shp)")

                if newname != None:
                	self.outfilename.setText(newname)

        def browse_notfoundfiles(self):
		newname = QFileDialog.getSaveFileName(None, "Output Unjoined CSV File", 
			self.notfoundfilename.displayText(), "CSV File (*.csv *.txt)")
                if newname != None:
                	self.notfoundfilename.setText(newname)

	def set_join_attributes(self):
		self.joinlayerattribute.clear()
		layer = mmqgis_find_layer(self.joinlayer.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.joinlayerattribute.addItem(field.name())

	def run(self):
		layername = unicode(self.joinlayer.currentText())
		joinfield = unicode(self.csvfilefield.currentText())
		joinattribute = unicode(self.joinlayerattribute.currentText())
		infilename = unicode(self.infilename.displayText())
		outfilename = unicode(self.outfilename.displayText())
		notfoundname = unicode(self.notfoundfilename.displayText()).strip()

		message = mmqgis_attribute_join(self.iface, layername, infilename, joinfield, \
			joinattribute, outfilename, notfoundname, 1)
		if message != None:
			QMessageBox.critical(self.iface.mainWindow(), "Attribute Join", message)

# ---------------------------------------------------------
#    mmqgis_buffers - Create buffer polygons
# ---------------------------------------------------------

from mmqgis_buffers_form import *

# These globals are a kludge to give search term persistence.
# This should probably be implemented in Qt with a static
# dialog and multiple exec(), but that is undocumented behavior
# that might break on Windoze.

mmqgis_buffers_radius = 5
mmqgis_buffers_radiusunit = 1 # miles
mmqgis_buffers_buffershape = 0 # rounded

class mmqgis_buffers_dialog(QDialog, Ui_mmqgis_buffers_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)
		
		self.radius.setText(unicode(mmqgis_buffers_radius))
		self.radiusunit.addItems(["Feet","Miles","Meters","Kilometers"])
		self.radiusunit.setCurrentIndex(mmqgis_buffers_radiusunit)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.layer_changed)
		if self.sourcelayer.count() > 0:
			self.layer_changed()

		self.filename.setText(mmqgis_temp_file_name(".shp"))

	def layer_changed(self):
		self.radiusattribute.clear()
		layer = mmqgis_find_layer(unicode(self.sourcelayer.currentText()))
		if (layer == None):
			return

		self.radiusattribute.addItem("(fixed)")
		for index, field in enumerate(layer.dataProvider().fields()):
			self.radiusattribute.addItem(field.name())
		self.radiusattribute.setCurrentIndex(0)

		if (layer.dataProvider().geometryType() == QGis.WKBPoint) or \
		   (layer.dataProvider().geometryType() == QGis.WKBPoint25D) or \
		   (layer.dataProvider().geometryType() == QGis.WKBMultiPoint) or \
		   (layer.dataProvider().geometryType() == QGis.WKBMultiPoint25D):
			self.buffershape.clear()
			self.buffershape.addItems(["Circle","Triangle","Diamond","Pentagon","Hexagon"])
			if mmqgis_buffers_buffershape < self.buffershape.count():
				self.buffershape.setCurrentIndex(mmqgis_buffers_buffershape)
			else:
				self.buffershape.setCurrentIndex(0)
			self.buffershape.setEnabled(True)

		elif (layer.dataProvider().geometryType() == QGis.WKBLineString) or \
		     (layer.dataProvider().geometryType() == QGis.WKBLineString25D) or \
		     (layer.dataProvider().geometryType() == QGis.WKBMultiLineString) or \
		     (layer.dataProvider().geometryType() == QGis.WKBMultiLineString25D):
			self.buffershape.clear()
			self.buffershape.addItems(["Rounded", "Flat End", "North Side", \
				"East Side", "South Side", "West Side"])
			if mmqgis_buffers_buffershape < self.buffershape.count():
				self.buffershape.setCurrentIndex(mmqgis_buffers_buffershape)
			else:
				self.buffershape.setCurrentIndex(0)
			self.buffershape.setEnabled(True)

		else:
			self.buffershape.clear()
			self.buffershape.addItems(["Rounded"])
			if mmqgis_buffers_buffershape < self.buffershape.count():
				self.buffershape.setCurrentIndex(mmqgis_buffers_buffershape)
			else:
				self.buffershape.setCurrentIndex(0)
			self.buffershape.setEnabled(False)



        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def run(self):
		global mmqgis_buffers_radius
		global mmqgis_buffers_radiusunit
		global mmqgis_buffers_buffershape

		shape = self.buffershape.currentText()
		unit = unicode(self.radiusunit.currentText())
		radius = unicode(self.radiusattribute.currentText())
		layername = unicode(self.sourcelayer.currentText())
		selectedonly = self.selectedonly.isChecked()
		mmqgis_buffers_radiusunit = self.radiusunit.currentIndex()
		mmqgis_buffers_buffershape = self.buffershape.currentIndex()

		if radius == "(fixed)":
			try:
				mmqgis_buffers_radius = float(self.radius.displayText())
			except:
				QMessageBox.critical(self.iface.mainWindow(), "Create Buffers", 
					"Invalid radius number format: " + unicode(self.radius.displayText()))
				return None
		else:
			mmqgis_buffers_radius = radius

		savename = unicode(self.filename.displayText()).strip()

		message = mmqgis_buffers(self.iface, layername, mmqgis_buffers_radius, unit, 
			shape, savename, selectedonly, True)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Create Buffers", message)

# --------------------------------------------------------
#    mmqgis_color_ramp - Robust layer coloring
# --------------------------------------------------------

from mmqgis_color_ramp_form import *

class mmqgis_color_ramp_dialog(QDialog, Ui_mmqgis_color_ramp_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.lowcolor, SIGNAL("clicked()"), self.select_color)
		QObject.connect(self.midcolor, SIGNAL("clicked()"), self.select_color)
		QObject.connect(self.highcolor, SIGNAL("clicked()"), self.select_color)
		QObject.connect(self.outlinecolor, SIGNAL("clicked()"), self.select_color)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		self.preset.addItems(["Red - Green", "Green - Red", "Red - Yellow", "Yellow - Red",
			"Blue - Brown", "Brown - Blue", "Purple - Green", "Green - Purple", 
			"Red - Green - Blue", "Blue - Green - Red", "Cyan - Magenta - Yellow"])
		QObject.connect(self.preset, SIGNAL("currentIndexChanged(QString)"), self.set_color_preset)
		self.preset.setCurrentIndex(0)

		self.ramptype.addItems(["Quantiles", "Linear", "Logarithmic", "Exponential", 
			"Square Root", "Squared", "Discrete"])
		self.symboltype.addItems(["Mixed", "Circle", "Square", "Rectangle", "Diamond", 
			"Pentagon", "Triangle", "Star", "Arrow"])

		self.symbolsize.addItems([str(i) for i in range(1, 8)])
		self.symbolsize.setCurrentIndex(4)
		
		self.thickness.addItems([str(i) for i in ([0, 0.25, 0.5] + range(1, 6))])
		self.thickness.setCurrentIndex(0)

		self.categories.addItems([str(i) for i in range(3, 8)])
		self.categories.setCurrentIndex(2)
		
		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			self.layername.addItem(layer.name())

		for index, layer in enumerate(self.iface.legendInterface().selectedLayers()):
			selection = self.layername.findText(layer.name())
			if selection >= 0:
				self.layername.setCurrentIndex(selection)
				break;

		QObject.connect(self.layername, SIGNAL("currentIndexChanged(QString)"), self.set_band_names)
		self.set_band_names()

		QObject.connect(self.bandname, SIGNAL("currentIndexChanged(QString)"), self.set_band_options)
		self.set_band_options()

        def select_color(self):
		button = self.sender()
		button_color = button.palette().color(QPalette.Normal, QPalette.Button)
		button_color = QColorDialog.getColor(button_color)
		print button_color
		if button_color.isValid():
			button.setStyleSheet("* { background-color: " + button_color.name() + " }");

	def set_color_preset(self):
		name = unicode(self.preset.currentText())
		if name == "Red - Green":
			self.lowcolor.setStyleSheet("* { background-color: #aa0000 }");
			self.midcolor.setStyleSheet("* { background-color: #ffff00 }");
			self.highcolor.setStyleSheet("* { background-color: #55aa00 }");
		elif name == "Green - Red":
			self.lowcolor.setStyleSheet("* { background-color: #55aa00 }");
			self.midcolor.setStyleSheet("* { background-color: #ffff00 }");
			self.highcolor.setStyleSheet("* { background-color: #aa0000 }");
		elif name == "Red - Yellow":
			self.lowcolor.setStyleSheet("* { background-color: #ff0000 }");
			self.midcolor.setStyleSheet("* { background-color: #ff8000 }");
			self.highcolor.setStyleSheet("* { background-color: #ffff00 }");
		elif name == "Yellow - Red":
			self.lowcolor.setStyleSheet("* { background-color: #ffff00 }");
			self.midcolor.setStyleSheet("* { background-color: #ff8000 }");
			self.highcolor.setStyleSheet("* { background-color: #ff0000 }");
		elif name == "Blue - Brown":
			self.lowcolor.setStyleSheet("* { background-color: #346666 }");
			self.midcolor.setStyleSheet("* { background-color: #c9c865 }");
			self.highcolor.setStyleSheet("* { background-color: #6e462d }");
		elif name == "Brown - Blue":
			self.lowcolor.setStyleSheet("* { background-color: #6e462d }");
			self.midcolor.setStyleSheet("* { background-color: #c9c865 }");
			self.highcolor.setStyleSheet("* { background-color: #346666 }");
		elif name == "Purple - Green":
			self.lowcolor.setStyleSheet("* { background-color: #5f309c }");
			self.midcolor.setStyleSheet("* { background-color: #fcfbbd }");
			self.highcolor.setStyleSheet("* { background-color: #147a0b }");
		elif name == "Green - Purple":
			self.highcolor.setStyleSheet("* { background-color: #5f309c }");
			self.midcolor.setStyleSheet("* { background-color: #fcfbbd }");
			self.lowcolor.setStyleSheet("* { background-color: #147a0b }");
		elif name == "Blue - Green - Red":
			self.lowcolor.setStyleSheet("* { background-color: #0000ff }");
			self.midcolor.setStyleSheet("* { background-color: #00ff00 }");
			self.highcolor.setStyleSheet("* { background-color: #ff0000 }");
		elif name == "Red - Green - Blue":
			self.lowcolor.setStyleSheet("* { background-color: #ff0000 }");
			self.midcolor.setStyleSheet("* { background-color: #00ff00 }");
			self.highcolor.setStyleSheet("* { background-color: #0000ff }");
		elif name == "Cyan - Magenta - Yellow":
			self.lowcolor.setStyleSheet("* { background-color: #00ffff }");
			self.midcolor.setStyleSheet("* { background-color: #ff00ff }");
			self.highcolor.setStyleSheet("* { background-color: #ffff00 }");
				
	def set_band_names(self):
		# print "set_band_names(): " + unicode(self.layername.currentText())
		self.bandname.clear()
		layer = mmqgis_find_layer(unicode(self.layername.currentText()))
		if layer == None:
			return

		if layer.type() == QgsMapLayer.RasterLayer:
			for x in range(1, layer.bandCount() + 1):
				self.bandname.addItem(layer.bandName(x))

		elif layer.type() == QgsMapLayer.VectorLayer:
			for field in layer.dataProvider().fields().toList():
				self.bandname.addItem(field.name())

	def set_band_options(self):
		# print "set_band_options()"
		if len(self.bandname.currentText()) <= 0:
			return

		layer = mmqgis_find_layer(unicode(self.layername.currentText()))
		if (layer == None):
			return

		if layer.type() == QgsMapLayer.RasterLayer:
			self.ramptype.setCurrentIndex(0)
			self.ramptype.setEnabled(True)
			self.categories.setEnabled(True)
			self.symbolsize.setEnabled(False)
			self.symboltype.setEnabled(False)
			self.thickness.setEnabled(False)

		elif layer.type() == QgsMapLayer.VectorLayer:
			#print "1 " + unicode(self.bandname.currentText())
			field = layer.dataProvider().fields().field(unicode(self.bandname.currentText()))
			if (layer.dataProvider().geometryType() == QGis.WKBPoint) or \
			   (layer.dataProvider().geometryType() == QGis.WKBMultiPoint):
				self.symbolsize.setEnabled(True)
				self.symboltype.setEnabled(True)
				self.thickness.setEnabled(True)
				self.thickness.setCurrentIndex(1)
			else: # Line / Polygon
				self.symbolsize.setEnabled(False)
				self.symboltype.setEnabled(False)
				self.thickness.setEnabled(True)
				self.thickness.setCurrentIndex(1)

			if ((field.type() == QVariant.Double) or
			    (field.type() == QVariant.Int) or
			    (field.type() == QVariant.UInt)):
				self.ramptype.setCurrentIndex(0)
				self.ramptype.setEnabled(True)
				self.categories.setEnabled(True)

			else: # Non-scalars can only be discrete
				self.ramptype.setCurrentIndex(6)
				self.ramptype.setEnabled(False)
				self.categories.setEnabled(False)

	def run(self):
		message = mmqgis_set_color_ramp(self.iface,
			unicode(self.layername.currentText()),
			unicode(self.bandname.currentText()), 
			unicode(self.ramptype.currentText()), 
			unicode(self.symboltype.currentText()).lower(),
			float(self.symbolsize.currentText()),
			float(self.thickness.currentText()),
			int(self.categories.currentText()),
			int(self.lowcolor.palette().color(QPalette.Normal, QPalette.Button).rgb()),
			int(self.midcolor.palette().color(QPalette.Normal, QPalette.Button).rgb()),
			int(self.highcolor.palette().color(QPalette.Normal, QPalette.Button).rgb()),
			int(self.outlinecolor.palette().color(QPalette.Normal, QPalette.Button).rgb()))
		# "hard:" + unicode(self.symboltype.currentText()).lower(),

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Color Ramp", message)

# ---------------------------------------------------------------
#    mmqgis_delete_columns - Delete columns and save to shapefile
# ---------------------------------------------------------------

from mmqgis_delete_columns_form import *

class mmqgis_delete_columns_dialog(QDialog, Ui_mmqgis_delete_columns_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_fieldnames)

		self.set_fieldnames()

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_fieldnames(self):
		self.fieldnames.clear()
		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.fieldnames.addItem(field.name())

	def run(self):
		layername = unicode(self.sourcelayer.currentText())
		savename = unicode(self.filename.displayText()).strip()

		attributes = []
		for x in range(0, self.fieldnames.count()):
			if self.fieldnames.item(x).isSelected():
				attributes.append(self.fieldnames.item(x).text())

		message = mmqgis_delete_columns(self.iface, layername, attributes, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Delete Columns", message)


# --------------------------------------------------------
#    mmqgis_delete_duplicate_geometries - Save to shaperile
#			while removing duplicate shapes
# --------------------------------------------------------

from mmqgis_delete_duplicate_form import *

class mmqgis_delete_duplicate_dialog(QDialog, Ui_mmqgis_delete_duplicate_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		layername = unicode(self.sourcelayer.currentText())

		message = mmqgis_delete_duplicate_geometries(self.iface, layername, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Delete Duplicate Geometries", message)

# ---------------------------------------------------------
#    mmqgis_float_to_text - Change text fields to numbers
# ---------------------------------------------------------

from mmqgis_float_to_text_form import *

class mmqgis_float_to_text_dialog(QDialog, Ui_mmqgis_float_to_text_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_fieldnames)

		self.set_fieldnames()

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_fieldnames(self):
		self.fieldnames.clear()
		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			if (field.type() == QVariant.Double) or (field.type() == QVariant.Int):
				self.fieldnames.addItem(field.name())
				self.fieldnames.item(self.fieldnames.count() - 1).setSelected(1)

	def run(self):
		layername = unicode(self.sourcelayer.currentText())
		savename = unicode(self.filename.displayText()).strip()

		if unicode(self.separator.currentText()) == "Comma":
			separator = ','
		elif unicode(self.separator.currentText()) == "Space":
			separator = ' '
		else:
			separator = None

		decimals = self.decimals.currentIndex()
		prefix = unicode(self.prefix.text())
		suffix = unicode(self.suffix.text())

		attributes = []
		for x in range(0, self.fieldnames.count()):
			if self.fieldnames.item(x).isSelected():
				attributes.append(self.fieldnames.item(x).text())

		message = mmqgis_float_to_text(self.iface, layername, attributes, separator, 
			decimals, prefix, suffix, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Float to Text", message)


# --------------------------------------------------------
#    mmqgis_geometry_convert - Convert geometries to
#		simpler types
# --------------------------------------------------------

from mmqgis_geometry_convert_form import *

class mmqgis_geometry_convert_dialog(QDialog, Ui_mmqgis_geometry_convert_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		self.mergeattop.addItems(["First", "Sum"])

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_geometry_types)
		QObject.connect(self.newgeometry, SIGNAL("currentIndexChanged(QString)"), self.set_merge_fields)

		self.set_geometry_types()

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_geometry_types(self):
		newtypes = []
		layername = self.sourcelayer.currentText()
		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			# print layername + " =? " + layer.name() + ": " + str(layer.dataProvider().geometryType())

			if layer.name() == layername:
				if layer.dataProvider().geometryType() == QGis.WKBPoint:
					self.oldgeometry.setText("Type: Point")
					newtypes = ["Multipoints"]

				elif layer.dataProvider().geometryType() == QGis.WKBPoint25D:
					self.oldgeometry.setText("Type: Point 2.5D")
					newtypes = ["Points", "Multipoints"]

				elif layer.dataProvider().geometryType() == QGis.WKBLineString:
					self.oldgeometry.setText("Type: Linestrings")
					# Multi-linestring layers have a geometry type of WKBLineString,
					# so a linestring option must be provided and no
					# multilinestring option is possible
					newtypes = ["Centroids", "Nodes", "Linestrings", "Multilinestrings"]

				elif layer.dataProvider().geometryType() == QGis.WKBLineString25D:
					self.oldgeometry.setText("Type: Linestring 2.5D")
					newtypes = ["Centroids", "Nodes", "Linestrings", "Multilinestrings"]

				elif layer.dataProvider().geometryType() == QGis.WKBPolygon:
					self.oldgeometry.setText("Type: Polygon")
					newtypes = ["Centroids", "Nodes", "Linestrings", "Polygons", "Multipolygons"]

				elif layer.dataProvider().geometryType() == QGis.WKBPolygon25D:
					self.oldgeometry.setText("Type: Polygon 2.5D")
					newtypes = ["Centroids", "Nodes", "Linestrings", "Polygons", "Multipolygons"] 

				elif layer.dataProvider().geometryType() == QGis.WKBMultiPoint:
					self.oldgeometry.setText("Type: Multipoint")
					newtypes = ["Points", "Centroids"]

				elif layer.dataProvider().geometryType() == QGis.WKBMultiPoint25D:
					self.oldgeometry.setText("Type: Multipoint 2.5D")
					newtypes = ["Points", "Centroids"]

				elif layer.dataProvider().geometryType() == QGis.WKBMultiLineString:
					self.oldgeometry.setText("Type: Multilinestring")
					newtypes = ["Centroids", "Nodes", "Linestrings"]

				elif layer.dataProvider().geometryType() == QGis.WKBMultiLineString25D:
					self.oldgeometry.setText("Type: Multilinestring 2.5D")
					newtypes = ["Centroids", "Nodes", "Linestrings", "Multilinestrings"]

				elif layer.dataProvider().geometryType() == QGis.WKBMultiPolygon:
					self.oldgeometry.setText("Type: Multilinestring")
					newtypes = ["Centroids", "Nodes", "Multilinestrings", "Polygons"] 

				elif layer.dataProvider().geometryType() == QGis.WKBMultiPolygon25D:
					self.oldgeometry.setText("Type: Multipolygon 2.5D")
					newtypes = ["Centroids", "Nodes", "Multilinestrings", "Polygons", "Multipolygons"]

		self.newgeometry.clear()
		self.newgeometry.addItems(newtypes)
		self.set_merge_fields()

	def set_merge_fields(self):
		self.mergefield.clear()
		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer == None):
			return

		oldgeometry = layer.dataProvider().geometryType()
		newgeometry = self.newgeometry.currentText()

		if ((oldgeometry == QGis.WKBPoint) and (newgeometry == "Multipoints")) or \
		   ((oldgeometry == QGis.WKBPoint25D) and (newgeometry == "Multipoints")) or \
		   ((oldgeometry == QGis.WKBLineString) and (newgeometry == "Multilinestrings")) or \
		   ((oldgeometry == QGis.WKBLineString25D) and (newgeometry == "Multilinestrings")) or \
		   ((oldgeometry == QGis.WKBPolygon) and (newgeometry == "Multipolygons")) or \
		   ((oldgeometry == QGis.WKBPolygon25D) and (newgeometry == "Multipolygons")):
			self.mergefield.clear()
			for index, field in enumerate(layer.dataProvider().fields()):
				self.mergefield.addItem(field.name())
			self.mergefield.setEnabled(True)
			self.mergeattop.setEnabled(True)

		else:
			self.mergefield.clear()
			self.mergefield.setEnabled(False)
			self.mergeattop.setEnabled(False)
		
	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		layername = unicode(self.sourcelayer.currentText())

		splitnodes = 0
		if self.newgeometry.currentText() == "Points":
			newtype = QGis.WKBPoint
			splitnodes = 1
		elif self.newgeometry.currentText() == "Centroids":
			newtype = QGis.WKBPoint
		elif self.newgeometry.currentText() == "Nodes":
			newtype = QGis.WKBPoint
			splitnodes = 1
		elif self.newgeometry.currentText() == "Linestrings":
			newtype = QGis.WKBLineString
		elif self.newgeometry.currentText() == "Polygons":
			newtype = QGis.WKBPolygon
		elif self.newgeometry.currentText() == "Multipoints":
			newtype = QGis.WKBMultiPoint
		elif self.newgeometry.currentText() == "Multilinestrings":
			newtype = QGis.WKBMultiLineString
		elif self.newgeometry.currentText() == "Multipolygons":
			newtype = QGis.WKBMultiPolygon
		else:
			newtype = QGis.WKBPoint

		if self.mergefield.isEnabled():
			mergefield = unicode(self.mergefield.currentText())
			mergeattop = unicode(self.mergeattop.currentText())
			message = mmqgis_geometry_to_multipart(self.iface, layername, mergefield, mergeattop, savename, 1)

		else:
			message = mmqgis_geometry_convert(self.iface, layername, newtype, splitnodes, savename, 1)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Label", message)


# --------------------------------------------------------
#    mmqgis_geometry_export - Import geometries from a
#			CSV files of nodes and attributes
#			into a shapefile
# --------------------------------------------------------

from mmqgis_geometry_export_form import *

class mmqgis_geometry_export_dialog(QDialog, Ui_mmqgis_geometry_export_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.nodebrowse, SIGNAL("clicked()"), self.browse_nodes)
		QObject.connect(self.attbrowse, SIGNAL("clicked()"), self.browse_attributes)
		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.check_layer_type)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		self.attfilename.setText(os.getcwd() + "/temp-attributes.csv")
		self.nodefilename.setText(os.getcwd() + "/temp-nodes.csv")

        def browse_nodes(self):
		newname = QFileDialog.getSaveFileName(None, "Output Nodes CSV File", 
			self.nodefilename.displayText(), "CSV File (*.csv *.txt)")

		if newname != None:
                	self.nodefilename.setText(newname)

        def browse_attributes(self):
		newname = QFileDialog.getSaveFileName(None, "Output Nodes CSV File", 
			self.attfilename.displayText(), "CSV File (*.csv *.txt)")

		if newname != None:
                	self.attfilename.setText(newname)

	def check_layer_type(self):
		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer != None) and (layer.type() == QgsMapLayer.VectorLayer):
			if (layer.geometryType() == QGis.Point):
				self.attbrowse.setEnabled(False)
				self.attfilename.setEnabled(False)
			else:
				self.attbrowse.setEnabled(True)
				self.attfilename.setEnabled(True)

	def run(self):
		delimiter = ","
		if unicode(self.delimiter.currentText()) == "(bar)":
			delimiter = "|"
		elif unicode(self.delimiter.currentText()) == "(space)":
			delimiter = " "

		lineterminator = "\r\n"
		if unicode(self.lineterminator.currentText()) == "LF":
			lineterminator = "\n"

		sourcelayer = self.sourcelayer.currentText()
		nodefilename = self.nodefilename.displayText()
		attributefilename = self.attfilename.displayText()

		message = mmqgis_geometry_export_to_csv(self.iface, sourcelayer, nodefilename, 
			attributefilename, delimiter, lineterminator)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Geometry Export", message)


# --------------------------------------------------------
#    mmqgis_geometry_import - Import geometries from a
#			CSV files of nodes and attributes
#			into a shapefile
# --------------------------------------------------------

from mmqgis_geometry_import_form import *

class mmqgis_geometry_import_dialog(QDialog, Ui_mmqgis_geometry_import_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.nodebrowse, SIGNAL("clicked()"), self.browse_nodes)
		QObject.connect(self.outfilebrowse, SIGNAL("clicked()"), self.browse_shapefile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		self.geometrytype.addItem("Point")
		self.geometrytype.addItem("Polyline")
		self.geometrytype.addItem("Polygon")

		self.outfilename.setText(mmqgis_temp_file_name(".shp"))

	def browse_nodes(self):
		newname = QFileDialog.getOpenFileName(None, "Input Nodes CSV File", 
			self.nodefilename.displayText(), "CSV File (*.csv *.txt)")

                if not newname:
			return

		header = mmqgis_read_csv_header(self.iface, newname)
		if not header:
			return

		self.longcol.clear()
		self.latcol.clear()
		self.shapeidcol.clear()
		for field in header:
			self.longcol.addItem(field)
			self.latcol.addItem(field)
			self.shapeidcol.addItem(field)

		for x in range(0, len(header)):
			if (header[x].lower() == "shapeid") or (header[x].lower() == 'shape_id'):
				self.shapeidcol.setCurrentIndex(x)
				break

		for x in range(0, len(header)):
			if (header[x].find("x") >= 0) or (header[x].find("X") >= 0) or (header[x].lower().find('lon') >= 0):
				self.longcol.setCurrentIndex(x)
				break

		for x in range(0, len(header)):
			if (header[x].find("y") >= 0) or (header[x].find("Y") >= 0) or (header[x].lower().find('lat') >= 0):
				self.latcol.setCurrentIndex(x)
				break


		#for x in range(self.shapeidcol.count()):
		#	if (unicode(self.shapeidcol.itemText(x)).lower() == "shapeid") or \
		#	   (unicode(self.shapeidcol.itemText(x)).lower() == "shape_id"):
		#		self.shapeidcol.setCurrentIndex(x)

		#for x in range(self.longcol.count()):
		#	if (unicode(self.longcol.itemText(x)).lower() == "x") or \
		#	   (unicode(self.longcol.itemText(x)).lower()[0:3] == "lon"):
		#		self.longcol.setCurrentIndex(x)

		#for x in range(self.latcol.count()):
		#	if (unicode(self.latcol.itemText(x)).lower() == "x") or \
		#	   (unicode(self.latcol.itemText(x)).lower()[0:3] == "lon"):
		#		self.latcol.setCurrentIndex(x)

		self.nodefilename.setText(newname)
		shapename = str(newname) # make copy or replace alters original
		shapename = shapename.replace(".csv", ".shp")
		shapename = shapename.replace(".CSV", ".shp")
		shapename = shapename.replace(".txt", ".shp")
		shapename = shapename.replace(".TXT", ".shp")
		if shapename == newname:
			shapename = unicode(shapename) + ".shp"
		self.outfilename.setText(shapename)


        def browse_shapefile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.outfilename.displayText(), "Shapefile (*.shp)")

                if newname != None:
                	self.outfilename.setText(newname)

	def run(self):
		message = mmqgis_geometry_import_from_csv(self.iface, unicode(self.nodefilename.displayText()), 
			unicode(self.longcol.currentText()), unicode(self.latcol.currentText()),
			unicode(self.shapeidcol.currentText()), unicode(self.geometrytype.currentText()),
			unicode(self.outfilename.displayText()), 1)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Geometry Import", message)


# --------------------------------------------------------
#    mmqgis_geocode_web_service - Geocode using Google Maps
# --------------------------------------------------------

from mmqgis_geocode_web_service_form import *

#pyqt4-dev-tools
#designer

class mmqgis_geocode_web_service_dialog(QDialog, Ui_mmqgis_geocode_web_service_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse_infile, SIGNAL("clicked()"), self.browse_infile_dialog)
		QObject.connect(self.browse_shapefile, SIGNAL("clicked()"), self.browse_shapefile_dialog)
		QObject.connect(self.browse_notfound, SIGNAL("clicked()"), self.browse_notfound_dialog)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)
		self.shapefilename.setText(mmqgis_temp_file_name(".shp"))
		self.notfoundfilename.setText(os.getcwd() + "/notfound.csv")

		self.servicename.clear()
		self.servicename.addItems(["Google Maps", "OpenStreetMap / Nominatim"])
		self.servicename.setCurrentIndex(0)

        def browse_infile_dialog(self):
		newname = QFileDialog.getOpenFileName(None, "Address CSV Input File", 
			self.infilename.displayText(), "CSV File (*.csv *.txt)")

                if newname:

			if len(newname) > 4:
				prefix = newname[:len(newname) - 4]
				self.shapefilename.setText(prefix + ".shp")
			else:
				self.shapefilename.setText(mmqgis_temp_file_name(".shp"))


			combolist = [self.addressfield, self.cityfield, self.statefield, self.countryfield]
			for box in combolist:
				box.clear()
				box.addItem("(none)")
				box.setCurrentIndex(0)
				
			header = mmqgis_read_csv_header(self.iface, newname)
			if header == None:
				return

			for index in range(0, len(header)):
				field = header[index]
				for box in combolist:
					box.addItem(field)

				if field.lower().find("addr") >= 0:
					self.addressfield.setCurrentIndex(index + 1)
				if field.lower().find("street") >= 0:
					self.addressfield.setCurrentIndex(index + 1)
				if field.lower().find("city") >= 0:
					self.cityfield.setCurrentIndex(index + 1)
				if field.lower().find("state") >= 0:
					self.statefield.setCurrentIndex(index + 1)
				if field.lower() == "st":
					self.statefield.setCurrentIndex(index + 1)
				if field.lower().find("province") >= 0:
					self.statefield.setCurrentIndex(index + 1)
				if field.lower().find("country") >= 0:
					self.countryfield.setCurrentIndex(index + 1)

                	self.infilename.setText(newname)

        def browse_notfound_dialog(self):
		newname = QFileDialog.getSaveFileName(None, "Not Found List Output File", 
			self.notfoundfilename.displayText(), "CSV File (*.csv *.txt)")
                if newname != None:
                	self.notfoundfilename.setText(newname)

        def browse_shapefile_dialog(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.shapefilename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.shapefilename.setText(newname)

	def run(self):
		csvname = unicode(self.infilename.displayText()).strip()
		shapefilename = unicode(self.shapefilename.displayText())
		notfoundfile = self.notfoundfilename.displayText()
		service = unicode(self.servicename.currentText()).strip()

		fields = [unicode(self.addressfield.currentText()).strip(),
			  unicode(self.cityfield.currentText()).strip(),
			  unicode(self.statefield.currentText()).strip(),
			  unicode(self.countryfield.currentText()).strip()]
	
		for x in range(0, len(fields)):
			if fields[x] == "(none)":
				fields[x] = ""

		# print csvname + "," + "," + shapefilename
		message = mmqgis_geocode_web_service(self.iface, csvname, 
			shapefilename, notfoundfile, fields, service, 1)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Web Service Geocode", message)

# --------------------------------------------------------
#    mmqgis_grid - Grid creation plugin
# --------------------------------------------------------

from mmqgis_grid_form import *

class mmqgis_grid_dialog(QDialog, Ui_mmqgis_grid_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.hspacing, SIGNAL("textEdited(QString)"), self.hspacing_changed)
		QObject.connect(self.vspacing, SIGNAL("textEdited(QString)"), self.vspacing_changed)
		QObject.connect(self.gridtype, SIGNAL("currentIndexChanged(QString)"), self.gridtype_changed)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		self.crs = QgsCoordinateReferenceSystem()
		self.crs.createFromProj4("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
		extent = QgsRectangle (-10.0, -10.0, 10.0, 20.0)

		# Done as exception handler to make backward compatible from "crs" functions new to qgis 1.7 and 2.0
		# if (self.iface.mapCanvas() != None) and (self.iface.mapCanvas().mapRenderer() != None):
		try:
			self.crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
			extent = self.iface.mapCanvas().mapRenderer().extent()

		#elif self.iface.activeLayer() != None:
		except:
			try:
				extent = self.iface.activeLayer().extent()
				self.crs = self.iface.activeLayer().crs()
			except:
				extent = extent

		centerx = mmqgis_round((extent.xMinimum() + extent.xMaximum()) / 2, 4)
		centery = mmqgis_round((extent.yMinimum() + extent.yMaximum()) / 2, 4)

		self.xtype.setCurrentIndex(1);
		self.ytype.setCurrentIndex(1);
		self.xvalue.setText(unicode(centerx))
		self.yvalue.setText(unicode(centery))

		width = mmqgis_round(extent.width(), 4)
		height = mmqgis_round(extent.height(), 4)

		self.width.setText(unicode(width))
		self.height.setText(unicode(height))

		hspacing = 1
		if width > 0:
			hspacing = width / 10.0

		vspacing = 1
		if height > 0:
			vspacing = height / 10.0

		self.hspacing.setText(unicode(hspacing))
		self.vspacing.setText(unicode(vspacing))

		self.gridtype.addItem("Rectangle (line)")
		self.gridtype.addItem("Rectangle (polygon)")
		self.gridtype.addItem("Diamond (polygon)")
		self.gridtype.addItem("Hexagon (polygon)")
		self.gridtype.setCurrentIndex(0)

		self.filename.setText(os.getcwd() + "/grid.shp")
		

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def vspacing_changed(self, text):
		# Hexagonal grid must maintain fixed aspect ratio to make sense
		if unicode(self.gridtype.currentText()) == "Hexagon (polygon)":
			spacing = float(text)
			self.hspacing.setText(unicode(spacing * 0.866025403784439))

	def hspacing_changed(self, text):
		if unicode(self.gridtype.currentText()) == "Hexagon (polygon)":
			spacing = float(text)
			self.vspacing.setText(unicode(spacing / 0.866025))

	def gridtype_changed(self, text):
		if text == "Hexagon (polygon)":
			spacing = float(self.vspacing.displayText())
			self.hspacing.setText(unicode(spacing * 0.866025))

	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		try:
			hspacing = float(self.hspacing.displayText())
			vspacing = float(self.vspacing.displayText())
			width = float(self.width.displayText())
			height = float(self.height.displayText())
		except:
			QMessageBox.critical(self.iface.mainWindow(), "Grid", "Invalid dimension parameter")
			return

		originx = float(self.xvalue.displayText())
		if (str(self.xtype.currentText()) == "Center X") and (hspacing != 0):
			originx = originx - (round(width / 2.0 / hspacing) * hspacing)
		elif str(self.xtype.currentText()) == "Right X":
			originx = originx - width

		originy = float(self.yvalue.displayText())
		if (str(self.ytype.currentText()) == "Middle Y") and (vspacing != 0):
			originy = originy - (round(height / 2.0 / vspacing) * vspacing)
		elif str(self.ytype.currentText()) == "Top Y":
			originy = originy - height

		gridtype = unicode(self.gridtype.currentText())

		message = mmqgis_grid(self.iface, savename, hspacing, vspacing, width, height, originx, originy, gridtype, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Grid", message)



# --------------------------------------------------------
#    mmqgis_gridify - Snap shape verticies to grid
# --------------------------------------------------------

from mmqgis_gridify_form import *

class mmqgis_gridify_dialog(QDialog, Ui_mmqgis_gridify_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(int)"), self.layer_changed)
		
		self.filename.setText(mmqgis_temp_file_name(".shp"))
		

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def layer_changed(self):
		layer = mmqgis_find_layer(unicode(self.sourcelayer.currentText()))
		if (layer == None):
			return

		extent = QgsRectangle (-10.0, -10.0, 10.0, 20.0)
		if (layer):
			extent = layer.extent()

		#if (self.iface.mapCanvas() != None) and (self.iface.mapCanvas().mapRenderer() != None):
		#	extent = self.iface.mapCanvas().mapRenderer().extent()
		#elif self.iface.activeLayer():
		#	extent = self.iface.activeLayer().extent()

		self.hspacing.setText(unicode(extent.width() / 200))
		self.vspacing.setText(unicode(extent.height() / 200))

	def run(self):
		layername = unicode(self.sourcelayer.currentText()).strip()
		savename = unicode(self.filename.displayText()).strip()
		try:
			hspacing = float(self.hspacing.displayText())
			vspacing = float(self.vspacing.displayText())
		except:
			QMessageBox.critical(self.iface.mainWindow(), "Gridify", "Invalid spacing parameter")
			return

		message = mmqgis_gridify_layer(self.iface, layername, hspacing, vspacing, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Gridify", message)


# --------------------------------------------------------
#    mmqgis_hub_distance - Create shapefile of distances
#			   from points to nearest hub
# --------------------------------------------------------

from mmqgis_hub_distance_form import *

class mmqgis_hub_distance_dialog(QDialog, Ui_mmqgis_hub_distance_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if layer.type() == QgsMapLayer.VectorLayer:
				self.sourcelayerbox.addItem(layer.name())
				self.hubslayerbox.addItem(layer.name())

		if self.hubslayerbox.count() > 1:
			self.hubslayerbox.setCurrentIndex(1)

		QObject.connect(self.hubslayerbox, SIGNAL("currentIndexChanged(QString)"), self.set_name_attributes)

		self.set_name_attributes()

		self.outputtype.addItems(["Line to Hub", "Point"])

		self.measurement.addItems(["Layer Units", "Meters", "Feet", "Miles", "Kilometers"])
		# self.measurement.setEnabled(False)
	
		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_name_attributes(self):
		self.nameattributebox.clear()
		layer = mmqgis_find_layer(self.hubslayerbox.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.nameattributebox.addItem(field.name())

	def run(self):
		sourcename = unicode(self.sourcelayerbox.currentText())
		destname = unicode(self.hubslayerbox.currentText())
		nameattributename = unicode(self.nameattributebox.currentText())
		units = unicode(self.measurement.currentText())
		addlines = (self.outputtype.currentText() == "Line to Hub")
		savename = unicode(self.filename.displayText()).strip()
		evenly_distributed = self.distribute.isChecked()

		message = mmqgis_hub_distance(self.iface, sourcename, destname, \
			nameattributename, units, addlines, savename, evenly_distributed, 1)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Hub Distance", message)


# --------------------------------------------------------
#    mmqgis_hub_lines - Create shapefile of lines from
#			spoke points to matching hubs
# --------------------------------------------------------

from mmqgis_hub_lines_form import *

class mmqgis_hub_lines_dialog(QDialog, Ui_mmqgis_hub_lines_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if layer.type() == QgsMapLayer.VectorLayer:
				self.hublayer.addItem(layer.name())
				self.spokelayer.addItem(layer.name())

		QObject.connect(self.hublayer, SIGNAL("currentIndexChanged(QString)"), self.set_hub_attributes)
		QObject.connect(self.spokelayer, SIGNAL("currentIndexChanged(QString)"), self.set_spoke_attributes)

		self.set_hub_attributes(self.hublayer.currentText())
		self.set_spoke_attributes(self.spokelayer.currentText())

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_hub_attributes(self, layername):
		self.hubid.clear()
		layer = mmqgis_find_layer(layername)
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.hubid.addItem(field.name())

	def set_spoke_attributes(self, layername):
		self.spokehubid.clear()
		layer = mmqgis_find_layer(layername)
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.spokehubid.addItem(field.name())

	def run(self):
		hubname = unicode(self.hublayer.currentText())
		hubattr = unicode(self.hubid.currentText())
		spokename = unicode(self.spokelayer.currentText())
		spokeattr = unicode(self.spokehubid.currentText())
		savename = unicode(self.filename.displayText()).strip()
			
		message = mmqgis_hub_lines(self.iface, hubname, hubattr, spokename, spokeattr, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Hub Lines", message)


# ----------------------------------------------------------
#    mmqgis_kml_export - Export attributes to KML file
#			 suitable for display in Google Maps
# ----------------------------------------------------------

from mmqgis_kml_export_form import *

class mmqgis_kml_export_dialog(QDialog, Ui_mmqgis_kml_export_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browseoutfile, SIGNAL("clicked()"), self.browse_outfiles)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		self.descriptionseparator.addItems([ 'Paragraphs', 'Field Names', 'Commas' ])

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_fields)
		self.set_fields()

		self.outfilename.setText(mmqgis_temp_file_name(".kml"))

        def browse_outfiles(self):
		newname = QFileDialog.getSaveFileName(None, "Output KML File", 
			self.outfilename.displayText(), "KML File (*.kml *.xml)")
                if newname != None:
                	self.outfilename.setText(newname)

	def set_fields(self):
		self.namefield.clear()
		self.descriptionfields.clear()

		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.namefield.addItem(field.name())
			self.descriptionfields.addItem(field.name())
			if index > 0:
				self.descriptionfields.item(index).setSelected(1)

	def run(self):
		layername = unicode(self.sourcelayer.currentText())
		outfilename = unicode(self.outfilename.displayText())
		separator = unicode(self.descriptionseparator.currentText())
		namefield = unicode(self.namefield.currentText())

		# Compile a list and header of selected fields
		description = []
		for x in range(0, self.descriptionfields.count()):
			list_item = self.descriptionfields.item(x)
			if list_item.isSelected():
				description.append(unicode(list_item.text()))

		message = mmqgis_kml_export(self.iface, layername, namefield, description, separator, outfilename, True)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "KML Export", message)

# --------------------------------------------------------
#    mmqgis_label - Create single label points for
#		    single- or multi-feature items
# --------------------------------------------------------

from mmqgis_label_form import *

class mmqgis_label_dialog(QDialog, Ui_mmqgis_label_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_label_attributes)

		self.set_label_attributes()

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_label_attributes(self):
		self.labelattribute.clear()
		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.labelattribute.addItem(field.name())

	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		layername = unicode(self.sourcelayer.currentText())
		labelattributename = self.labelattribute.currentText()

		message = mmqgis_label_point(self.iface, layername, labelattributename, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Label", message)


# --------------------------------------------------------
#    mmqgis_merge - Merge layers to single shapefile
# --------------------------------------------------------

from mmqgis_merge_form import *

class mmqgis_merge_dialog(QDialog, Ui_mmqgis_merge_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browseoutfile, SIGNAL("clicked()"), self.browse_outfiles)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		self.sourcelayers.clear()
		for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if layer.type() == QgsMapLayer.VectorLayer:
				self.sourcelayers.addItem(layer.name())
				self.sourcelayers.item(self.sourcelayers.count() - 1).setSelected(1)

		# Suggested by Daniel Vaz
		self.sourcelayers.setDragDropMode(QAbstractItemView.InternalMove)
		self.outfilename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfiles(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.outfilename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.outfilename.setText(newname)

	def run(self):
		layernames = []
		for x in range(0, self.sourcelayers.count()):
			if self.sourcelayers.item(x).isSelected():
				layernames.append(unicode(self.sourcelayers.item(x).text()))

		savename = unicode(self.outfilename.displayText()).strip()

		message = mmqgis_merge(self.iface, layernames, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Merge", message)


# --------------------------------------------------------
#    mmqgis_points - Point creation plugin
# --------------------------------------------------------

from mmqgis_points_form import *

class mmqgis_points_dialog(QDialog, Ui_mmqgis_grid_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.boundarytype, SIGNAL("currentIndexChanged(QString)"), self.boundarytype_changed)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		# Default to 10x10 grid over current map view
		self.units.setCurrentIndex(0);
		self.boundarytype.setCurrentIndex(0);

		extent = self.iface.mapCanvas().mapSettings().extent()
		self.hspacing.setText(unicode(mmqgis_round(extent.width() / 10, 2)))
		self.vspacing.setText(unicode(mmqgis_round(extent.height() / 10, 2)))

		self.filename.setText(mmqgis_temp_file_name(".shp"))
		

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def boundarytype_changed(self, text):
		if text == "Fill Current Map View":
			self.boundarylayer.clear()
			self.boundarylayer.setEnabled(False)

		if text == "Fill Boundary Layer Extent":
			self.boundarylayer.clear()
			self.boundarylayer.setEnabled(True)

			for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
				# if layer.type() == QgsMapLayer.VectorLayer:
				self.boundarylayer.addItem(layer.name())

		if text == "Fill Boundary Layer Polygons":
			self.boundarylayer.clear()
			self.boundarylayer.setEnabled(True)

			for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
				if (layer.type() == QgsMapLayer.VectorLayer) and \
				   ((layer.dataProvider().geometryType() == QGis.WKBPolygon) or \
			   	    (layer.dataProvider().geometryType() == QGis.WKBPolygon25D) or \
				    (layer.dataProvider().geometryType() == QGis.WKBMultiPolygon) or \
				    (layer.dataProvider().geometryType() == QGis.WKBMultiPolygon25D)):
					self.boundarylayer.addItem(layer.name())

		if self.boundarylayer.count() > 0:
			self.boundarylayer.setCurrentIndex(0);

	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		hspacing = float(self.hspacing.displayText())
		vspacing = float(self.vspacing.displayText())
		hoffset = float(self.hoffset.displayText())
		voffset = float(self.voffset.displayText())

		extent = self.iface.mapCanvas().mapSettings().extent()
		crs = self.iface.mapCanvas().mapSettings().destinationCrs()

		# If using a boundary layer, transform extent to current map CRS
		polygon_layer = None
		if self.boundarytype.currentText() != "Fill Current Map View":
			polygon_layer = self.boundarylayer.currentText()
			layer = mmqgis_find_layer(polygon_layer)
			if layer == None:
				QMessageBox.critical(self.iface.mainWindow(), "Grid", message)
				return

			transform = QgsCoordinateTransform(layer.crs(), crs)
			extent = transform.transformBoundingBox(layer.extent())

		# Don't pass polygon layer if not constraining to polygons
		if self.boundarytype.currentText() == "Fill Boundary Layer Extent":
			polygon_layer = None

		# Transform everything to meters
		if self.units.currentText() == "Feet":
			hspacing = mmqgis_feet_to_meters(hspacing)
			vspacing = mmqgis_feet_to_meters(vspacing)
			hoffset = mmqgis_feet_to_meters(hoffset)
			voffset = mmqgis_feet_to_meters(voffset)

		elif self.units.currentText() == "Miles":
			hspacing = mmqgis_miles_to_meters(hspacing)
			vspacing = mmqgis_miles_to_meters(vspacing)
			hoffset = mmqgis_miles_to_meters(hoffset)
			voffset = mmqgis_miles_to_meters(voffset)

		elif self.units.currentText() == "Kilometers":
			hspacing = hspacing * 1000
			vspacing = vspacing * 1000
			hoffset = hoffset * 1000
			voffset = voffset * 1000

		# If using absolute units, transform to current map CRS via WGS84
		if self.units.currentText() != "Project Coordinates":
			wgs84 = QgsCoordinateReferenceSystem()
			wgs84.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")
			transform = QgsCoordinateTransform(crs, wgs84)

			center = transform.transform(extent.center())
			hs_end = transform.transform(mmqgis_endpoint(center, hspacing, 90), 
				QgsCoordinateTransform.ReverseTransform)
			vs_end = transform.transform(mmqgis_endpoint(center, vspacing, 0),
				QgsCoordinateTransform.ReverseTransform)
			ho_end = transform.transform(mmqgis_endpoint(center, hoffset, 90),
				QgsCoordinateTransform.ReverseTransform)
			vo_end = transform.transform(mmqgis_endpoint(center, voffset, 0),
				QgsCoordinateTransform.ReverseTransform)

			center = extent.center()
			hspacing = hs_end.x() - center.x()
			vspacing = vs_end.y() - center.y()
			hoffset = ho_end.x() - center.x()
			voffset = vo_end.y() - center.y()
			
		message = mmqgis_points(self.iface, savename, hspacing, vspacing, 
			hoffset, voffset, extent, crs, polygon_layer)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Points", message)




# ----------------------------------------------------------
#    mmqgis_search - Interactive search
# ----------------------------------------------------------

from mmqgis_search_form import *

# These globals are a kludge to give search term persistence.
# This should probably be implemented in Qt with a static
# dialog and multiple exec(), but that is undocumented behavior
# that might break on Windoze.
# Defaults were requested by South Derbyshire District Council (7/14/2013)

mmqgis_search_layername = "SD_LLPG_MI_Live"
mmqgis_search_attribute1 = "SearchAddress"
mmqgis_search_attribute2 = "Postcode"
mmqgis_search_comparison1 = "contains"
mmqgis_search_comparison2 = "contains"
mmqgis_search_value1 = ""
mmqgis_search_value2 = ""

class mmqgis_search_dialog(QDialog, Ui_mmqgis_search_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)

		# print "Setup: " + mmqgis_search_layername

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.searchlayer, mmqgis_search_layername)
		self.searchlayer.addItem("[Google Maps]")
		self.searchlayer.addItem("[Open Street Map]")

		#Change of selection signals: currentTextChanged, currentRowChanged, itemSelectionChanged
		QObject.connect(self.results, SIGNAL("itemSelectionChanged()"), self.select_feature)

		QObject.connect(self.search, SIGNAL("clicked()"), self.perform_search)
		QObject.connect(self.donebutton, SIGNAL("clicked()"), self.finished)
		QObject.connect(self.searchlayer, SIGNAL("currentIndexChanged(QString)"), self.set_search_attributes)
		# QObject.connect(self.exportcsv, SIGNAL("clicked()"), self.export_to_file)

		comparisons = ['contains', 'begins with', '=', '<>', '>', '>=', '<', '<=']
		for x in comparisons:
			self.comparison1.addItem(x)
			self.comparison2.addItem(x)

		self.set_search_attributes()

	def set_search_attributes(self):
		self.results.clear()
		self.attribute1.clear()
		self.attribute2.clear()
		self.attribute2.addItem("(none)")

		# Special case for web address searches
		if (self.searchlayer.currentText() == "[Google Maps]") or \
		   (self.searchlayer.currentText() == "[Open Street Map]"):
			self.comparison1.setCurrentIndex(self.comparison1.findText("="))
			self.comparison2.setEnabled(False)
			self.attribute1.addItem("Address")
			self.attribute1.setEnabled(False)
			self.attribute2.setEnabled(False)
			self.value2.setEnabled(False)
			return

		else:
			self.comparison2.setEnabled(True)
			self.attribute1.setEnabled(True)
			self.attribute2.setEnabled(True)
			self.value2.setEnabled(True)

		layer = mmqgis_find_layer(self.searchlayer.currentText())
		if layer == None:
			return

		if (mmqgis_search_comparison1 > ""):
			self.comparison1.setCurrentIndex(self.comparison1.findText(mmqgis_search_comparison1))

		if (mmqgis_search_comparison2 > ""):
			self.comparison2.setCurrentIndex(self.comparison2.findText(mmqgis_search_comparison2))

		for index, field in enumerate(layer.dataProvider().fields().toList()):
			self.attribute1.addItem(field.name())
			self.attribute2.addItem(field.name())

			if (field.name() == mmqgis_search_attribute1):
				self.attribute1.setCurrentIndex(index)
				self.value1.setText(mmqgis_search_value1)

			elif (field.name() == mmqgis_search_attribute2):
				self.attribute2.setCurrentIndex(index + 1)
				self.value2.setText(mmqgis_search_value2)

	def perform_search(self):
		if (self.searchlayer.currentText() == "[Google Maps]"):
			return self.perform_web_search("google")

		elif (self.searchlayer.currentText() == "[Open Street Map]"):
			return self.perform_web_search("osm")

		# print "perform_search(" + self.searchlayer.currentText() + ")"

		# Build list(s) of attribute names, comparison operators and comparison values
		layername = unicode(self.searchlayer.currentText())
		attributes = [ unicode(self.attribute1.currentText()) ]
		comparisons = [ self.comparison1.currentText() ]
		values = [ unicode(self.value1.displayText()).strip() ]

		if len(values[0]) <= 0:
			QMessageBox.critical(self.iface.mainWindow(), "Search", "No value given for comparison")
			return

		if (unicode(self.attribute1.currentText()) != "(none)") and \
		   (len(unicode(self.value2.displayText()).strip()) > 0):
			attributes.append(unicode(self.attribute2.currentText()))
			comparisons.append(self.comparison2.currentText())
			values.append(unicode(self.value2.displayText()).strip())

		# Perform search
		self.results.clear()
		self.features = mmqgis_search(self.iface, layername, attributes, comparisons, values, 1000)
		if type(self.features) != list:
			QMessageBox.critical(self.iface.mainWindow(), "Search", self.features)
			self.features = None
			return

		# Populate list of found features
		self.results.clear()
		for index, feature in self.features:
			# print str(index) + ") " + unicode(feature)
			self.results.addItem(unicode(feature))

	def perform_web_search(self, service):
		address = unicode(self.value1.displayText()).strip()
		address.replace("  ", " ")
		address.replace(" ", "+")
		# print "perform_web_search(" + address + ")"

		if (service == "google"):
			x, y, addrtype, addrlocat, formatted_addr = mmqgis_geocode_address_google(address)
		else:
			x, y, addrtype, addrlocat, formatted_addr = mmqgis_geocode_address_osm(address)

		self.features = []
		self.results.clear()
		for z in range(0, len(x)):
			self.features.append([[x[z],y[z]], formatted_addr[z]])
			self.results.addItem(unicode(formatted_addr[z]))


	# def export_to_file(self):
	#	newname = QFileDialog.getSaveFileName(None, "Output CSV File", 
	#		mmqgis_temp_file_name(".csv"), "CSV File (*.csv)")
	#
	#	if newname != None:
	#		self.filename.setText(newname)

	def select_feature(self):
		if (len(self.features) <= 0):
			return

		# Results from OSM / Google Maps
		if (type(self.features[0][0]) == list):
			return self.pan_to_xy_locations()

		layer = mmqgis_find_layer(self.searchlayer.currentText())
		if layer == None:
			return

		# Select all features in the layer that are selected in the results box
		layer.removeSelection()
		for index in range(0, self.results.count()):
			if (index < len(self.features)) and self.results.item(index).isSelected():
				# print unicode(index) + ") selected feature " + unicode(self.features[index][0])
				layer.select(self.features[index][0])

		# Nothing selected
		if len(layer.selectedFeatures()) <= 0:
			return 

		# Find the extent of the selected items
		transform = QgsCoordinateTransform(layer.dataProvider().crs(), 
			self.iface.mapCanvas().mapRenderer().destinationCrs())

		centroids = []
		for feature in layer.selectedFeatures():
			centroids.append(transform.transform(feature.geometry().boundingBox().center()))

		# Center the canvas around the centroid of the selected features
		center = QgsGeometry.fromMultiPoint(centroids).boundingBox().center()
		extent = self.iface.mapCanvas().extent()
		extent.set(center.x() - (extent.width() / 2.0), center.y() - (extent.height() / 2.0),
			center.x() + (extent.width() / 2.0), center.y() + (extent.height() / 2.0))
		self.iface.mapCanvas().setExtent(extent)

		layer.triggerRepaint()
		# self.iface.mapCanvas().refresh()
		

	def pan_to_xy_locations(self):
		if (len(self.features) <= 0):
			return

		# Get list of selected points
		points = []
		for index in range(0, self.results.count()):
			if (index < len(self.features)) and self.results.item(index).isSelected():
				points.append(QgsPoint(self.features[index][0][0], self.features[index][0][1]))

		# Nothing selected
		if (len(points) <= 0):
			return

		# Transform to the map's coordinate system
		wgs84 = QgsCoordinateReferenceSystem()
		wgs84.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")
		transform = QgsCoordinateTransform(wgs84,
			self.iface.mapCanvas().mapRenderer().destinationCrs())

		for z in range(0, len(points)):
			points[z] = transform.transform(points[z])

		# Center the canvas around the centroid of the selected features
		center = QgsGeometry.fromMultiPoint(points).boundingBox().center()
		extent = self.iface.mapCanvas().extent()
		extent.set(center.x() - (extent.width() / 2.0), center.y() - (extent.height() / 2.0),
			center.x() + (extent.width() / 2.0), center.y() + (extent.height() / 2.0))
		self.iface.mapCanvas().setExtent(extent)

		# layer.triggerRepaint()
		self.iface.mapCanvas().refresh()

	def finished(self):
		# Save form contents for future searches
		global mmqgis_search_layername
		global mmqgis_search_attribute1
		global mmqgis_search_attribute2
		global mmqgis_search_comparison1
		global mmqgis_search_comparison2
		global mmqgis_search_value1
		global mmqgis_search_value2

		mmqgis_search_layername = self.searchlayer.currentText()
		mmqgis_search_attribute1 = self.attribute1.currentText()
		mmqgis_search_attribute2 = self.attribute2.currentText()
		mmqgis_search_comparison1 = self.comparison1.currentText()
		mmqgis_search_comparison2 = self.comparison2.currentText()
		mmqgis_search_value1 = self.value1.displayText()
		mmqgis_search_value2 = self.value2.displayText()

		# print "Finished " + mmqgis_search_layername

		self.done(1)



# ----------------------------------------------------------
#    mmqgis_select - Select features by attribute
# ----------------------------------------------------------

from mmqgis_select_form import *

class mmqgis_select_dialog(QDialog, Ui_mmqgis_select_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_select_attributes)
		self.set_select_attributes()

		comparisons = ['=', '<>', '>', '>=', '<', '<=', 'begins with', 'contains']
		for x in comparisons:
			self.comparison.addItem(x)

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_select_attributes(self):
		self.selectattribute.clear()
		layername = self.sourcelayer.currentText()
		for name, selectlayer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if selectlayer.name() == layername:
				for field in selectlayer.dataProvider().fields().toList():
					self.selectattribute.addItem(field.name())

	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		layername = unicode(self.sourcelayer.currentText())
		comparisonname = self.comparison.currentText()
		comparisonvalue = unicode(self.value.displayText()).strip()
		selectattributename = self.selectattribute.currentText()

		message = mmqgis_select(self.iface, layername, [ selectattributename], \
			[ comparisonname ], [ comparisonvalue ], savename, 1)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Select", message)


# --------------------------------------------------------
#    mmqgis_sort - Sort shapefile by attribute
# --------------------------------------------------------

from mmqgis_sort_form import *

class mmqgis_sort_dialog(QDialog, Ui_mmqgis_sort_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_sort_attributes)

		self.set_sort_attributes()

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_sort_attributes(self):
		self.sortattribute.clear()
		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.sortattribute.addItem(field.name())

	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		layername = unicode(self.sourcelayer.currentText())
		direction = unicode(self.direction.currentText())
		sortattributename = self.sortattribute.currentText()

		message = mmqgis_sort(self.iface, layername, sortattributename, savename, direction, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Sort", message)


# ---------------------------------------------------------------
#    mmqgis_geocode_street_layer - Geocode addresses from street 
#					address finder shapefile
# ---------------------------------------------------------------

from mmqgis_geocode_street_layer_form import *

class mmqgis_geocode_street_layer_dialog(QDialog, Ui_mmqgis_geocode_street_layer_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse_infile, SIGNAL("clicked()"), self.browse_infile_dialog)
		QObject.connect(self.browse_shapefile, SIGNAL("clicked()"), self.browse_shapefile_dialog)
		QObject.connect(self.browse_notfound, SIGNAL("clicked()"), self.browse_notfound_dialog)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.streetlayer, True)

		QObject.connect(self.streetlayer, SIGNAL("currentIndexChanged(int)"), self.set_layer_attributes)

		self.set_layer_attributes(0)

		self.shapefilename.setText(mmqgis_temp_file_name(".shp"))
		self.notfoundfilename.setText(os.getcwd() + "/notfound.csv")

        def browse_infile_dialog(self):
		newname = QFileDialog.getOpenFileName(None, "Address CSV Input File", 
			self.infilename.displayText(), "CSV File (*.csv *.txt)")

                if newname:
			header = mmqgis_read_csv_header(self.iface, newname)
			if not header:
				return

			# Add attributes to street and number
			self.streetnamefield.clear()
			self.numberfield.clear()
			self.zipfield.clear()

			self.zipfield.addItem("(none)")
			for field in header:
				self.streetnamefield.addItem(field)
				self.numberfield.addItem(field)
				self.zipfield.addItem(field)

			self.zipfield.setCurrentIndex(0)
			for x, field in enumerate(header):
				if field.strip().lower().find("street") >= 0:
					self.streetnamefield.setCurrentIndex(x)

#				elif field.strip().lower().find("number") >= 0:
				elif field.strip().lower().find("numero") >= 0: # jja
					self.numberfield.setCurrentIndex(x)

				elif field.strip().lower().find("zip") >= 0:
					self.zipfield.setCurrentIndex(x + 1)

                	self.infilename.setText(newname)

        def browse_notfound_dialog(self):
		newname = QFileDialog.getSaveFileName(None, "Not Found List Output File", 
			self.notfoundfilename.displayText(), "CSV File (*.csv *.txt)")
                if newname != None:
                	self.notfoundfilename.setText(newname)

        def browse_shapefile_dialog(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.shapefilename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.shapefilename.setText(newname)

	def set_layer_attributes(self, index):
		# index parameter required for currentIndexChanged() signal and is not used
		layername = unicode(self.streetlayer.currentText())
		layer = mmqgis_find_layer(layername)

		if not layer:
			print "Layer not found " + layername
			return

		self.setback.setText("15") # +15 by jja
		self.aeiou_qual.setCurrentIndex(0) # jja quality level 1-2-3-4-5 (0-4)

		#if (layer.dataProvider().crs().mapUnits() == QGis.Feet):
                #	self.setback.setText("60")
		#elif (layer.dataProvider().crs().mapUnits() == QGis.Meters):
                #	self.setback.setText("4")
                #else:
		#	self.setback.setText("0")
	
		#elif (layer.dataProvider().crs().mapUnits() == QGis.Degrees):
		#	meters = 4 * cos(layer.extent().center().y() * pi / 180) * 6378137.0
                #	self.setback.setText(unicode(meters))
		#else:
                #	self.setback.setText("4")

		self.streetname.clear()
		self.fromx.clear()
		self.fromy.clear()
		self.tox.clear()
		self.toy.clear()
		self.leftfrom.clear()
		self.leftto.clear()
		self.rightfrom.clear()
		self.rightto.clear()
		self.leftzip.clear()
		self.rightzip.clear()

		# From/To options to use line geometries for X/Y coordinates
		# Assumes order of line vertices in shapefile is consistent

		self.fromx.addItem("(street line start)")
		self.fromx.addItem("(street line end)")
		self.fromy.addItem("(street line start)")
		self.fromy.addItem("(street line end)")
		self.tox.addItem("(street line start)")
		self.tox.addItem("(street line end)")
		self.toy.addItem("(street line start)")
		self.toy.addItem("(street line end)")

		self.fromx.setCurrentIndex(0)
		self.fromy.setCurrentIndex(0)
		self.tox.setCurrentIndex(1)
		self.toy.setCurrentIndex(1)

		self.leftzip.addItem("(none)")
		self.rightzip.addItem("(none)")

		# Add all attributes to lists

		for field in layer.dataProvider().fields().toList():
			self.streetname.addItem(unicode(field.name()))
			self.fromx.addItem(unicode(field.name()))
			self.fromy.addItem(unicode(field.name()))
			self.tox.addItem(unicode(field.name()))
			self.toy.addItem(unicode(field.name()))
			self.leftfrom.addItem(unicode(field.name()))
			self.leftto.addItem(unicode(field.name()))
			self.rightfrom.addItem(unicode(field.name()))
			self.rightto.addItem(unicode(field.name()))
			self.leftzip.addItem(unicode(field.name()))
			self.rightzip.addItem(unicode(field.name()))


		# Select different parameters based on guesses from attribute names

		self.leftzip.setCurrentIndex(0)
		self.rightzip.setCurrentIndex(0)
		for index, field in enumerate(layer.dataProvider().fields()):
			if unicode(field.name()).lower().find("name") >= 0: # org
#			if unicode(field.name()).lower().find("str_name") >= 0: # jja
				self.streetname.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "street":
				self.streetname.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "xfrom":
				self.fromx.setCurrentIndex(index + 2)
			elif unicode(field.name()).lower() == "yfrom":
				self.fromy.setCurrentIndex(index + 2)
			elif unicode(field.name()).lower() == "xto":
				self.tox.setCurrentIndex(index + 2)
			elif unicode(field.name()).lower() == "yto":
				self.toy.setCurrentIndex(index + 2)
			elif unicode(field.name()).lower() == "fromleft":
				self.leftfrom.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "lfromadd":
				self.leftfrom.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "fromright":
				self.rightfrom.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "rfromadd":
				self.rightfrom.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "toleft":
				self.leftto.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "ltoadd":
				self.leftto.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "toright":
				self.rightto.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "rtoadd":
				self.rightto.setCurrentIndex(index)
			elif unicode(field.name()).lower() == "zipl":
				self.leftzip.setCurrentIndex(index + 1)
			elif unicode(field.name()).lower() == "zipr":
				self.rightzip.setCurrentIndex(index + 1)

	def run(self):
		csvname = unicode(self.infilename.displayText()).strip()
		streetnamefield = unicode(self.streetnamefield.currentText()).strip()
		numberfield = unicode(self.numberfield.currentText()).strip()
		zipfield = unicode(self.zipfield.currentText()).strip()
		if zipfield == "(none)":
			zipfield = None

		layername = unicode(self.streetlayer.currentText())
		streetname = unicode(self.streetname.currentText())
		fromx = unicode(self.fromx.currentText())
		fromy = unicode(self.fromy.currentText())
		tox = unicode(self.tox.currentText())
		toy = unicode(self.toy.currentText())
		leftfrom = unicode(self.leftfrom.currentText())
		rightfrom = unicode(self.rightfrom.currentText())
		leftto = unicode(self.leftto.currentText())
		rightto = unicode(self.rightto.currentText())
		
		aeiou_qual = unicode(self.aeiou_qual.currentText()) # jja
		zip_allowance = unicode(self.zip_allowance.checkState()) # jja
		nr_allowance = unicode(self.nr_allowance.checkState()) # jja

		leftzip = unicode(self.leftzip.currentText())
		if leftzip == "(none)":
			leftzip = None
		rightzip = unicode(self.rightzip.currentText())
		if rightzip == "(none)":
			rightzip = None

		setback = float(self.setback.displayText())
		shapefilename = unicode(self.shapefilename.displayText())
		notfoundfile = self.notfoundfilename.displayText()
		# addlayer = self.addtoproject.isChecked()

		message = mmqgis_geocode_street_layer(self.iface, layername, csvname, streetnamefield, 
			numberfield, zipfield, streetname, fromx, fromy, tox, toy, leftfrom, rightfrom, 
			leftto, rightto, leftzip, rightzip, setback, shapefilename, notfoundfile, 1, aeiou_qual, zip_allowance, nr_allowance)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Geocode", message)

# ----------------------------------------------------------
#    mmqgis_spatial_join - Spatial Join
# ----------------------------------------------------------

from mmqgis_spatial_join_form import *

class mmqgis_spatial_join_dialog(QDialog, Ui_mmqgis_spatial_join_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browseoutfile, SIGNAL("clicked()"), self.browse_outfiles)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.targetlayer, True)

		self.fieldop.addItems(["First", "Sum", "Average", "Proportional Sum"])
		QObject.connect(self.targetlayer, SIGNAL("currentIndexChanged(QString)"), self.set_join_layers)
		QObject.connect(self.joinlayer, SIGNAL("currentIndexChanged(QString)"), self.set_spatial_operations)
		self.set_join_layers()

		self.outfilename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfiles(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.outfilename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.outfilename.setText(newname)

	def set_join_layers(self):
		self.joinlayer.clear()
		layer = mmqgis_find_layer(self.targetlayer.currentText())
		if (layer == None):
			return
		for name, join in QgsMapLayerRegistry.instance().mapLayers().iteritems():
			if (layer.type() == QgsMapLayer.VectorLayer) and \
			   (layer.name() != join.name()):
				self.joinlayer.addItem(join.name())

		self.joinlayer.setCurrentIndex(0)
		self.set_spatial_operations()

	def set_spatial_operations(self):
		target = mmqgis_find_layer(self.targetlayer.currentText())
		if (target == None):
			return

		join = mmqgis_find_layer(self.joinlayer.currentText())
		if (join == None):
			return

		self.spatialop.clear()

		if not join:
			return

		# OpenLayers layers don't have a dataProvider
		if (not hasattr(target, "dataProvider")) or \
			(not hasattr(join, "dataProvider")):
			return

		# Rasters don't have fields()
		if (not hasattr(target.dataProvider(), "fields")) or \
			(not hasattr(join.dataProvider(), "fields")):
			return

		self.fieldnames.clear()
		for index, field in enumerate(target.dataProvider().fields()):
			self.fieldnames.addItem(field.name())
			self.fieldnames.item(self.fieldnames.count() - 1).setSelected(1)

		for index, field in enumerate(join.dataProvider().fields()):
			self.fieldnames.addItem(field.name())
			self.fieldnames.item(self.fieldnames.count() - 1).setSelected(1)

		if (target.dataProvider().geometryType() == QGis.WKBPoint) or \
		   (target.dataProvider().geometryType() == QGis.WKBPoint25D):
			if (join.dataProvider().geometryType() == QGis.WKBPolygon) or \
			   (join.dataProvider().geometryType() == QGis.WKBPolygon25D) or \
			   (join.dataProvider().geometryType() == QGis.WKBMultiPolygon) or \
			   (join.dataProvider().geometryType() == QGis.WKBMultiPolygon25D):
				self.spatialop.addItems(["Within"])

		elif (target.dataProvider().geometryType() == QGis.WKBMultiPoint) or \
		     (target.dataProvider().geometryType() == QGis.WKBMultiPoint25D) or \
		     (target.dataProvider().geometryType() == QGis.WKBLineString) or \
		     (target.dataProvider().geometryType() == QGis.WKBLineString25D) or \
		     (target.dataProvider().geometryType() == QGis.WKBMultiLineString) or \
		     (target.dataProvider().geometryType() == QGis.WKBMultiLineString25D):
			if (join.dataProvider().geometryType() == QGis.WKBPolygon) or \
			   (join.dataProvider().geometryType() == QGis.WKBPolygon25D) or \
			   (join.dataProvider().geometryType() == QGis.WKBMultiPolygon) or \
			   (join.dataProvider().geometryType() == QGis.WKBMultiPolygon25D):
				self.spatialop.addItems(["Intersects", "Within"])

		else: # Polygon
			if (join.dataProvider().geometryType() == QGis.WKBPoint) or \
			   (join.dataProvider().geometryType() == QGis.WKBPoint25D):
				self.spatialop.addItems(["Contains"])

			elif (join.dataProvider().geometryType() == QGis.WKBMultiPoint) or \
			     (join.dataProvider().geometryType() == QGis.WKBMultiPoint25D) or \
			     (join.dataProvider().geometryType() == QGis.WKBLineString) or \
			     (join.dataProvider().geometryType() == QGis.WKBLineString25D) or \
			     (join.dataProvider().geometryType() == QGis.WKBMultiLineString):
				self.spatialop.addItems(["Intersects", "Contains"])

			else: # Polygon
				self.spatialop.addItems(["Intersects", "Within", "Contains"])


	def run(self):
		target = unicode(self.targetlayer.currentText())
		spatialop = unicode(self.spatialop.currentText())
		join = unicode(self.joinlayer.currentText())
		fieldop = unicode(self.fieldop.currentText())
		outfilename = unicode(self.outfilename.displayText())

		fields = []
		for x in range(0, self.fieldnames.count()):
			if self.fieldnames.item(x).isSelected():
				fields.append(self.fieldnames.item(x).text())

		message = mmqgis_spatial_join(self.iface, target, spatialop, join, fields, fieldop, outfilename, True)

		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Spatial Join", message)

# ---------------------------------------------------------
#    mmqgis_text_to_float - Change text fields to numbers
# ---------------------------------------------------------

from mmqgis_text_to_float_form import *

class mmqgis_text_to_float_dialog(QDialog, Ui_mmqgis_text_to_float_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		QObject.connect(self.sourcelayer, SIGNAL("currentIndexChanged(QString)"), self.set_fieldnames)

		self.set_fieldnames()

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def set_fieldnames(self):
		self.fieldnames.clear()
		layer = mmqgis_find_layer(self.sourcelayer.currentText())
		if (layer == None):
			return
		for index, field in enumerate(layer.dataProvider().fields()):
			self.fieldnames.addItem(field.name())

		# for index, field in enumerate(layer.dataProvider().fields()):
			if (field.type() == QVariant.String):
				self.fieldnames.item(index).setSelected(1)

	def run(self):
		layername = unicode(self.sourcelayer.currentText())
		savename = unicode(self.filename.displayText()).strip()
		# addlayer = self.addtoproject.isChecked()

		attributes = []
		for x in range(0, self.fieldnames.count()):
			if self.fieldnames.item(x).isSelected():
				attributes.append(self.fieldnames.item(x).text())

		message = mmqgis_text_to_float(self.iface, layername, attributes, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Text to Float", message)


# --------------------------------------------------------
#    mmqgis_voronoi - Voronoi diagram creation
# --------------------------------------------------------

from mmqgis_voronoi_form import *

class mmqgis_voronoi_dialog(QDialog, Ui_mmqgis_voronoi_form):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.browse, SIGNAL("clicked()"), self.browse_outfile)
        	QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)

		mmqgis_load_combo_box_with_vector_layers(self.iface, self.sourcelayer, True)

		self.filename.setText(mmqgis_temp_file_name(".shp"))

        def browse_outfile(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.filename.displayText(), "Shapefile (*.shp)")
                if newname != None:
                	self.filename.setText(newname)

	def run(self):
		savename = unicode(self.filename.displayText()).strip()
		layer = unicode(self.sourcelayer.currentText())

		message = mmqgis_voronoi_diagram(self.iface, layer, savename, 1)
		if message <> None:
			QMessageBox.critical(self.iface.mainWindow(), "Voronoi", message)


# --------------------------------------------------------
#    Utility Functions
# --------------------------------------------------------

def mmqgis_read_csv_header(qgis, filename):
	try:
		infile = open(filename, 'r')
	except Exception as e:
		QMessageBox.information(qgis.mainWindow(), 
			"Input CSV File", "Failure opening " + filename + ": " + unicode(e))
		return None

	try:
		dialect = csv.Sniffer().sniff(infile.read(4096))
	except:
		QMessageBox.information(qgis.mainWindow(), "Input CSV File", 
			"Bad CSV file - verify that your delimiters are consistent");
		return None

	infile.seek(0)
	reader = csv.reader(infile, dialect)
		
	# Decode from UTF-8 characters because csv.reader can only handle 8-bit characters
	header = reader.next()
	header = [unicode(field, "utf-8") for field in header]

	del reader
	del infile

	if len(header) <= 0:
		QMessageBox.information(qgis.mainWindow(), "Input CSV File", 
			filename + " does not appear to be a CSV file")
		return None

	return header

def mmqgis_load_combo_box_with_vector_layers(qgis, combo_box, set_selected):
	for name, layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
		if layer.type() == QgsMapLayer.VectorLayer:
			combo_box.addItem(layer.name())

	# Parameter can be boolean "True" to use current selection in layer pane
	# or can be a str/unicode name

	if (type(set_selected) != bool):
		combo_index = combo_box.findText(set_selected)
		if combo_index >= 0:
			combo_box.setCurrentIndex(combo_index)
			return;

	for index, layer in enumerate(qgis.legendInterface().selectedLayers()):
		combo_index = combo_box.findText(layer.name())
		if combo_index >= 0:
			combo_box.setCurrentIndex(combo_index)
			break;

	

def mmqgis_temp_file_name(suffix):
	preferred = os.getcwd() + "/temp" + suffix
	if not os.path.isfile(preferred):
		return preferred

	for x in range(2, 10):
		name = os.getcwd() + "/temp" + unicode(x) + suffix
		if not os.path.isfile(name):
			return name

	return preferred


