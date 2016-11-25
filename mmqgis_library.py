# -*- coding: utf-8 -*-
# --------------------------------------------------------
#    mmqgis_library - mmqgis operation functions
#
#    begin                : 10 May 2010
#    copyright            : (c) 2010 by Michael Minn
#    email                : See michaelminn.com
#
#   MMQGIS is free software and is offered without guarantee
#   or warranty. You can redistribute it and/or modify it 
#   under the terms of version 2 of the GNU General Public 
#   License (GPL v2) as published by the Free Software 
#   Foundation (www.gnu.org).
#   
#   Modified: MC JJA (c) 2016 by Janko J A
#   
# --------------------------------------------------------

import io
import csv
import sys
import time
import math
import locale
import urllib2
import os.path
import operator
import tempfile
import xml.etree.ElementTree

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from math import *
from inspect import currentframe # jja
import re # jja

# --------------------------------------------------------
#    MC JJA Utility Functions
#		Features added for address geocoding:
#			Linear interpolation on curved streets
#			Allowance for post code alterations
#			Allowance for both street sides having same parity
#			Allowance for mixed parity
#			Allowance for house number /a - /g (with floating number value)
#			Reduced setback on shorter streets
#			Corner setback based on relative (assumed) parcel width
#			Logging reference centerline source feature ID
#			
#			original rightzipcode bug fixed
# --------------------------------------------------------

def lin_int_mc(geometry, linear_pos, oid=(0,0,0)):
	(gml_oid_number,width_number,number) = oid
	lin_cum = 0
	if (geometry.wkbType() == QGis.WKBLineString):
		line = geometry.asPolyline()
		for i in range(0, len(line)):
			if i + 1 >= len(line):
				QgsMessageLog.logMessage(''.join(('oid: ',str(gml_oid_number),';linear_pos: ',str(linear_pos),\
				';width_number: ',str(width_number),';number: ',str(number)))) # jja
			fromx = line[i].x()
			fromy = line[i].y()
			tox = line[i+1].x()
			toy = line[i+1].y()
			lin_cur = sqrt(pow(tox - fromx, 2.0) + pow(toy - fromy, 2.0))
			if (lin_cum + lin_cur) >= linear_pos:
				angle = atan2(toy - fromy, tox - fromx)
				ratio = (linear_pos - lin_cum) / lin_cur
				x = fromx + ((lin_cur * ratio) * cos(angle))
				y = fromy + ((lin_cur * ratio) * sin(angle))
				return (x,y,angle)
			else:
				lin_cum += lin_cur

	elif (geometry.wkbType() == QGis.WKBMultiLineString):
		lines = geometry.asMultiPolyline()
		for m in range(0, len(lines)+1):
			if m >= len(lines):
				QgsMessageLog.logMessage(''.join(('oid: ',str(gml_oid_number),';linear_pos: ',str(linear_pos),\
				';width_number: ',str(width_number),';number: ',str(number),';len(lines): ',str(len(lines))))) # jja
			line = lines[m]
			for i in range(0, len(line)):
				if i + 1 >= len(line):
					QgsMessageLog.logMessage(''.join(('oid: ',str(oid),';linear_pos: ',str(linear_pos)))) # jja
				fromx = line[i].x()
				fromy = line[i].y()
				tox = line[i+1].x()
				toy = line[i+1].y()
				lin_cur = sqrt(pow(tox - fromx, 2.0) + pow(toy - fromy, 2.0))
				if (lin_cum + lin_cur) >= linear_pos:
					angle = atan2(toy - fromy, tox - fromx)
					ratio = (linear_pos - lin_cum) / lin_cur
					x = fromx + ((lin_cur * ratio) * cos(angle))
					y = fromy + ((lin_cur * ratio) * sin(angle))
					return (x,y,angle)
				else:
					lin_cum += lin_cur

def alt_str_name_mc(name, src='unset', aieou=1):
	# Alt names for misspelled address list content
	if not name:
		return ""
#	QgsMessageLog.logMessage(''.join(('name in: ',name,';src: ',src)))
	# name = unicode(name).strip().lower()
	name = name.strip().lower()
	
	# jja block start
	name = name.replace(u'dr. ', u'')
	name = name.replace(u'-', u' ')
	name = name.replace(u'szent ', u'szent')

	# jja block start
	name = name.replace(u'  ', u' ')
	
	name = name.replace(u'ä', u'a')
	name = name.replace(u'ë', u'e')
	name = name.replace(u'ú', u'u')
	name = name.replace(u'ó', u'o')
	name = name.replace(u'í', u'i')
	name = name.replace(u'th', u't')

#	name = name.replace(u'wi', u'w')
	name = name.replace(u'w', u'v')
	name = name.replace(u'vy', u'w')
	name = name.replace(u'viii', u'8')
	name = name.replace(u'vii', u'7')
	name = name.replace(u'vi', u'w')
	
	name = name.replace(u'xiii', u'9')
	name = name.replace(u'xii', u'5')
	name = name.replace(u'xi', u'z')
	
	name = name.replace(u' iii', u' 3')
	name = name.replace(u' ii', u' 2')
	name = name.replace(u' i', u' 1')
	name = name.replace(u'iii.', u'3')
	name = name.replace(u'ii.', u'2')
	name = name.replace(u'i.', u'1')
	name = name.replace(u'iii-', u'3')
	name = name.replace(u'ii-', u'2')
	name = name.replace(u'i-', u'1')

	if aieou == 1:
		name = name.replace(u'õ', u'ö')
		name = name.replace(u'û', u'ü')
	if aieou > 1:
		name = name.replace(u'õ', u'o')
		name = name.replace(u'û', u'u')
		name = name.replace(u'ö', u'o')
		name = name.replace(u'ü', u'u')
		if aieou > 2:
			name = name.replace(u'á', u'a')
			name = name.replace(u'é', u'e')
			name = name.replace(u'h', u'')
			name = name.replace(u' tere', u' t')
			name = name.replace(u' ter', u' t')
			if aieou < 5:
				name = name.replace(u'sz', u's')

	name = name.replace(u'y', u'i')
	name = name.replace(u'aa', u'a')
	name = name.replace(u'ii', u'i')
	name = name.replace(u'oo', u'o')
	name = name.replace(u'cz', u'c')
	name = name.replace(u'ch', u'c')
	name = name.replace(u'cs', u'c')
	name = name.replace(u'ts', u'c')
	name = name.replace(u'ff', u'f')
	name = name.replace(u'kk', u'k')
	name = name.replace(u'll', u'l')
	name = name.replace(u'nn', u'n')
	name = name.replace(u'pp', u'p')
	name = name.replace(u'ss', u's')
	name = name.replace(u'tt', u't')
	
	name_ar = name.split()
	if len(name_ar) > 2:
		# second name stripped from reference
		# good in case it is missing from address list
		if aieou == 3:
			name_ar[1] = name_ar[1][0]
		name = ' '.join(name_ar)
		if aieou > 3:
#			name_ar[1] = ''
			name_ar[1] = name_ar[1][0]
			if aieou > 4 and len(name_ar) > 3:
				name_ar[2] = ''
			name = ' '.join(name_ar)
	if len(name_ar) == 1:
		name = ''.join((name, u' utca'))
	if aieou > 2:
		if len(name_ar) == 2:
			name = ''.join((name, u' utca'))
			name = name.replace(u' t utca', u' t')
			name_ar = name.split()
			if len(name_ar) > 2:
				if aieou == 4:
					name_ar[1] = name_ar[1][0]
					name = ' '.join(name_ar)
				if aieou > 4:
					name_ar[1] = ''
					if aieou > 5 and len(name_ar) > 3:
						name_ar[2] = ''
					name = ' '.join(name_ar)
		name = name.replace(u' utja', u' y')
		name = name.replace(u' utca', u' y')
		name = name.replace(u' ut', u' y')
		if aieou > 3:
			name = name.replace(u'korter', u'krt')
			name = name.replace(u'o y', u'qxqy')
			name = name.replace(u'o', u'')
			name = name.replace(u'u', u'')
			if aieou > 4:
				# use with caution
				name = name.replace(u'a', u'')
				name = name.replace(u'e', u'')
				name = name.replace(u'i', u'')

	name = name.replace(u'.', u'')
	name = name.replace(u' ', u'')
	name = name.replace(u'yy', u'y')
	name = name.replace(u'sory', u'sor')
	# more source-specific steps tob be added
	# jja tmp block end
#	QgsMessageLog.logMessage(''.join(('name out: ',name,';src: ',src)))
	return name

# --------------------------------------------------------
#    MMQGIS Utility Functions
# --------------------------------------------------------

# Needed to replace the useful function QgsVectorLayer::featureAtId()
# that was tantalizingly added in 1.9 but then removed

def mmqgis_feature_at_id(layer, featureid):

	iterator = layer.getFeatures(QgsFeatureRequest(featureid))
	feature = QgsFeature()
	if iterator.nextFeature(feature):
		return feature

	return None

def mmqgis_find_layer(layer_name):
	# print "find_layer(" + str(layer_name) + ")"

	for name, search_layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
		# print unicode(search_layer.name()) + " ?= " + unicode(layer_name)
		if search_layer.name() == layer_name:
			return search_layer

	return None

def mmqgis_is_float(s):
	try:
		float(s)
		return True
	except:
		return False

# Cumbersome function to give backward compatibility before python 2.7

def mmqgis_format_float(value, separator, decimals):
	formatstring = ("%0." + unicode(int(decimals)) + "f")
	# print str(value) + ": " + formatstring
	string = formatstring % value
	intend = string.find('.')
	if intend < 0:
		intend = len(string)

	if separator and (intend > 3):
		start = intend % 3
		if start == 0:
			start = 3
		intstring = string[0:start]

		for x in range(start, intend, 3):
			intstring = intstring + separator + string[x:x+3]

		string = intstring + string[intend:]

	return string

def mmqgis_gridify_points(hspacing, vspacing, points):
	# Align points to grid
	point_count = 0
	deleted_points = 0
	newpoints = []
	for point in points:
		point_count += 1
		newpoints.append(QgsPoint(round(point.x() / hspacing, 0) * hspacing, \
				    round(point.y() / vspacing, 0) * vspacing))

	# Delete overlapping points
	z = 0
	while z < (len(newpoints) - 2):
		if newpoints[z] == newpoints[z + 1]:
			newpoints.pop(z + 1)
			deleted_points += 1
		else:
			z += 1

	# Delete line points that go out and return to the same place
	z = 0
	while z < (len(newpoints) - 3):
		if newpoints[z] == newpoints[z + 2]:
			newpoints.pop(z + 1)
			newpoints.pop(z + 1)
			deleted_points += 2
			# Step back to catch arcs
			if (z > 0):
				z -= 1
		else:
			z += 1

	# Delete overlapping start/end points
	while (len(newpoints) > 1) and (newpoints[0] == newpoints[len(newpoints) - 1]):
		newpoints.pop(len(newpoints) - 1)
		deleted_points += 2
				
	return newpoints, point_count, deleted_points


# http://stackoverflow.com/questions/3410976/how-to-round-a-number-to-significant-figures-in-python

def mmqgis_round(number, digits):
	if (number == 0):
		return 0
	else:
		return round(number, digits - int(floor(log10(abs(number)))) - 1)


def mmqgis_searchable_streetname(name):
	# Use common address abbreviations to reduce naming discrepancies and improve hit ratio
	# print "searchable_name(" + str(name) + ")"
	if not name:
		return ""
	# name = unicode(name).strip().lower()
	name = name.strip().lower()

	name = name.replace(".", "")
	name = name.replace(" street", " st")
	name = name.replace(" avenue", " av")
	name = name.replace(" plaza", " plz")
	name = name.replace(" drive", " dr")
	name = name.replace("saint ", "st ")
	name = name.replace("fort ", "ft ")
	name = name.replace(" ave", " av")

	name = name.replace("east", "e")
	name = name.replace("west", "w")
	name = name.replace("north", "n")
	name = name.replace("south", "s")
	name = name.replace("1st", "1")
	name = name.replace("2nd", "2")
	name = name.replace("3rd", "3")
	name = name.replace("4th", "4")
	name = name.replace("5th", "5")
	name = name.replace("6th", "6")
	name = name.replace("7th", "7")
	name = name.replace("8th", "8")
	name = name.replace("9th", "9")
	name = name.replace("0th", "0")
	name = name.replace("1th", "1")
	name = name.replace("2th", "2")
	name = name.replace("3th", "3")
	return name

def mmqgis_geocode_address_google(address):
	url = "http://maps.googleapis.com/maps/api/geocode/xml?sensor=false&address=" + address
	try:
		xml = urllib2.urlopen(url).read()

	except:
		# URLError as e: e.reason
		return "Failure connecting to maps.googleapis.com", None, None, None, None

	if (xml.find('OVER_QUERY_LIMIT') > 0):
		return "Exceeded Daily Google Limit", None, None, None, None
		

	#print(url)
	resultstart = 0

	x = []
	y = []
	addrtype = []
	addrlocat = []
	formatted_addr = []
	
	resultstart = xml.find("<result>")
	while (resultstart > 0):
		resultend = xml.find("</result>", resultstart)
		if (resultend < 0):
			resultend = len(xml)
		result = xml[resultstart:resultend]
		resultstart = xml.find("<result>", resultend)

		latstart = result.find("<lat>")
		latend = result.find("</lat>")
		if (latstart < 0) or (latend < (latstart + 5)):
			continue

		longstart = result.find("<lng>")
		longend = result.find("</lng>")
		if (longstart < 0) and (longend < (longstart + 5)):
			continue

		y.append(float(result[latstart + 5:latend]))
			
		x.append(float(result[longstart + 5:longend]))

		addrtypestart = result.find("<type>")
		addrtypeend = result.find("</type>")
		if (addrtypestart > 0) and (addrtypeend > (addrtypestart + 6)):
			addrtype.append(unicode(result[(addrtypestart + 6):addrtypeend], 'utf-8').strip())
		else:
			addrtype.append("")

		addrlocatstart = result.find("<location_type>")
		addrlocatend = result.find("</location_type>")
		if (addrlocatstart > 0) and (addrlocatend > (addrlocatstart + 15)):
			addrlocat.append(unicode(result[(addrlocatstart + 15):addrlocatend], 'utf-8').strip())
		else:
			addrlocat.append("")

		formstart = result.find("<formatted_address>")
		formend = result.find("</formatted_address>")
		if (formstart > 0) and (formend > (formstart + 19)):
			formatted_addr.append(unicode(result[(formstart + 19):formend], 'utf-8').strip())
		else:
			formatted_addr.append(address)

	return x, y, addrtype, addrlocat, formatted_addr


def mmqgis_geocode_address_osm(address):
	url = "http://nominatim.openstreetmap.org/search?format=xml&q=" + address
	try:
		osm = urllib2.urlopen(url).read()

	except URLError as e:
		return e.reason, None, None, None, None
	# print(url)
	# print(osm)

	x = []
	y = []
	addrtype = []
	addrlocat = []
	formatted_addr = []

	# Parse the XML
	try:
		results = xml.etree.ElementTree.fromstring(osm)
		# results = tree.getroot()
	except:
		print("XML Parser Failure")
		return None, None, None, None, None

	# Parse <place> under <searchresults>
	for place in results:
		try:
			lat = place.attrib['lat']
			lon = place.attrib['lon']
		except:
			lat = None
			lon = None

		try:
			aclass = place.attrib['class']
		except:
			aclass = ""

		try:
			atype = place.attrib['type']
		except:
			atype = ""

		try:
			aname = place.attrib['display_name']
		except:
			aname = ""

		# print(lat, lon)

		if (lat != None) and (lon != None):
			x.append(float(lon))
			y.append(float(lat))
			addrtype.append(aclass)
			addrlocat.append(atype)
			formatted_addr.append(aname)

	return x, y, addrtype, addrlocat, formatted_addr


# Legacy code left here for reference if anything breaks in new XML parsing 1/31/2016

def mmqgis_old_geocode_address_osm(address):
	url = "http://nominatim.openstreetmap.org/search?format=xml&q=" + address
	try:
		xml = urllib2.urlopen(url).read()

	except:
		# URLError as e: e.reason
		return "Failure connecting to nominatim.openstreetmap.org", None, None, None, None
	#print(url)
	#print(xml)

	x = []
	y = []
	addrtype = []
	addrlocat = []
	formatted_addr = []

	placestart = xml.find("<place")
	while (placestart > 0):
		placeend = xml.find("/>", placestart)
		if (placeend < 0):
			placeend = len(xml)
		place = xml[placestart:placeend]
		placestart = xml.find("<place", placeend)

		latstart = place.find('lat="')
		latend = place.find('"', latstart + 5)
		if (latstart < 0) or (latend < (latstart + 5)):
			continue

		longstart = place.find('lon="')
		longend = place.find('"', longstart + 5)
		if (latstart < 0) or (latend < (latstart + 5)):
			continue

		y.append(float(place[latstart + 5:latend]))

		x.append(float(place[longstart + 5:longend]))

		addrtypestart = place.find("class=")
		addrtypeend = place.find("'", addrtypestart + 7)
		if (addrtypestart > 0) and (addrtypeend > (addrtypestart + 7)):
			addrtype.append(unicode(place[(addrtypestart + 7):addrtypeend], 'utf-8').strip())
		else:
			addrtype.append("")

		addrlocatstart = place.find("type=")
		addrlocatend = place.find("'", addrlocatstart + 6)
		if (addrlocatstart > 0) and (addrlocatend > (addrlocatstart + 6)):
			addrlocat.append(unicode(place[(addrlocatstart + 6):addrlocatend], 'utf-8').strip())
		else:
			addrlocat.append("")

		formstart = place.find("display_name=")
		formend = place.find("'", formstart + 14)
		if (formstart > 0) and (formend > (formstart + 14)):
			formatted_addr.append(unicode(place[(formstart + 14):formend], 'utf-8').strip())
		else:
			formatted_addr.append(address)

	return x, y, addrtype, addrlocat, formatted_addr


def mmqgis_wkbtype_to_text(wkbtype):
	if wkbtype == QGis.WKBUnknown: return "Unknown"
	if wkbtype == QGis.WKBPoint: return "point"
	if wkbtype == QGis.WKBLineString: return "linestring"
	if wkbtype == QGis.WKBPolygon: return "polygon"
	if wkbtype == QGis.WKBMultiPoint: return "multipoint"
	if wkbtype == QGis.WKBMultiLineString: return "multilinestring"
	if wkbtype == QGis.WKBMultiPolygon: return "multipolygon"
	if wkbtype == QGis.WKBPoint25D: return "point 2.5d"
	if wkbtype == QGis.WKBLineString25D: return "linestring 2.5D"
	if wkbtype == QGis.WKBPolygon25D: return "polygon 2.5D"
	if wkbtype == QGis.WKBMultiPoint25D: return "multipoint 2.5D"
	if wkbtype == QGis.WKBMultiLineString25D: return "multilinestring 2.5D"
	if wkbtype == QGis.WKBMultiPolygon25D: return "multipolygon 2.5D"
	return "Unknown WKB " + unicode(wkbtype)

def mmqgis_status_message(qgis, message):
	qgis.mainWindow().statusBar().showMessage(message)

def mmqgis_completion_message(qgis, message):
	mmqgis_status_message(qgis, message)
	qgis.messageBar().pushMessage(message, 0, 3)

def mmqgis_distance(start, end):
	# Assumes points are WGS 84 lat/long
	# Returns great circle distance in meters
	radius = 6378137 # meters
	flattening = 1/298.257223563

	# Convert to radians with reduced latitudes to compensate
	# for flattening of the earth as in Lambert's formula
	start_lon = start.x() * math.pi / 180
	start_lat = math.atan2((1 - flattening) * sin(start.y() * math.pi / 180), cos(start.y() * math.pi / 180))
	end_lon = end.x() * math.pi / 180
	end_lat = math.atan2((1 - flattening) * sin(end.y() * math.pi / 180), cos(end.y() * math.pi / 180))

	# Haversine formula
	arc_distance = (math.sin((end_lat - start_lat) / 2) ** 2) + \
		(math.cos(start_lat) * math.cos(end_lat) * (math.sin((end_lon - start_lon) / 2) ** 2))

	return 2 * radius * math.atan2(math.sqrt(arc_distance), math.sqrt(1 - arc_distance))

def mmqgis_bearing(start, end):
	# Assumes points are WGS 84 lat/long
	# http://www.movable-type.co.uk/scripts/latlong.html

	start_lon = start.x() * math.pi / 180
	start_lat = start.y() * math.pi / 180
	end_lon = end.x() * math.pi / 180
	end_lat = end.y() * math.pi / 180

	return math.atan2(math.sin(end_lon - start_lon) * math.cos(end_lat), \
		(math.cos(start_lat) * math.sin(end_lat)) - \
		(math.sin(start_lat) * math.cos(end_lat) * math.cos(end_lon - start_lon))) \
		* 180 / math.pi

def mmqgis_endpoint(start, distance, degrees):
	# Assumes points are WGS 84 lat/long, distance in meters,
	# bearing in degrees with north = 0, east = 90, west = -90
	# http://www.movable-type.co.uk/scripts/latlong.html
	radius = 6378137.0 # meters

	start_lon = start.x() * math.pi / 180
	start_lat = start.y() * math.pi / 180
	bearing = degrees * math.pi / 180

	end_lat = math.asin((math.sin(start_lat) * math.cos(distance / radius)) +
		(math.cos(start_lat) * math.sin(distance / radius) * math.cos(bearing)))
	end_lon = start_lon + math.atan2( \
		math.sin(bearing) * math.sin(distance / radius) * math.cos(start_lat),
		math.cos(distance / radius) - (math.sin(start_lat) * math.sin(end_lat)))

	return QgsPoint(end_lon * 180 / math.pi, end_lat * 180 / math.pi)


def mmqgis_feet_to_meters(feet):
	return feet / 3.2808399

def mmqgis_meters_to_feet(meters):
	return meters * 3.2808399

def mmqgis_miles_to_meters(miles):
	return miles * 1609.344

def mmqgis_meters_to_miles(meters):
	return meters / 1609.344

#chm = QgsPoint(-88.241161, 40.115742)
#dav = QgsPoint(-88.226386,40.1072)
#chi = QgsPoint(-87.640368,41.877438)
#jan = QgsPoint(-90.191065, 32.301516)
#ufl = QgsPoint(-88.209445, 40.111328)


def mmqgis_buffer_geometry(geometry, meters):
	if meters <= 0:
		return None

	# To approximate meaningful meter distances independent of the original CRS,
	# the geometry is transformed to an azimuthal equidistant projection
	# with the center of the polygon as the origin. After buffer creation,
	# the buffer is transformed to WGS 84 and returned. While this may introduce
	# some deviation from the original CRS, buffering is assumed in practice
	# to be a fairly inexact operation that can tolerate such deviation

	wgs84 = QgsCoordinateReferenceSystem()
	wgs84.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")

	latitude = str(geometry.centroid().asPoint().y())
	longitude = str(geometry.centroid().asPoint().x())

	#proj4 = "+proj=aeqd +lat_0=" + str(geometry.centroid().asPoint().y()) + \
	#	" +lon_0=" + str(geometry.centroid().asPoint().x()) + \
	#	" +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"

	# For some reason, Azimuthal Equidistant transformation noticed to not be
	# working on 10 July 2014. World Equidistant Conic works, but there may be errors.
	proj4 = "+proj=eqdc +lat_0=0 +lon_0=0 +lat_1=60 +lat_2=60 " + \
		"+x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

	azimuthal_equidistant = QgsCoordinateReferenceSystem()
	azimuthal_equidistant.createFromProj4(proj4)
	
	transform = QgsCoordinateTransform(wgs84, azimuthal_equidistant)
	geometry.transform(transform)

	newgeometry = geometry.buffer(meters, 7)

	wgs84 = QgsCoordinateReferenceSystem()
	wgs84.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")

	transform = QgsCoordinateTransform(azimuthal_equidistant, wgs84)
	newgeometry.transform(transform)

	return newgeometry


def mmqgis_buffer_point(point, meters, edges):
	if (meters <= 0) or (edges < 3):
		return None

	# Points are treated separately from other geometries so that discrete
	# edges can be supplied for non-circular buffers that are not supported
	# by the QgsGeometry.buffer() function

	wgs84 = QgsCoordinateReferenceSystem()
	wgs84.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")

	# print "Point " + unicode(point.x()) + ", " + unicode(point.y()) + " meters " + unicode(meters)

	polyline = []
	for edge in range(0, edges + 1):
		polyline.append(mmqgis_endpoint(point, meters, float(edge) * 360.0 / float(edges)))

	return QgsGeometry.fromPolygon([polyline])


def mmqgis_buffer_line_side(geometry, width, direction):
	# width in meters
	# direction should be 0 for north side, 90 for east, 180 for south, 270 for west

	# print "\nmmqgis_buffer_line_side(" + unicode(direction) + ")"

	if (geometry.wkbType() == QGis.WKBMultiLineString) or \
	   (geometry.wkbType() == QGis.WKBMultiLineString25D):
		multipolygon = None
		for line in geometry.asMultiPolyline():
			segment = mmqgis_buffer_line_side(QgsGeometry.fromPolyline(line), width, direction)
			if multipolygon == None:
				multipolygon = segment
			else:
				multipolygon = multipolygon.combine(segment)
			# print "  Build multipolygon " + str(multipolygon.isGeosValid())

		# Multiline always has multipolygon buffer even if buffers merge into one polygon
		if multipolygon.wkbType() == QGis.WKBPolygon:
			multipolygon = QgsGeometry.fromMultiPolygon([multipolygon.asPolygon()])

		# print "Final Multipolygon " + str(multipolygon.isGeosValid())
		return multipolygon

	if (geometry.wkbType() != QGis.WKBLineString) and \
	   (geometry.wkbType() != QGis.WKBLineString25D):
		return geometry

	points = geometry.asPolyline()
	line_bearing = mmqgis_bearing(points[0], points[-1]) % 360

	# Determine side of line to buffer based on angle from start point to end point
	# "bearing" will be 90 for right side buffer, -90 for left side buffer
	direction = round((direction % 360) / 90) * 90
	if (direction == 0): # North
		if (line_bearing >= 180):
			bearing = 90 # Right
		else:
			bearing = -90 # Left

	elif (direction == 90): # East
		if (line_bearing >= 270) or (line_bearing < 90):
			bearing = 90 # Right
		else:
			bearing = -90 # Left

	elif (direction == 180): # South
		if (line_bearing < 180):
			bearing = 90 # Right
		else:
			bearing = -90 # Left

	else: # West
		if (line_bearing >= 90) and (line_bearing < 270):
			bearing = 90 # Right
		else:
			bearing = -90 # Left

	# Buffer individual segments
	polygon = None
	for z in range(0, len(points) - 1):
		b1 = mmqgis_bearing(points[z], points[z + 1]) % 360

		# Form rectangle beside line 
		# 2% offset mitigates topology floating-point errors
		linestring = [QgsPoint(points[z])]
		if (z == 0):
			linestring.append(mmqgis_endpoint(points[z], width, b1 + bearing))
		else:
			linestring.append(mmqgis_endpoint(points[z], width, b1 + (1.02 * bearing)))
		linestring.append(mmqgis_endpoint(points[z + 1], width, b1 + bearing))

		# Determine if rounded convex elbow is needed
		if (z < (len(points) - 2)):
			b2 = mmqgis_bearing(points[z + 1], points[z + 2]) % 360
			elbow = b2 - b1
			if (elbow < -180):
				elbow = elbow + 360
			elif (elbow > 180):
				elbow = elbow - 360

			# print unicode(b1) + ", " + unicode(b2) + " = " + unicode(elbow)

			# 8-step interpolation of arc
			if (((bearing > 0) and (elbow < 0)) or \
			    ((bearing < 0) and (elbow > 0))): 
				for a in range(1,8):
					b = b1 + (elbow * a / 8.0) + bearing
					linestring.append(mmqgis_endpoint(points[z + 1], width, b))
					# print "  arc: " + unicode(b)

				linestring.append(mmqgis_endpoint(points[z + 1], width, b2 + bearing))

		# Close polygon
		linestring.append(QgsPoint(points[z + 1]))
		linestring.append(QgsPoint(points[z]))	
		segment = QgsGeometry.fromPolygon([linestring])
		# print linestring
		# print "  Line to polygon " + str(segment.isGeosValid())

		if (polygon == None):
			polygon = segment
		else:
			polygon = polygon.combine(segment)

		#print "  Polygon build " + str(polygon.isGeosValid())
		#if not polygon.isGeosValid():
		#	print polygon.asPolygon()

	# print "  Final polygon " + str(polygon.isGeosValid())

	return polygon


# --------------------------------------------------------
#    mmqgis_animate_columns - Create animations by
#		interpolating offsets from attributes
# --------------------------------------------------------

def mmqgis_animate_columns(qgis, layer_name, long_col, lat_col, outdir, frame_count):

	# Error Checks
	layer = mmqgis_find_layer(layer_name)
	if layer == None:
		return "Invalid map layer ID: " + unicode(map_layer_id)

	long_col_index = layer.dataProvider().fieldNameIndex(long_col)
	if (long_col_index < 0):
		return "Invalid longitude column index: " + unicode(long_col)

	lat_col_index = layer.dataProvider().fieldNameIndex(lat_col)
	if (lat_col_index < 0):
		return "Invalid latitude column: " + unicode(lat_col)

	if not os.path.isdir(outdir):
		return "Invalid output directory: " + unicode(outdir)

	if frame_count <= 0:
		return "Invalid number of frames specified: " + unicode(frame_count)

	# Find differential change with each frame
	feature_id = []
	xdifferential = []
	ydifferential = []

	for feature in layer.dataProvider().getFeatures():
		attributes = feature.attributes()
		try:
			xtotal = float(attributes[long_col_index])
			ytotal = float(attributes[lat_col_index])
		except:
			xtotal = 0
			ytotal = 0

		feature_id.append(feature.id())
		xdifferential.append(xtotal / frame_count)
		ydifferential.append(ytotal / frame_count)

	# for feature in range(0, len(xdifferential)):
	#	print "Differentials: " + unicode(xdifferential[feature]) + ", " + unicode(ydifferential[feature])

	# Iterate Frames

	for frame in range(frame_count + 1):
		mmqgis_status_message(qgis, "Rendering frame " + unicode(frame))

		# Shift shapes

		layer.startEditing()

		for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
			geometry = QgsGeometry(feature.geometry())
			geometry.translate(xdifferential[feature_index] * frame, 
				ydifferential[feature_index] * frame)
			# print unicode(geometry.asPoint().x()) + " - " + unicode(geometry.asPoint().y())
			layer.changeGeometry(feature_id[feature_index], geometry)

		# Write Frame

		# qgis.mapCanvas().refreshMap()
		pixmap = QPixmap(qgis.mapCanvas().mapSettings().outputSize().width(), 
			qgis.mapCanvas().mapSettings().outputSize().height())

		framefile = outdir + "/frame" + format(frame, "06d") + ".png"
		qgis.mapCanvas().saveAsImage(framefile, pixmap)

		# Clean up: Constantly starting and stopping editing is slow, 
		# but leaving editing open and accumulating successive changes
		# seems to be even slower (6/5/2014)

		layer.rollBack()

	return None

# --------------------------------------------------------
#    mmqgis_animate_lines
# --------------------------------------------------------

def mmqgis_animate_lines(qgis, layer_name, fixed_speed, frame_count, outdir):

	# Error Checks
	layer = mmqgis_find_layer(layer_name)
	if layer == None:
		return "Invalid map layer: " + unicode(layer_name)
	
	if (layer.type() != QgsMapLayer.VectorLayer) or\
	   ((layer.dataProvider().geometryType() != QGis.WKBLineString) and \
	    (layer.dataProvider().geometryType() != QGis.WKBLineString25D) and \
	    (layer.dataProvider().geometryType() != QGis.WKBMultiLineString) and \
	    (layer.dataProvider().geometryType() != QGis.WKBMultiLineString25D)):
		return "Not a line layer: " + unicode(layer_name)
	
	if not os.path.isdir(outdir):
		return "Invalid output directory: " + unicode(outdir)

	if frame_count <= 0:
		return "Invalid number of frames specified: " + unicode(frame_count)

	# Convert features to lists of points
	points = []
	length = []
	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):

		fpoints = []
		if (feature.geometry().wkbType() == QGis.WKBLineString):
			fpoints = feature.geometry().asPolyline()

		elif (feature.geometry().wkbType() == QGis.WKBMultiLineString):
			fpoints = []
			for line in feature.geometry().asMultiPolyline():
				fpoints.extend(line)

		else:
			return "Invalid geometry type " + unicode(feature.geometry().wkbType())

		points.append(fpoints)

		# print unicode(feature_index) + " = " + unicode(len(points)) + \
		#	" = " + unicode(feature.geometry().wkbType()) + " = " + unicode(type(points))

		# Calculate total shape length 
		# Can't use length() function because it does not consider circuity
		flength = 0
		for point in range(0,len(fpoints) - 1):
			flength = flength + \
				sqrt(pow(fpoints[point].x() - fpoints[point + 1].x(), 2) + \
				pow(fpoints[point].y() - fpoints[point + 1].y(), 2))

		length.append(flength)

	max_length = max(length)

	# Iterate Frames
	for frame in range(frame_count + 1):
		mmqgis_status_message(qgis, "Rendering frame " + unicode(frame))

		layer.startEditing()

		for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):

			fpoints = points[feature_index]
			if (len(fpoints) <= 0):
				continue

			if fixed_speed:
				visible_length = min([length[feature_index], max_length * frame / frame_count])
			else:
				visible_length = length[feature_index] * frame / frame_count


			total_length = 0
			visible = [fpoints[0], fpoints[0]]
			for z in range(1, len(fpoints)):
				segment_length = pow(pow(fpoints[z].x() - fpoints[z - 1].x(), 2) + \
					pow(fpoints[z].y() - fpoints[z - 1].y(), 2), 0.5)

				# print "   " + unicode(total_length) + " + " + unicode(segment_length)

				if (total_length >= visible_length):
					break

				elif (total_length + segment_length) <= visible_length:
					visible.append(fpoints[z])
					total_length = total_length + segment_length

				else: # only display part of line segment
					fraction = (visible_length - total_length) / segment_length
					x = fpoints[z - 1].x() + ((fpoints[z].x() - fpoints[z - 1].x()) * fraction)
					y = fpoints[z - 1].y() + ((fpoints[z].y() - fpoints[z - 1].y()) * fraction)
					visible.append(QgsPoint(x, y))
					break

			# print unicode(visible_length) + ", " + unicode(len(visible)) + ", " + \
			#	unicode(total_length) + ", " + unicode(max_length)

			layer.changeGeometry(feature.id(), QgsGeometry.fromPolyline(visible))

		# Write Frame

		pixmap = QPixmap(qgis.mapCanvas().mapSettings().outputSize().width(), 
			qgis.mapCanvas().mapSettings().outputSize().height())

		framefile = outdir + "/frame" + format(frame, "06d") + ".png"
		qgis.mapCanvas().saveAsImage(framefile, pixmap)

		# Clean up: Constantly starting and stopping editing is slow, 
		# but leaving editing open and accumulating successive changes
		# seems to be even slower

		layer.rollBack()

	return None


# --------------------------------------------------------
#    mmqgis_animate_rows - Create animations by
#		displaying successive rows
# --------------------------------------------------------

def mmqgis_animate_rows(qgis, layer_names, outdir):

	# Error Checks
	if not os.path.isdir(outdir):
		return "Invalid output directory: " + unicode(outdir)

	layers = []
	for layer_name in layer_names:
		layer = mmqgis_find_layer(layer_name)
		if layer == None:
			return "Invalid layer name: " + unicode(layer_name)
		layers.append(layer)

	frame_count = 0
	for layer in layers:
		if frame_count < layer.dataProvider().featureCount():
			frame_count = layer.dataProvider().featureCount()

	if frame_count <= 1:
		return "At least one animated layer must have more than one feature"


	# Lists of Feature IDs and fields used for subsetting

	feature_ids = [None] * len(layers)
	subset_fields = []
	for index in range(len(layers)):
		feature_ids[index] = layers[index].allFeatureIds()

		fields = layers[index].dataProvider().fields()
		if (len(fields) <= 0):
			return "Each layer must have at least one attribute"
		subset_fields.append(fields[0].name())


	# Iterate frames

	for frame in range(int(frame_count + 1)):
		mmqgis_status_message(qgis, "Rendering frame " + unicode(frame))

		for layer_index, layer in enumerate(layers):
			if frame < len(feature_ids[layer_index]):
				feature_id = feature_ids[layer_index][frame]
				feature = list(layer.dataProvider().getFeatures(QgsFeatureRequest(feature_id)))[0]
				attribute = feature.attributes()[0]
				subset_string = subset_fields[layer_index] + " = '" + unicode(attribute) + "'"
				# print unicode(layer_index) + ": " + subset_string
				if (not layer.setSubsetString(subset_string)):
					return "Failure subsetting layer: " + subset_string

		# qgis.mapCanvas().refresh()
		pixmap = QPixmap(qgis.mapCanvas().mapSettings().outputSize().width(), 
			qgis.mapCanvas().mapSettings().outputSize().height())

		framefile = outdir + "/frame" + format(frame, "06d") + ".png"
		qgis.mapCanvas().saveAsImage(framefile, pixmap)

		# This is now too hard to do with subsetString

		# if not cumulative:
		#	for layer_index in range(len(layers)):
		#		if frame < layers[layer_index].featureCount():
		#			feature = QgsFeature()
		#			featureid = feature_ids[layer_index][frame]
		#			templayers[layer_index].dataProvider().deleteFeatures([featureid])


	# Restore visibility to all features

	for layer in layers:
		layer.setSubsetString("")

	return None

# ----------------------------------------------------------
#    mmqgis_attribute_export - Export attributes to CSV file
# ----------------------------------------------------------

def mmqgis_attribute_export(qgis, outfilename, layername, attribute_names, field_delimiter, line_terminator, decimal_mark):
	# Error checks

	if (not outfilename) or (len(outfilename) <= 0):
		return "No output CSV file given"
	
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Layer " + layername + " not found"

	# print("Delimiter: ", field_delimiter, " Decimal mark: ", decimal_mark)

	# Find attribute indices
	attribute_indices = []
	if (not attribute_names) or (len(attribute_names) <= 0):
		attribute_names = []
		# print "fields: " + str(layer.dataProvider().fields())
		for index, field in enumerate(layer.dataProvider().fields()):
			attribute_indices.append(index)
			attribute_names.append(field.name())

	else:
		for x in range(0, len(attribute_names)):
			index = layer.dataProvider().fieldNameIndex(attribute_names[x])
			if index < 0:
				return "Layer " + layername + " has no attribute " + attribute_names[x]
			attribute_indices.append(index)

	# Create the CSV file
	try:
		outfile = open(outfilename, 'w')
    	except:
		return "Failure opening " + outfilename

	writer = csv.writer(outfile, delimiter = field_delimiter, lineterminator = line_terminator)

	# Encoding is forced to UTF-8 because CSV writer doesn't support Unicode
	writer.writerow([field.encode("utf-8") for field in attribute_names])

	# Iterate through each feature in the source layer
	feature_count = layer.dataProvider().featureCount()

	#feature = QgsFeature()
	#layer.dataProvider().select(layer.dataProvider().attributeIndexes())
	#layer.dataProvider().rewind()
        #while layer.dataProvider().nextFeature(feature):

	for index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (index % 50) == 0:
			qgis.mainWindow().statusBar().showMessage \
				("Exporting feature " + unicode(feature.id()) + " of " + unicode(feature_count))
		attributes = feature.attributes()

		row = []
		for column in attribute_indices:
			# print unicode(column) + " (" + decimal_mark + "): " + type(attributes[column]).__name__

			if attributes[column] == None:
				row.append("")

			elif type(attributes[column]) == QDate:
				row.append(attributes[column].toString("yyyy-MM-dd"))

			# Non-period decimal mark (probably comma in Europe)
			elif (type(attributes[column]) == float) and (decimal_mark != '.'):
				# print(unicode(attributes[column]).replace('.', decimal_mark))
				row.append(unicode(attributes[column]).replace('.', decimal_mark))
				
			else:
				row.append(attributes[column])

		writer.writerow([unicode(field).encode("utf-8") for field in row])

	del writer

	mmqgis_completion_message(qgis, unicode(feature_count) + " records exported")

	return None


# --------------------------------------------------------
#    mmqgis_attribute_join - Join attributes from a CSV
#                            file to a shapefile
# --------------------------------------------------------

def mmqgis_attribute_join(qgis, layername, infilename, joinfield, targetfield, outfilename, notfoundname, addlayer):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Layer " + unicode(layername) + " not found"

	target_index = layer.fieldNameIndex(targetfield)
	if target_index < 0:
		return "Invalid join attribute " + unicode(targetfield)

	if len(infilename) <= 0:
		return "No input CSV file given"

	if len(outfilename) <= 0:
		return "No output shapefile name given"
		
	# Create a combined field list from the source layer and the CSV file header
	try:
		infile = open(infilename, 'r')
	except:
		return "Failure opening input file: " + unicode(infilename)
			
	try:
		dialect = csv.Sniffer().sniff(infile.read(4096))
	except:
		return "Bad CSV file (verify that your delimiters are consistent)" + unicode(infilename)

	infile.seek(0)
	reader = csv.reader(infile, dialect)

	# Build composite list of fields
	join_index = -1
	newfields = layer.dataProvider().fields()

	# Decode from UTF-8 characters because csv.reader can only handle 8-bit characters
	header = reader.next()
	try:
		header = [unicode(field, "utf-8") for field in header]
	except:
		return "CSV file must be in UTF-8 encoding"


	# Create a combined list of fields with shapefile-safe (<= 10 char) unique names
	for index in range(0, len(header)):
		if header[index].strip().lower() == joinfield.strip().lower():
			join_index = index

		else:
			# Shapefile-safe = 10 characters or less
			fieldname = header[index].strip()[0:10]

			# Rename fields that have duplicate names
			suffix = 1
			while (newfields.indexFromName(fieldname) >= 0):
				suffix = suffix + 1
				if (suffix <= 9):
					fieldname = fieldname[0:9] + unicode(suffix)
				else:
					fieldname = fieldname[0:8] + unicode(suffix)

			# print header[index] + "=" + fieldname
			newfields.append(QgsField(fieldname, QVariant.String))

	if join_index < 0:
		return "Join field " + unicode(joinfield) + " not found in " + unicode(infilename)

	# Create the output shapefile
	if QFile(outfilename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(outfilename):
			return "Failure deleting existing shapefile: " + unicode(outfilename)

	#print newfields

	outfile = QgsVectorFileWriter(outfilename, "utf-8", newfields, 
		layer.dataProvider().geometryType(), layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Read the CSV file data into memory
	csv_data = []
	csv_found = []
	for row in reader:
		csv_data.append(row)
		csv_found.append(0)

	del reader


	# Iterate through each feature in the source layer
	matched_count = 0
	feature_count = layer.dataProvider().featureCount()

	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (feature_index % 50) == 0:
			mmqgis_status_message(qgis, "Joining feature " + unicode(feature_index) + \
					" of " + unicode(feature_count) + " (" + unicode(matched_count) + " matched)")
		attributes = feature.attributes()

		if feature.geometry() == None:
			return "No geometry in layer: " + unicode(layername)

		# Key must be UTF-8 encoded to be comparable with UTF-8 encoded 8-bit characters from CSV file
		key = unicode(attributes[target_index]).encode("utf-8").lower().strip()

		for row_index, row in enumerate(csv_data):
			if row[join_index].strip().lower() == key:
				# print key + " --------------"
				newattributes = []
				for value in attributes:
					newattributes.append(value)
					
				for combine_index, combine in enumerate(row):
					if combine_index != join_index:
						try:
							newattribute = unicode(combine, 'utf-8')
						except:
							return "CSV file does not appear to be UTF-8 encoded: " + unicode(infilename)
						newattributes.append(newattribute)

				newfeature = QgsFeature()
				newfeature.setAttributes(newattributes)
				newfeature.setGeometry(feature.geometry())
				outfile.addFeature(newfeature)
				matched_count += 1
				csv_found[row_index] += 1

	if matched_count <= 0:
		return "No matching records found"

	del outfile
	del infile

	# Write records that were not joined to the notfound file
	try:
		outfile = open(notfoundname, 'w')
	except:
		return "Failure opening not found file: " + unicode(notfoundname)

	else:
		# Detected CSV dialects don't infer escape character
		if not dialect.escapechar:
			dialect.escapechar = '\\'

		writer = csv.writer(outfile, dialect)

		# Encoding is forced to UTF-8 because CSV writer doesn't support Unicode
		writer.writerow([field.encode("utf-8") for field in header])

		for x in range(0, len(csv_data)):
			if not csv_found[x]:
				writer.writerow(csv_data[x])
		del writer
		del outfile
	
	if addlayer:	
		newlayer = qgis.addVectorLayer(outfilename, os.path.basename(outfilename), "ogr")
		newlayer.setProviderEncoding("utf-8")

	mmqgis_completion_message(qgis, unicode(matched_count) + " records joined from " + \
		unicode(feature_count) + " shape records and " + unicode(len(csv_data)) + " CSV file records")

	return None

# --------------------------------------------------------
#    mmqgis_buffers - Create buffers around shapes
# --------------------------------------------------------

def mmqgis_buffers(qgis, layername, radius, unit, shape, savename, selectedonly, addlayer):

	# Error checking
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Layer " + unicode(layername) + " not found"

	if len(savename) <= 0:
		return "No output filename given"

	if type(radius) == float:
		field_index = -1
		if radius <= 0:
			return "Invalid radius: " + unicode(radius)
	else:
		field_index = layer.fieldNameIndex(radius)
		if field_index < 0:
			return "Invalid radius attribute name: " + unicode(radius)

	# Create the output file
	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename
 
	wgs84 = QgsCoordinateReferenceSystem()
	wgs84.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")
	transform = QgsCoordinateTransform(layer.crs(), wgs84)
	# print layer.crs().toProj4() + " -> " + wgs84.toProj4()
	

	outfile = QgsVectorFileWriter(savename, "utf-8",
			layer.dataProvider().fields(), QGis.WKBPolygon, wgs84)

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Create buffers for each feature
	buffercount = 0
	featurecount = layer.dataProvider().featureCount();
	if selectedonly:
		feature_list = layer.selectedFeatures()
	else:
		feature_list = layer.dataProvider().getFeatures()

	for feature_index, feature in enumerate(feature_list):
		mmqgis_status_message(qgis, "Writing feature " + \
			unicode(feature.id()) + " of " + unicode(featurecount))

		if field_index < 0:
			feature_radius = radius
		else:
			try:
				feature_radius = float(feature.attributes()[field_index])
			except:
				feature_radius = 0.0

		if feature_radius > 0:
			# Buffer radii are always in meters
			if unit == "Feet":
				feature_radius = mmqgis_feet_to_meters(feature_radius)

			elif unit == "Miles":
				feature_radius = mmqgis_miles_to_meters(feature_radius)

			elif unit == "Kilometers":
				feature_radius = feature_radius * 1000


			geometry = feature.geometry()
			geometry.transform(transform) # Needs to be WGS 84
			# print "Transform " + unicode(x) + ": " + unicode(geometry.centroid().asPoint().x())

			if (geometry.wkbType() == QGis.WKBPoint) or \
			   (geometry.wkbType() == QGis.WKBPoint25D) or \
			   (geometry.wkbType() == QGis.WKBMultiPoint) or \
			   (geometry.wkbType() == QGis.WKBMultiPoint25D):
				if shape == "Triangle":
					buffer_edges = 3
				elif shape == "Diamond":
					buffer_edges = 4
				elif shape == "Pentagon":
					buffer_edges = 5
				elif shape == "Hexagon":
					buffer_edges = 6
				else: # Circle
					buffer_edges = 32

				newgeometry = mmqgis_buffer_point(geometry.asPoint(), \
					feature_radius, buffer_edges)

			elif (geometry.wkbType() == QGis.WKBLineString) or \
			     (geometry.wkbType() == QGis.WKBLineString25D) or \
			     (geometry.wkbType() == QGis.WKBMultiLineString) or \
			     (geometry.wkbType() == QGis.WKBMultiLineString25D):

				if (shape == "Flat End"):
					# newgeometry = mmqgis_buffer_line_flat_end(geometry, feature_radius)
					north = mmqgis_buffer_line_side(QgsGeometry(geometry), feature_radius, 0)
					south = mmqgis_buffer_line_side(QgsGeometry(geometry), feature_radius, 180)
					newgeometry = north.combine(south)

				elif (shape == "North Side"):
					newgeometry = mmqgis_buffer_line_side(geometry, feature_radius, 0)

				elif (shape == "East Side"):
					newgeometry = mmqgis_buffer_line_side(geometry, feature_radius, 90)

				elif (shape == "South Side"):
					newgeometry = mmqgis_buffer_line_side(geometry, feature_radius, 180)

				elif (shape == "West Side"):
					newgeometry = mmqgis_buffer_line_side(geometry, feature_radius, 270)

				else: # "Rounded"
					newgeometry = mmqgis_buffer_geometry(geometry, feature_radius)
			else:
				newgeometry = mmqgis_buffer_geometry(geometry, feature_radius)

			if newgeometry == None:
				print "Failure converting geometry for feature " + unicode(buffercount)
			else:
				newfeature = QgsFeature()
				newfeature.setGeometry(newgeometry)
				newfeature.setAttributes(feature.attributes())
				outfile.addFeature(newfeature)
		
			buffercount = buffercount + 1

	del outfile

	if addlayer:
		vlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
		
	mmqgis_completion_message(qgis, unicode(buffercount) + " buffers created for " + \
		unicode(featurecount) + " features")

	return None



# --------------------------------------------------------
#    mmqgis_color_ramp - Robust layer coloring
# --------------------------------------------------------

def mmqgis_interpolate_color(scale, lowcolor, midcolor, highcolor):
	if scale <= 0:
		return QColor((lowcolor >> 16) & 0xff, (lowcolor >> 8) & 0xff, lowcolor & 0xff)

	if scale >= 1:
		return QColor((highcolor >> 16) & 0xff, (highcolor >> 8) & 0xff, highcolor & 0xff)

	
	lowred = (lowcolor >> 16) & 0xff
	lowgreen = (lowcolor >> 8) & 0xff
	lowblue = lowcolor & 0xff

	midred = (midcolor >> 16) & 0xff
	midgreen = (midcolor >> 8) & 0xff
	midblue = midcolor & 0xff
		
	highred = (highcolor >> 16) & 0xff
	highgreen = (highcolor >> 8) & 0xff
	highblue = highcolor & 0xff
		
	if scale <= 0.5:
		scale = scale * 2
		red = int((lowred * (1.0 - scale)) + (midred * scale))
		green = int((lowgreen * (1.0 - scale)) + (midgreen * scale))
		blue = int((lowblue * (1.0 - scale)) + (midblue * scale))

	else:
		scale = (scale - 0.5) * 2
		red = int((midred * (1.0 - scale)) + (highred * scale))
		green = int((midgreen * (1.0 - scale)) + (highgreen * scale))
		blue = int((midblue * (1.0 - scale)) + (highblue * scale))

	# print str(scale) + " = " + str(red) + "," + str(green) + "," + str(blue)
	return QColor(red, green, blue)

def mmqgis_color_ramp_symbol(layer, symboltype, symbolsize, thickness, color, border_color):

	if (layer.dataProvider().geometryType() == QGis.WKBPoint) or \
	   (layer.dataProvider().geometryType() == QGis.WKBMultiPoint):
		# core/symbology-ng/qgsmarkersymbollayerv2.cpp
		# "circle", "square", "rectangle", "diamond", "pentagon", "triangle", "star", "arrow"
		#print unicode(symboltype) + ": " + unicode(color.name()) + ", " + \
		#	unicode(border_color.name()) + ", " + unicode(symbolsize)
		symbol_layer = QgsSimpleMarkerSymbolLayerV2(symboltype, color, border_color, float(symbolsize))
		#print unicode(type(symbol_layer))
		symbol = QgsMarkerSymbolV2()
		symbol.changeSymbolLayer(0, symbol_layer)

	elif (layer.dataProvider().geometryType() == QGis.WKBLineString) or \
	     (layer.dataProvider().geometryType() == QGis.WKBMultiLineString):
		symbol_layer = QgsSimpleLineSymbolLayerV2(color, thickness)
		symbol = QgsLineSymbolV2()
		symbol.changeSymbolLayer(0, symbol_layer)

	else: # polygon
		outline_pen = Qt.SolidLine
		if thickness <= 0:
			outline_pen = 0
		symbol_layer = QgsSimpleFillSymbolLayerV2(color, Qt.SolidPattern,
			border_color, outline_pen, float(thickness))
		symbol = QgsFillSymbolV2()
		symbol.changeSymbolLayer(0, symbol_layer)

	return symbol

def mmqgis_ramped_ranges(minimum, maximum, categories, ramptype):
	ranges = []
	for index in range(0, categories):
		if ramptype == "Logarithmic":
			lower = minimum + ((maximum - minimum) * log(index + 1) / log(categories + 1))
			upper = minimum + ((maximum - minimum) * log(index + 2) / log(categories + 1))

		elif ramptype == "Exponential":
			if index == 0:
				lower = 0
			else:
				lower = minimum + ((maximum - minimum) * exp(index - 1) / exp(categories - 1))
			upper = minimum + ((maximum - minimum) * exp(index) / exp(categories - 1))

		elif ramptype == "Square Root":
			lower = minimum + ((maximum - minimum) * sqrt(index) / sqrt(categories))
			upper = minimum + ((maximum - minimum) * sqrt(index + 1) / sqrt(categories))

		elif ramptype == "Squared":
			lower = minimum + ((maximum - minimum) * pow(index, 2) / pow(categories, 2))
			upper = minimum + ((maximum - minimum) * pow(index + 1, 2) / pow(categories, 2))

		else: # linear
			lower = minimum + ((maximum - minimum) * float(index) / float(categories))
			upper = minimum + ((maximum - minimum) * float(index + 1) / float(categories))

		ranges.append([lower, upper])

	return ranges

def mmqgis_legend_label(ranges):
	label = ""
	for index, value in enumerate(ranges):
		formatted_value = mmqgis_round(value, 4)
		if (value >= 1000):
			formatted_value = format(int(formatted_value), ",d")

		label = label + unicode(formatted_value)

		if (index + 1) < len(ranges):
			label = label + " - "

	return label


def mmqgis_set_color_ramp(qgis, layername, fieldname, ramptype, symboltype, symbolsize, 
		thickness, categories, lowcolor, midcolor, highcolor, outlinecolor):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Invalid layer name: " + layername

	# ------- RASTER -------
	if layer.type() == QgsMapLayer.RasterLayer:
		band_number = layer.bandNumber(fieldname)
		if band_number == 0:
			return "Invalid band name: " + fieldname

		if ramptype == "Discrete": # To be implemented
			ramptype = "Linear"
			categories = 100

		if ramptype == "Quantiles": # To be implemented
			ramptype = "Linear"

		if categories < 3:
			return "Invalid number of categories: " + str(categories)

		# print "Band #" + str(band_number)
		# print "Renderer: " + str(layer.renderer().type())

		minimum = layer.dataProvider().minimumValue(band_number)
		maximum = layer.dataProvider().maximumValue(band_number)
		# print "Range: " + str(minimum) + " - " + str(maximum)

		shades = []
		range_list = mmqgis_ramped_ranges(minimum, maximum, categories, ramptype)
		for index, ranges in enumerate(range_list):
			if index == 0:
				value = ranges[0]
			else:
				value = ranges[1]
			color = mmqgis_interpolate_color(float(index) / float(categories - 1), lowcolor, midcolor, highcolor)
			shades.append(QgsColorRampShader.ColorRampItem(value, color, mmqgis_legend_label([value])))

		ramp_shader = QgsColorRampShader(minimum, maximum)
		ramp_shader.setColorRampType(QgsColorRampShader.INTERPOLATED)
		ramp_shader.setColorRampItemList(shades)

		shader = QgsRasterShader(minimum, maximum)
		shader.setRasterShaderFunction(ramp_shader)
		renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), band_number, shader)
		layer.setRenderer(renderer)
		layer.triggerRepaint()
		qgis.legendInterface().refreshLayerSymbology(layer)

		return None

	# ------- VECTOR -------
	max_symbols = 128 # arbitrary limit

	if (symboltype == "mixed"):
		symboltype_list = ["circle", "square", "diamond", "pentagon", "triangle", "star"]
	else:
		symboltype_list = [ symboltype ]

	field_index = layer.fieldNameIndex(fieldname)
	if (field_index < 0):
		return "Invalid field name: " + unicode(fieldname)
	field = layer.dataProvider().fields()[field_index]
	# print "field[" + str(field_index) + "] = " + field.name()

	if ramptype == "Discrete":
		# Get List of discrete values
		values = []
		for feature in layer.dataProvider().getFeatures(QgsFeatureRequest().setFlags(
		    QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([field_index])):
			# attribute = unicode(feature.attribute(fieldname).toString())
			attribute = unicode(feature.attribute(fieldname))
			values.append(attribute)
			# print unicode(feature.id()) + ") " + attribute

		values = set(values)
		if len(values) > max_symbols:
			return unicode(len(values)) + " discrete values exceeds " + unicode(max_symbols) + " limit"
		if len(values) < 2:
			return "Too few discrete values for color ramp"
		values = sorted(values)

		renderer = QgsCategorizedSymbolRendererV2(fieldname)
		for index, value in enumerate(values):
			color = mmqgis_interpolate_color(float(index) / float(len(values) - 1), lowcolor, midcolor, highcolor)
			border_color = QColor((outlinecolor >> 16) & 0xff, (outlinecolor >> 8) & 0xff, outlinecolor % 0xff)
			shape = symboltype_list[index % len(symboltype_list)]
			# print unicode(index) + ") " + unicode(color) + ", " + unicode(border_color) + ", " + unicode(shape)

			symbol = mmqgis_color_ramp_symbol(layer, shape, symbolsize, thickness, color, border_color)
			# print unicode(value) + ": " + unicode(type(value))
			# BUG: Category for integers stored as real will add single decimal place that causes not to display
			category = QgsRendererCategoryV2(value, symbol, unicode(value))
			renderer.addCategory(category)

	elif ramptype == "Quantiles":
		if (field.type() != QVariant.Int) and (field.type() != QVariant.Double):
			return "Only numeric fields can be used with quantiles: " + unicode(fieldname)

		if categories < 3:
			return "Too few categories: " + unicode(categories)

		# Get List of values
		values = []
		for feature in layer.dataProvider().getFeatures(QgsFeatureRequest().setFlags(
		    QgsFeatureRequest.NoGeometry).setSubsetOfAttributes([field_index])):
			#for index, field in enumerate(layer.dataProvider().fields()):
			#	print type(feature.attribute(field.name()))

			# attribute = unicode(feature.attribute(fieldname).toString())
			attribute = unicode(feature.attribute(fieldname))
			try:
				values.append(float(attribute))
			except:
				pass
			# print unicode(feature.id()) + ") " + attribute

		if len(values) < categories:
			return "Too few discrete values for " + str(categories) + " category color ramp"

		values = sorted(values)

		classes = []

		for index in range(0, categories):
			lower = float(values[index * len(values) / categories])
			upper = float(values[((index + 1) * len(values) / categories) - 1])

			color = mmqgis_interpolate_color(float(index) / float(categories - 1), lowcolor, midcolor, highcolor)
			border_color = QColor((outlinecolor >> 16) & 0xff, (outlinecolor >> 8) & 0xff, outlinecolor % 0xff)
			shape = symboltype_list[index % len(symboltype_list)]
				
			symbol = mmqgis_color_ramp_symbol(layer, shape, symbolsize, thickness, color, border_color)

			category = QgsRendererRangeV2(lower, upper, symbol, mmqgis_legend_label([lower, upper]))
			classes.append(category)

		renderer = QgsGraduatedSymbolRendererV2(fieldname, classes)

	else: # Range categories
		if (field.type() != QVariant.Int) and (field.type() != QVariant.Double):
			return "Only numeric fields can be used with quantiles: " + unicode(fieldname)

		if categories < 3:
			return "Too few categories: " + unicode(categories)

		#minimum, mingood = layer.minimumValue(field_index).toDouble()
		#maximum, maxgood = layer.maximumValue(field_index).toDouble()
		try:
			minimum = float(layer.minimumValue(field_index))
			maximum = float(layer.maximumValue(field_index))
		except:
			minimum = 0
			maximum = 0
		range_list = mmqgis_ramped_ranges(minimum, maximum, categories, ramptype)
		classes = []

		for index, ranges in enumerate(range_list):
			color = mmqgis_interpolate_color(float(index) / float(categories - 1), lowcolor, midcolor, highcolor)
			border_color = QColor((outlinecolor >> 16) & 0xff, (outlinecolor >> 8) & 0xff, outlinecolor % 0xff)
			shape = symboltype_list[index % len(symboltype_list)]
			symbol = mmqgis_color_ramp_symbol(layer, shape, symbolsize, thickness, color, border_color)

			category = QgsRendererRangeV2(ranges[0], ranges[1], symbol, 
				mmqgis_legend_label([ranges[0], ranges[1]]))
			classes.append(category)

		renderer = QgsGraduatedSymbolRendererV2(fieldname, classes)

	layer.setRendererV2(renderer)
	layer.triggerRepaint()
	qgis.legendInterface().refreshLayerSymbology(layer)

	return None

#	EXAMPLE WITH OLD RENDERER
#
#	renderer = QgsUniqueValueRenderer(layer.geometryType())
#	for index, value in enumerate(values):
#		symbol = QgsSymbol(layer.geometryType(), unicode(value), unicode(value))
#		color = mmqgis_interpolate_color(float(index) / float(len(values) - 1), lowcolor, midcolor, highcolor)
#		outline_color = QColor((outlinecolor >> 16) & 0xff, (outlinecolor >> 8) & 0xff, outlinecolor % 0xff)
#
#		print str(value) + " = " + unicode(color.name())
#		if (layer.dataProvider().geometryType() == QGis.WKBLineString) or \
#		   (layer.dataProvider().geometryType() == QGis.WKBMultiLineString):
#			symbol.setColor(color)
#		else:
#			symbol.setColor(outline_color)
#
#		symbol.setLineStyle(Qt.SolidLine)
#		symbol.setLineWidth(thickness)
#		symbol.setFillColor(color)
#		symbol.setFillStyle(Qt.SolidPattern)
#		symbol.setNamedPointSymbol(symboltype)
#		symbol.setPointSize(symbolsize)
#		symbol.setPointSizeUnits(False) 
#		# symbol.setScaleClassificationField( it->second->scaleClassificationField() );
#		# symbol.setRotationClassificationField( it->second->rotationClassificationField() );
#		# symbol.setCustomTexture("")
#
#		renderer.insertValue(unicode(value), symbol)
#
#	renderer.updateSymbolAttributes()
#	renderer.setClassificationField(field_index)
#	layer.setRenderer(renderer)
#	layer.triggerRepaint()
#	qgis.legendInterface().refreshLayerSymbology(layer)
#
#	return None


# ---------------------------------------------------------
#    mmqgis_delete_columns - Change text fields to numbers
# ---------------------------------------------------------

def mmqgis_delete_columns(qgis, layername, columns, savename, addlayer):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "No layer specified to modify: " + layername

	if len(savename) <= 0:
		return "No output filename given"

	if len(columns) <= 0:
		return "No columns specified for deletion"

	# Build dictionary of fields excluding fields flagged for deletion
	srcindex = []
	srcfields = QgsFields()
	destfields = QgsFields()
	for index, field in enumerate(layer.dataProvider().fields()):
		keep = 1
		for column in columns:
			if field.name() == column:
				keep = 0

		if keep:
			srcindex.append(index)
			srcfields.append(field)
			destfields.append(field)

	if len(destfields) <= 0:
		return "All columns being deleted"
 
	# Create the output file
	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", destfields,
			layer.dataProvider().geometryType(), layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())


	# Write the features with modified attributes
	featurecount = layer.dataProvider().featureCount();
	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (feature_index % 50) == 0:
			mmqgis_status_message(qgis, "Writing feature " + \
				unicode(feature.id()) + " of " + unicode(featurecount))

		attributes = []
		for index, field in enumerate(srcfields):
			attributes.append(feature.attributes()[srcindex[index]])

		feature.setAttributes(attributes)
		outfile.addFeature(feature)

	del outfile

	if addlayer:
		vlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
		
	mmqgis_completion_message(qgis, unicode(len(columns)) + " columns deleted and written to " + savename)

	return None

# --------------------------------------------------------
#    mmqgis_delete_duplicate_geometries - Save to shaperile
#			while removing duplicate shapes
# --------------------------------------------------------

def mmqgis_delete_duplicate_geometries(qgis, layername, savename, addlayer):

	# Initialization and error checking
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Invalid layer name: " + savename

	if len(savename) <= 0:
		return "No output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", layer.dataProvider().fields(),
			layer.dataProvider().geometryType(), layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Read geometries into an array
	# Have to save as WKT because saving geometries causes segfault 
	# when they are used with equal() later
	geometries = []

	for feature in layer.dataProvider().getFeatures():
		geometries.append(feature.geometry().exportToWkt())

	# NULL duplicate geometries
	for x in range(0, len(geometries) - 1):
		if geometries[x] != None:
			if (x % 20) == 0:
				mmqgis_status_message(qgis, "Checking feature " + unicode(x))

			for y in range(x + 1, len(geometries)):
				#print "Comparing " + str(x) + ", " + str(y)
				if geometries[x] == geometries[y]:
					#print "None " + str(x)
					geometries[y] = None

	# Write unique features to output
	#layer.dataProvider().select(layer.dataProvider().attributeIndexes())
	#layer.dataProvider().rewind()
	#for x in range(0, len(geometries)):
	#	if layer.dataProvider().nextFeature(feature):
	#		if geometries[x] != None:
	#			writecount += 1
	#			outfile.addFeature(feature)

	writecount = 0
	for index, feature in enumerate(layer.dataProvider().getFeatures()):
		if geometries[index] != None:
			writecount += 1
			outfile.addFeature(feature)
				
	del outfile

	if addlayer:
		qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
		
	mmqgis_completion_message(qgis, unicode(writecount) + " of " + \
		unicode(layer.dataProvider().featureCount()) + \
		" unique features written to " + savename)

	return None

# ---------------------------------------------------------
#    mmqgis_float_to_text - String format numeric fields
# ---------------------------------------------------------

def mmqgis_float_to_text(qgis, layername, attributes, separator, 
			decimals, prefix, suffix, savename, addlayer):

	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Project has no active vector layer to convert: " + layername

	if decimals < 0:
		return "Invalid number of decimals: " + unicode(decimals)

	if len(savename) <= 0:
		return "No output filename given"

	# Build dictionary of fields with selected fields for conversion to floating point
	changecount = 0
	fieldchanged = []
	destfields = QgsFields();
	for index, field in enumerate(layer.dataProvider().fields()):
		if field.name() in attributes:
			if (field.type() != QVariant.Int) and (field.type() != QVariant.Double):
				return "Cannot convert non-numeric field: " + unicode(field.name())
		
			changecount += 1
			fieldchanged.append(True)
			destfields.append(QgsField (field.name(), QVariant.String, field.typeName(), \
				20, 0, field.comment()))
		else:
			fieldchanged.append(False)
			destfields.append(QgsField (field.name(), field.type(), field.typeName(), \
				field.length(), field.precision(), field.comment()))

	if (changecount <= 0):
		return "No numeric fields selected for conversion"

	# Create the output file
	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", destfields,
			layer.dataProvider().geometryType(), layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())


	# Write the features with modified attributes
	featurecount = layer.dataProvider().featureCount();
	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (feature_index % 50) == 0:
			mmqgis_status_message(qgis, "Writing feature " + \
				unicode(feature.id()) + " of " + unicode(featurecount))

		attributes = feature.attributes()
		for index, field in enumerate(layer.dataProvider().fields()):
			if fieldchanged[index]:
				# floatvalue, test = attributes[index].toDouble()
				try:
					floatvalue = float(attributes[index])
				except:
					floatvalue = 0
				value = prefix + mmqgis_format_float(floatvalue, separator, decimals) + suffix
				# attributes[index] = QVariant(value)
				attributes[index] = value

		feature.setAttributes(attributes)
		outfile.addFeature(feature)

	del outfile

	if addlayer:
		vlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
		
	mmqgis_completion_message(qgis, unicode(changecount) + " numeric fields converted to text")

	return None

# --------------------------------------------------------------
#    mmqgis_geocode_web_service - Geocode CSV points from Google Maps
# --------------------------------------------------------------

def mmqgis_geocode_web_service(qgis, csvname, shapefilename, notfoundfile, keys, service, addlayer):
	# Read the CSV file header
	if ((service <> "Google Maps") and (service <> "OpenStreetMap / Nominatim")):
		return "Invalid web mapping service name given: " + service

	if (not csvname) or (len(csvname) <= 0):
		return "No CSV address file given"
	
	try:
		infile = open(csvname, 'r')
		dialect = csv.Sniffer().sniff(infile.read(4096))
		infile.seek(0)
		reader = csv.reader(infile, dialect)
		header = reader.next()

	except Exception as e:
		return unicode(csvname) + ": " + unicode(e)

	# Decode from UTF-8 characters because csv.reader can only handle 8-bit characters
	try:
		header = [unicode(field, "utf-8") for field in header]
	except:
		return "CSV file must be in UTF-8 encoding"

	# Create attributes from field names in header

	fields = QgsFields()
	indices = []
	for x in range(0, len(header)):
		for y in range(0, len(keys)):
			if header[x] == keys[y]:
				indices.append(x)

		fieldname = header[x].strip()
		fields.append(QgsField(fieldname[0:10], QVariant.String))

	if (len(fields) <= 0) or (len(indices) <= 0):
		return "No valid location fields in " + csvname


	# Add fields for the <type> and <location_type> returned by Google
	# or the class and type returned by OSM

	fields.append(QgsField("addrtype", QVariant.String))
	fields.append(QgsField("addrlocat", QVariant.String))
	

	# Create the CSV file for ungeocoded records
	try:
		notfound = open(notfoundfile, 'w')

	except Exception as e:
		return unicode(e)

	# Kludge to prevent writer from crashing in Windoze 
	# Opening in local encoding rather than UTF-8?
	dialect.escapechar = '\\' 

	notwriter = csv.writer(notfound, dialect)

	# Encoding is forced to UTF-8 because CSV writer doesn't support Unicode
	notwriter.writerow([field.encode("utf-8") for field in header])

	# Create the output shapefile
	if QFile(shapefilename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(shapefilename):
			return "Failure deleting existing shapefile: " + unicode(shapefilename)

	crs = QgsCoordinateReferenceSystem()
	crs.createFromSrid(4326)
	outfile = QgsVectorFileWriter(shapefilename, "utf-8", fields, QGis.WKBPoint, crs)

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Proxy settings from qgis options settings
	try:
		settings = QSettings()
		proxyEnabled = settings.value("proxy/proxyEnabled", "")
		proxyType = settings.value("proxy/proxyType", "" )
		proxyHost = settings.value("proxy/proxyHost", "" )
		proxyPort = settings.value("proxy/proxyPort", "" )
		proxyUser = settings.value("proxy/proxyUser", "" )
		proxyPassword = settings.value("proxy/proxyPassword", "" )

		# http://stackoverflow.com/questions/1450132/proxy-with-urllib2
		if proxyEnabled == "true":
			proxy = urllib2.ProxyHandler({'http': 'http://' + proxyHost + ':' + proxyPort})
			opener = urllib2.build_opener(proxy)
			urllib2.install_opener(opener)
	except:
		pass

	# Geocode and import
	error = None
	recordcount = 0
	notfoundcount = 0
	for row in reader:
		time.sleep(0.5) # to avoid Google rate quota limits

		recordcount += 1	
		mmqgis_status_message(qgis, "Geocoding " + unicode(recordcount) + 
			" (" + unicode(notfoundcount) + " not found)")

		address = ""
		for x in indices:
			if x < len(row):
				# value = row[x].strip().replace(" ","+")
				try:
					# The unicode coversion throws an exception on non-utf-8 characters
					# However, urllib.quote() requires the encoded string or it throws an error
					utf8_test = unicode(row[x], "utf-8").strip()
					# print utf8_test
					value = urllib2.quote(row[x].strip())
					# print value
				except:
					return "CSV file must be in UTF-8 encoding"

				if len(value) > 0:
					if x != indices[0]:
						address += ",+"
					address += value
						

		if len(address) <= 0:
			notfoundcount += 1
			notwriter.writerow(row)
			continue
	
		if (service == "Google Maps"):
			x, y, addrtype, addrlocat, formatted_addr = mmqgis_geocode_address_google(address)
		else:
			x, y, addrtype, addrlocat, formatted_addr = mmqgis_geocode_address_osm(address)

		# Error condition
		if (x != None) and (y == None):
			error = unicode(x)
			break
			
		elif (x != None) and (len(x) > 0):
			# print address + ": " + str(x) + ", " + str(y)

			attributes = []
			for z in range(0, len(header)):
				if z < len(row):
					# attributes.append(QVariant(unicode(row[z], 'utf-8').strip()))
					attributes.append(unicode(row[z], 'utf-8').strip())

			attributes.append(addrtype[0])
			attributes.append(addrlocat[0])
			
			newfeature = QgsFeature()
			newfeature.setAttributes(attributes)
			geometry = QgsGeometry.fromPoint(QgsPoint(x[0], y[0]))
			newfeature.setGeometry(geometry)
			outfile.addFeature(newfeature)

		else:
			notfoundcount += 1
			notwriter.writerow(row)
				# print xml

	del outfile
	del notfound

	if addlayer and (recordcount > notfoundcount) and (recordcount > 0):
		vlayer = qgis.addVectorLayer(shapefilename, os.path.basename(shapefilename), "ogr")

	if (error != None):
		return error + ": " + unicode(recordcount - notfoundcount - 1) + " addresses geocoded"

	mmqgis_completion_message(qgis, unicode(recordcount - notfoundcount) + " of " + unicode(recordcount)
		+ " addresses geocoded with " + service)

	return None


# --------------------------------------------------------
#    mmqgis_geocode_street_layer - Geocode addresses from street 
#			     address finder shapefile
# --------------------------------------------------------

def mmqgis_geocode_street_layer(qgis, layername, csvname, streetnamefield, numberfield, zipfield, \
	streetname, fromx, fromy, tox, toy, leftfrom, rightfrom, leftto, rightto, leftzip, rightzip, \
	setback, shapefilename, notfoundfile, addlayer, aeiou_qual='1', zip_allowance='0', nr_allowance='0'):

	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Address layer not found: " + layername

	if len(csvname) <= 0:
		return "No CSV address file given"

	# Read the CSV file data into memory
	try:
		infile = open(csvname, 'r')
		dialect = csv.Sniffer().sniff(infile.read(4096))

	except Exception as e:
		return unicode(csvname) + ": " + unicode(e)
	
	infile.seek(0)
	reader = csv.reader(infile, dialect)
	
	# Build attribute fields for geocoded address shapefile
	fields = QgsFields()
	header = reader.next()
	header.append('qual') # jja

	# Decode from UTF-8 characters because csv.reader can only handle 8-bit characters
	try:
		header = [unicode(field, "utf-8") for field in header]
	except:
		return "CSV file must be in UTF-8 encoding"
	
	streetnamefield_index = -1
	numberfield_index = -1
	zipfield_index = -1
	for index, field in enumerate(header):
		if field == streetnamefield:
			streetnamefield_index = index
		if field == numberfield:
			numberfield_index = index
		if (zipfield != None) and (field == zipfield):
			zipfield_index = index
		if field == 'qual': # jja for debug
			qual_index_mc = index # jja for debug
		fields.append(QgsField(field[0:10].strip(), QVariant.String))

#	aeiou_qual = 3 # jja misspelling level if not set from QTForm
	aeiou_qual = int(float(aeiou_qual))
	aeiou = int( 1000 * ( 10 - aeiou_qual))
	zip_allowance = int(float(zip_allowance))
	nr_allowance = int(float(nr_allowance))
	fields.append(QgsField("xref", QVariant.Int)) # jja
	fields.append(QgsField("Longitude", QVariant.Double, "real", 24, 16))
	fields.append(QgsField("Latitude", QVariant.Double, "real", 24, 16))

#	QMessageBox.information(None, "DEBUG:", ''.join(('qual_indx: ',str(qual_index_mc))))
	if streetnamefield_index < 0:
		return "Invalid street name field: " + str(streetnamefield)
	if (numberfield_index < 0):
		return "Invalid street number field: " + str(numberfield)


	# Read CSV addresses into memory and convert to unicode
	addresses = []
	for row in reader:
		for index in range(0, len(row)):
			try:
				row[index] = unicode(row[index], "utf-8")
			except:
				return "CSV file must be in UTF-8 encoding"
		try:
			message = row[numberfield_index]
#			row[numberfield_index] = int(row[numberfield_index]) # org
			# allow float for /a - /g # jja
			row[numberfield_index] = float(row[numberfield_index]) # jja
		except:
			return "Invalid street address number: " + message

#		addresses.append(row) # org
		addresses.append(row + [0]) # jja for quality debug

	del reader
	del infile

	# Create the output shapefile
	if QFile(shapefilename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(shapefilename):
			return "Failure deleting existing shapefile: " + shapefilename

	outfile = QgsVectorFileWriter(shapefilename, "utf-8", fields, QGis.WKBPoint, layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	fromx_attribute = None
	fromy_attribute = None
	tox_attribute = None
	toy_attribute = None
	if (fromx != "(street line start)") and (fromx != "(street line end)"):
		fromx_attribute = layer.dataProvider().fieldNameIndex(fromx)
	if (fromy != "(street line start)") and (fromy != "(street line end)"):
		fromy_attribute = layer.dataProvider().fieldNameIndex(fromy)
	if (tox != "(street line start)") and (tox != "(street line end)"):
		tox_attribute = layer.dataProvider().fieldNameIndex(tox)
	if (toy != "(street line start)") and (toy != "(street line end)"):
		toy_attribute = layer.dataProvider().fieldNameIndex(toy)

	streetname_attribute = layer.dataProvider().fieldNameIndex(streetname)
	leftfrom_attribute = layer.dataProvider().fieldNameIndex(leftfrom)
	rightfrom_attribute = layer.dataProvider().fieldNameIndex(rightfrom)
	leftto_attribute = layer.dataProvider().fieldNameIndex(leftto)
	rightto_attribute = layer.dataProvider().fieldNameIndex(rightto)

	gml_oid_attribute = layer.dataProvider().fieldNameIndex('gml_oid') # jja
	widthleft_attribute = layer.dataProvider().fieldNameIndex('widthleft') # jja
	widthright_attribute = layer.dataProvider().fieldNameIndex('widthright') # jja

	leftzip_attribute = -1
	rightzip_attribute = -1
	if leftzip:
		leftzip_attribute = layer.dataProvider().fieldNameIndex(leftzip)
	if rightzip:
		rightzip_attribute = layer.dataProvider().fieldNameIndex(rightzip)

	# Iterate through each feature in the source layer
	matched_count = 0 # org full match
	str_matched_count_mc = 0 # jja steet name/post code 
	feature_count = layer.dataProvider().featureCount()
	debug_indx_int = {} # jja match matrix
	diff_nr = {} # jja house number diff
	zipp_nr = {} # jja post code match only
	srch_name = {} # jja for searched street name txt
	approx_rows = [] # jja partially matched address rows
	meta_rows = [] # jja holding reference meta data
	feature_indx_mc = 0 # jja
	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (feature.id() % 100) == 0:
			mmqgis_status_message(qgis, "Searching street " + \
				unicode(feature_index) + " of " + unicode(feature_count) + \
				" (" + unicode(matched_count) + " matched)")

		# print "Searching street " + unicode(feature_index) + " of " + unicode(feature_count)

		attributes = feature.attributes()
		# feature_streetname = mmqgis_searchable_streetname(unicode(attributes[streetname_attribute].toString()))
#		feature_streetname = mmqgis_searchable_streetname(unicode(attributes[streetname_attribute])) ## org
#		ftr_alt_strname_u = alt_str_name_mc(unicode(attributes[streetname_attribute]), 'xref_u') ## jja
		ftr_alt_strname = alt_str_name_mc(attributes[streetname_attribute], 'xref', aeiou_qual) ## jja
		# Check each address against this feature
		feature_indx_mc += 1
#		QgsMessageLog.logMessage(''.join(('feature_indx_mc: ',str(feature_indx_mc))))
		row_indx_mc = 0
		for row_index, row in enumerate(addresses):
			street = mmqgis_searchable_streetname(row[streetnamefield_index].lower())
			# print "Compare " + str(feature_streetname) + " ?= " + str(street)

			row_indx_mc += 1
			try:
				diff_nr_test = diff_nr[row_indx_mc]
#				QgsMessageLog.logMessage(''.join(('diff_nr_test: ',str(diff_nr_test))))
			except:
				diff_nr[row_indx_mc] = 99999
#				QgsMessageLog.logMessage(''.join(('row_indx_mc: ',str(row_indx_mc))))
			try:
				zipp_nr_test = zipp_nr[row_indx_mc]
#				QgsMessageLog.logMessage(''.join(('zipp_nr_test: ',str(zipp_nr_test))))
			except:
				zipp_nr[row_indx_mc] = 0
#				QgsMessageLog.logMessage(''.join(('row_indx_mc: ',str(row_indx_mc))))

			gml_oid_number = int(attributes[gml_oid_attribute]) # jja
			# jja outdented for postal code match only
			if zipfield_index >= 0:
				zipcode = row[zipfield_index]
			else:
				zipcode = None
			
#			alt_strname_u = alt_str_name_mc(unicode(row[streetnamefield_index]), 'addr_u') # jja
			alt_strname = alt_str_name_mc(row[streetnamefield_index], 'addr', aeiou_qual) # jja
#			if feature_streetname == street: # org
#			if ftr_alt_strname.encode('utf-8') == alt_strname.encode('utf-8'): # jja
			srch_name[row_indx_mc] = alt_strname
			if ftr_alt_strname == alt_strname: # jja
				debug_indx_int[feature_indx_mc,row_indx_mc] = 750 # jja street name matched (assuming that postal code fully matched)
				row[qual_index_mc] = aeiou + debug_indx_int[feature_indx_mc,row_indx_mc]
				#print "Name match " + str(street) + ", feature " + str(feature.id()) + ": " + \
				#	str(len(attributes)) + "," + str(leftto_attribute) + "," + str(leftfrom_attribute) + \
				#	"," + str(rightto_attribute) + "," + str(rightfrom_attribute)

				# Find range of street numbers on this feature
				#(leftto_number, test) = attributes[leftto_attribute].toInt()
				#(leftfrom_number, test) = attributes[leftfrom_attribute].toInt()
				#(rightto_number, test) = attributes[rightto_attribute].toInt()
				#(rightfrom_number, test) = attributes[rightfrom_attribute].toInt()
				try:
					leftto_number = int(attributes[leftto_attribute])
					leftfrom_number = int(attributes[leftfrom_attribute])
					rightto_number = int(attributes[rightto_attribute])
					rightfrom_number = int(attributes[rightfrom_attribute])
				except:
					leftto_number = 0
					leftfrom_number = 0
					rightto_number = 0
					rightfrom_number = 0
				if leftzip_attribute >= 0:
					# leftzipcode = unicode(attributes[leftzip_attribute].toString())
					leftzipcode = unicode(attributes[leftzip_attribute])
				else:
					leftzipcode = None
				if rightzip_attribute >= 0:
					# rightzipcode = unicode(attributes[leftzip_attribute].toString())
					rightzipcode = unicode(attributes[rightzip_attribute]) # jja
				else:
					rightzipcode = None

				try:
					widthleft_number = int(attributes[widthleft_attribute]) # jja
				except:
					widthleft_number = 0 # jja
				try:
					widthright_number = int(attributes[widthright_attribute]) # jja
				except:
					widthright_number = 0 # jja

				number_mc = float(row[numberfield_index]) # jja accept float for /a - /g
				number = int(number_mc) # jja

				left = ((leftfrom_number % 2) == (number % 2))
				if ((rightfrom_number % 2) == (number % 2)) and (number >= rightfrom_number) \
					and (number <= rightto_number):
					left = False
				if left:
					width_number = widthleft_number # jja
					from_number_mc = leftfrom_number # jja
					to_number_mc = leftto_number # jja
				else:
					width_number = widthright_number # jja
					from_number_mc = rightfrom_number # jja
					to_number_mc = rightto_number # jja
				# allowance for post code alteration
				if zip_allowance == 2:
					zip_diff = 9
				else:
					zip_diff = 0
				try:
					zipcode_int = int(zipcode)
					leftzipcode_int = int(leftzipcode)
					rightzipcode_int = int(rightzipcode)
					leftzip = ((zipcode_int >= leftzipcode_int - zip_diff) and (zipcode_int <= leftzipcode_int + zip_diff))
					rightzip = ((zipcode_int >= rightzipcode_int - zip_diff) and (zipcode_int <= rightzipcode_int + zip_diff))
				except:
#					QgsMessageLog.logMessage('zipcode as was')
					leftzip = ((zipcode == leftzipcode))
					rightzip = ((zipcode == rightzipcode))
				if not (zipcode == rightzipcode) and not (zipcode == leftzipcode):
					debug_indx_int[feature_indx_mc,row_indx_mc] = 550 # jja postal code not matched exactly
					row[qual_index_mc] = aeiou + debug_indx_int[feature_indx_mc,row_indx_mc]
				if not leftzip and not rightzip:
					debug_indx_int[feature_indx_mc,row_indx_mc] = 50 # jja postal code not matched
					row[qual_index_mc] = aeiou + debug_indx_int[feature_indx_mc,row_indx_mc]
				# Check address number
				if ((leftto_number >= leftfrom_number) \
				    and (number >= leftfrom_number) \
				    and (number <= leftto_number) \
				    and ((leftfrom_number % 2) == (number % 2)) \
				    and ((leftzipcode == None) or (zipcode == None) or (leftzip))) or \
				    ((leftto_number < leftfrom_number) \
				    and (number >= leftto_number) \
				    and (number <= leftfrom_number) \
				    and ((leftfrom_number % 2) == (number % 2)) \
				    and ((leftzipcode == None) or (zipcode == None) or (leftzip))) or \
				   ((rightto_number >= rightfrom_number) \
				    and (number >= rightfrom_number) \
				    and (number <= rightto_number) \
				    and ((rightfrom_number % 2) == (number % 2))
				    and ((rightzipcode == None) or (zipcode == None) or (rightzip))) or \
				   ((rightto_number < rightfrom_number) \
				    and (number >= rightto_number) \
				    and (number <= rightfrom_number) \
				    and ((rightfrom_number % 2) == (number % 2))
				    and ((rightzipcode == None) or (zipcode == None) or (rightzip))):
					
					debug_indx_int[feature_indx_mc,row_indx_mc] += 3 # jja house nr matched
					row[qual_index_mc] = aeiou + debug_indx_int[feature_indx_mc,row_indx_mc]
					
					# Find line start and end points
					geometry = feature.geometry()
					length_mc = geometry.length() # jja
					if length_mc < 95:
						# sort street might be narrower -> use smaller setback
						setback_mc = setback / 3 * 2 # jja
					else:
						setback_mc = setback # jja
					if (geometry.wkbType() == QGis.WKBLineString):
						line = geometry.asPolyline()
						fromx = line[0].x()
						fromy = line[0].y()
						tox = line[len(line) - 1].x()
						toy = line[len(line) - 1].y()

					elif (geometry.wkbType() == QGis.WKBMultiLineString):
						lines = geometry.asMultiPolyline()
						line = lines[0]
						fromx = line[0].x()
						fromy = line[0].y()
						line = lines[len(lines) - 1]
						tox = line[len(line) - 1].x()
						toy = line[len(line) - 1].y()
					else:
						return "Street layer must be a lines or multilines"

					# Use attribute values if specified
					try:
						if tox_attribute:
							# (tox, test) = attributes[tox_attribute].toDouble()
							tox = float(attributes[tox_attribute])
						if toy_attribute:
							# (toy, test) = attributes[toy_attribute].toDouble()
							toy = float(attributes[toy_attribute])
						if fromx_attribute:
							# (fromx, test) = attributes[fromx_attribute].toDouble()
							fromx = float(attributes[fromx_attribute])
						if fromy_attribute:
							# (fromy, test) = attributes[fromy_attribute].toDouble()
							fromy = float(attributes[fromy_attribute])
					except:
						tox = 0
						toy = 0
						fromx = 0
						fromy = 0

					# Find percentage distance along street
					# jja: left check outdented
					
					if width_number > 3.0 * setback_mc:
						width_number = 3.0 * setback_mc
					if width_number > length_mc / 4.0:
						width_number = length_mc / 4.0
					
					if width_number < setback_mc:
						width_number = (width_number + setback_mc) / 2.0
					
					
					if (from_number_mc == to_number_mc):
						width_number = 0.0
						ratio = 0.7 + .2 * (int(number % 2 + .1) - 1)
						if rightfrom_number < -2 or leftfrom_number < -2 or number_mc-number > 0: # jja
							if int(number % 2 + .1) == 1:
								ratio = 0.5 - (.9 - (number_mc-number)) / 2.0
							else:
								ratio = 0.5 + .05 + (number_mc-number) / 2.0
					else:
						ratio = float(number_mc - from_number_mc) \
							/ float(to_number_mc - from_number_mc)
						if 3 * width_number < length_mc / ((to_number_mc - from_number_mc) + 1):
							width_number = 3 * width_number
						# >1 in some cases with house nr /a - /g # jja
						if rightfrom_number < -2 or leftfrom_number < -2: # jja
							width_number = 0.0
							if int(number % 2 + .1) == 1:
								ratio = ratio - 0.5 / float(to_number_mc - from_number_mc)
							else:
								ratio = ratio + 0.5 / float(to_number_mc - from_number_mc)
							# leave ratio check here # jja
							if ratio < 0:
								ratio = 0.0
							if ratio > 1:
								ratio = 1.0

					# setback from corner
					angle = atan2(toy - fromy, tox - fromx)
					"""
					## org
					setback_fromx = fromx + (setback * cos(angle))
					setback_tox = tox - (setback * cos(angle))
					setback_fromy = fromy + (setback * sin(angle))
					setback_toy = toy - (setback * sin(angle))
					"""
					setback_fromx = fromx + ((width_number + setback_mc / 2) * cos(angle)) # jja
					setback_tox = tox - ((width_number + setback_mc / 2) * cos(angle)) # jja
					setback_fromy = fromy + ((width_number + setback_mc / 2) * sin(angle)) # jja
					setback_toy = toy - ((width_number + setback_mc / 2) * sin(angle)) # jja

					x = setback_fromx + ((setback_tox - setback_fromx) * ratio)
					y = setback_fromy + ((setback_toy - setback_fromy) * ratio)
					
					# street is curving
					# jja
					length_xy = sqrt(pow(tox - fromx, 2.0) + pow(toy - fromy, 2.0))
					if length_mc > length_xy * 1.001:
						linear_pos = (width_number + setback_mc / 2.0) + \
							((length_mc - (2 * width_number + setback_mc)) * ratio)
						if linear_pos > length_mc:
							# if ratio >>1, putting house nr /a - /g close to corner # jja
							linear_pos = length_mc * 0.95
						(x, y, angle) = lin_int_mc(geometry, linear_pos, (gml_oid_number,width_number,number))

					# setback from house nr /a - /g
					if int((100 * number_mc) % 2 + .1) == 1:
						setback_mc +=  int(10.0 / 3.0 * 2.0 * ((number_mc * 10.0) - int(number_mc * 10.0)) + .4) * 3.0
					# setback from street center
					if left:
						y += (setback_mc * cos(angle))
						x -= (setback_mc * sin(angle))
					else:
						y -= (setback_mc * cos(angle))
						x += (setback_mc * sin(angle))

					
					# Create the output feature
					newattributes = []
					for field in row:
						# newattributes.append(QVariant(field))
						newattributes.append(field)

					newattributes.append(gml_oid_number) # jja
					#newattributes.append(QVariant(x))
					#newattributes.append(QVariant(y))
					newattributes.append(x)
					newattributes.append(y)
					newfeature = QgsFeature()
					newfeature.setAttributes(newattributes)
					geometry = QgsGeometry.fromPoint(QgsPoint(x, y))
					newfeature.setGeometry(geometry)
					outfile.addFeature(newfeature)
					matched_count += 1
					
					# Empty address so not searched further
					row[streetnamefield_index] = ""
					diff_nr[row_indx_mc] = 0
					del debug_indx_int[feature_indx_mc,row_indx_mc] # jja match quality measure
				#print "    End of match"
				try:
					if nr_allowance  == 2 and debug_indx_int[feature_indx_mc,row_indx_mc] > 50:
						# collect street name matches
						if from_number_mc < 0:
							debug_indx_int[feature_indx_mc,row_indx_mc] -= 40
							row[qual_index_mc] = aeiou + debug_indx_int[feature_indx_mc,row_indx_mc]
						diff_nr_test = min(abs(from_number_mc - number), abs(to_number_mc - number))
						if diff_nr_test < diff_nr[row_indx_mc]:
							diff_nr[row_indx_mc] = diff_nr_test # jja
							approx_rows.append(row)
							geom_mc = feature.geometry()
							length_mc = geom_mc.length() # jja
							(x, y, angle) = lin_int_mc(geom_mc, length_mc/2)
							meta_rows.append({'rid':row_indx_mc,'diff':diff_nr_test,'oid':gml_oid_number,'x':x,'y':y})
				except:
					do = None
#			QgsMessageLog.logMessage('Register diff')
#		QgsMessageLog.logMessage('Donno')
	###
	# collect approx. address here
#	QgsMessageLog.logMessage('Add plus (len):')
#	approx_len = len(approx_rows)
#	QgsMessageLog.logMessage(str(approx_len))
#	i = 0
	for i, arow in enumerate(approx_rows):
#		for arow in approx_rows:
		if meta_rows[i]['diff'] == diff_nr[meta_rows[i]['rid']]:
			# choose first match of minimal house nr diff
			oid = meta_rows[i]['oid']
			x = meta_rows[i]['x']
			y = meta_rows[i]['y']
			# Create the output feature
			newattributes = []
			for field in arow:
				# newattributes.append(QVariant(field))
				newattributes.append(field)
			newattributes.append(oid) # jja
			newattributes.append(x)
			newattributes.append(y)
			newfeature = QgsFeature()
			newfeature.setAttributes(newattributes)
			geometry = QgsGeometry.fromPoint(QgsPoint(x, y))
			newfeature.setGeometry(geometry)
			outfile.addFeature(newfeature)
			str_matched_count_mc += 1

			diff_nr[meta_rows[i]['rid']] = 0
			addresses[meta_rows[i]['rid'] - 1][streetnamefield_index] = ''
#		else:
#			QgsMessageLog.logMessage(str(meta_rows[i]['diff']))
#		i +=1
	###

	#print "del outfile 1"
	del outfile

	# Write records that were not joined to the notfound file
	try:
		outfile = open(notfoundfile, 'w')
	except:
		return "Failure opening " + notfoundfile
	else:
                writer = csv.writer(outfile, dialect)
                header.append('srch_name') # jja
                
                # Encoding is forced to UTF-8 because CSV writer doesn't support Unicode
                writer.writerow([field.encode("utf-8") for field in header])

		for index, row in enumerate(addresses):
#			QMessageBox.information(None, "DEBUG:", ''.join(('indx: ',row[streetnamefield_index])))
			if row[streetnamefield_index] > "":
                		row = row + [srch_name[index + 1]]
                		writer.writerow([unicode(field).encode("utf-8") for field in row])

                del outfile


	if (matched_count or str_matched_count_mc) and addlayer:
		#print "addLayer"
		vlayer = qgis.addVectorLayer(shapefilename, os.path.basename(shapefilename), "ogr")
		
	mmqgis_completion_message(qgis, unicode(matched_count) + " (" + unicode(str_matched_count_mc) + ") of " + unicode(len(addresses)) \
		+ " addresses geocoded from " + unicode(feature_count) + " street records")

	return None


# --------------------------------------------------------
#    mmqgis_geometry_convert - Convert geometries to
#		simpler types
# --------------------------------------------------------

def mmqgis_geometry_convert(qgis, layername, newtype, splitnodes, savename, addlayer):
	layer = mmqgis_find_layer(layername)

	if (layer == None) and (layer.type() != QgsMapLayer.VectorLayer):
		return "Invalid Vector Layer " + layername

	# Create output file
	if len(savename) <= 0:
		return "Invalid output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8",
		layer.dataProvider().fields(), newtype, layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Iterate through each feature in the source layer
	feature_count = layer.dataProvider().featureCount()
	out_count = 0

        for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		# shapeid = unicode(feature.id()).strip()

		if (feature_index % 10) == 0:
			mmqgis_status_message(qgis, "Converting feature " + str(feature_index) \
				+ " of " + unicode(feature_count))

		if (feature.geometry().wkbType() == QGis.WKBPoint) or \
		   (feature.geometry().wkbType() == QGis.WKBPoint25D):

			if (newtype == QGis.WKBPoint):
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(QgsGeometry.fromPoint(feature.geometry().asPoint()))
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			else:
				return "Invalid Conversion: " + mmqgis_wkbtype_to_text(feature.geometry().wkbType()) + \
					" to " + mmqgis_wkbtype_to_text(newtype)

		elif (feature.geometry().wkbType() == QGis.WKBLineString) or \
		     (feature.geometry().wkbType() == QGis.WKBLineString25D):

			if (newtype == QGis.WKBPoint) and splitnodes:
				polyline = feature.geometry().asPolyline()
				for point in polyline:
					newfeature = QgsFeature()
					newfeature.setAttributes(feature.attributes())
					newfeature.setGeometry(QgsGeometry.fromPoint(point))
					outfile.addFeature(newfeature)
					out_count = out_count + 1

			elif (newtype == QGis.WKBPoint):
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(feature.geometry().centroid())
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			elif (newtype == QGis.WKBLineString):
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(feature.geometry())
				outfile.addFeature(newfeature)
				out_count = out_count + 1
				
			else:
				return "Invalid Conversion: " + mmqgis_wkbtype_to_text(feature.geometry().wkbType()) + \
					" to " + mmqgis_wkbtype_to_text(newtype)

		elif (feature.geometry().wkbType() == QGis.WKBPolygon) or \
		     (feature.geometry().wkbType() == QGis.WKBPolygon25D):

			if (newtype == QGis.WKBPoint) and splitnodes:
				polygon = feature.geometry().asPolygon()
				for polyline in polygon:
					for point in polyline:
						newfeature = QgsFeature()
						newfeature.setAttributes(feature.attributes())
						newfeature.setGeometry(QgsGeometry.fromPoint(point))
						outfile.addFeature(newfeature)
						out_count = out_count + 1

			elif (newtype == QGis.WKBPoint):
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(feature.geometry().centroid())
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			elif (newtype == QGis.WKBLineString):
				polygon = feature.geometry().asPolygon()
				for polyline in polygon:
					newfeature = QgsFeature()
					newfeature.setAttributes(feature.attributes())
					newfeature.setGeometry(QgsGeometry.fromPolyline(polyline))
					outfile.addFeature(newfeature)
					out_count = out_count + 1

			elif (newtype == QGis.WKBMultiLineString):
				linestrings = []
				polygon = feature.geometry().asPolygon()
				for polyline in polygon:
					linestrings.append(polyline)

				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(QgsGeometry.fromMultiPolyline(linestrings))
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			elif (newtype == QGis.WKBPolygon):
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(feature.geometry())
				outfile.addFeature(newfeature)
				out_count = out_count + 1
				
			else:
				return "Invalid Conversion: " + mmqgis_wkbtype_to_text(feature.geometry().wkbType()) + \
					" to " + mmqgis_wkbtype_to_text(newtype)

		elif (feature.geometry().wkbType() == QGis.WKBMultiPoint) or \
		     (feature.geometry().wkbType() == QGis.WKBMultiPoint25D):

			if (newtype == QGis.WKBPoint) and splitnodes:
				points = feature.geometry().asMultiPoint()
				for point in points:
					newfeature = QgsFeature()
					newfeature.setAttributes(feature.attributes())
					newfeature.setGeometry(QgsGeometry.fromPoint(point))
					outfile.addFeature(newfeature)
					out_count = out_count + 1

			elif (newtype == QGis.WKBPoint):
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(feature.geometry().centroid())
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			else:
				return "Invalid Conversion: " + mmqgis_wkbtype_to_text(feature.geometry().wkbType()) + \
					" to " + mmqgis_wkbtype_to_text(newtype)


		elif (feature.geometry().wkbType() == QGis.WKBMultiLineString) or \
		     (feature.geometry().wkbType() == QGis.WKBMultiLineString25D):

			if (newtype == QGis.WKBPoint) and splitnodes:
				polylines = feature.geometry().asMultiPolyline()
				for polyline in polylines:
					for point in polyline:
						newfeature = QgsFeature()
						newfeature.setAttributes(feature.attributes())
						newfeature.setGeometry(QgsGeometry.fromPoint(point))
						outfile.addFeature(newfeature)
						out_count = out_count + 1

			elif (newtype == QGis.WKBPoint):
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(feature.geometry().centroid())
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			elif (newtype == QGis.WKBLineString):
				linestrings = feature.geometry().asMultiPolyline()
				for linestring in linestrings:
					newfeature = QgsFeature()
					newfeature.setAttributes(feature.attributes())
					newfeature.setGeometry(QgsGeometry.fromPolyline(linestring))
					outfile.addFeature(newfeature)
					out_count = out_count + 1

			elif (newtype == QGis.WKBMultiLineString):
				linestrings = feature.geometry().asMultiPolyline()
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(QgsGeometry.fromMultiPolyline(linestrings))
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			else:
				return "Invalid Conversion: " + mmqgis_wkbtype_to_text(feature.geometry().wkbType()) + \
					" to " + mmqgis_wkbtype_to_text(newtype)

		elif (feature.geometry().wkbType() == QGis.WKBMultiPolygon) or \
		     (feature.geometry().wkbType() == QGis.WKBMultiPolygon25D):

			if (newtype == QGis.WKBPoint) and splitnodes:
				polygons = feature.geometry().asMultiPolygon()
				for polygon in polygons:
					for polyline in polygon:
						for point in polyline:
							newfeature = QgsFeature()
							newfeature.setAttributes(feature.attributes())
							newfeature.setGeometry(QgsGeometry.fromPoint(point))
							outfile.addFeature(newfeature)
							out_count = out_count + 1
	
			elif (newtype == QGis.WKBPoint):
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(feature.geometry().centroid())
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			elif (newtype == QGis.WKBLineString):
				polygons = feature.geometry().asMultiPolygon()
				for polygon in polygons:
					for polyline in polygon:
						newfeature = QgsFeature()
						newfeature.setAttributes(feature.attributes())
						newfeature.setGeometry(QgsGeometry.fromPolyline(polyline))
						outfile.addFeature(newfeature)
						out_count = out_count + 1

			elif (newtype == QGis.WKBPolygon):
				polygons = feature.geometry().asMultiPolygon()
				for polygon in polygons:
					newfeature = QgsFeature()
					newfeature.setAttributes(feature.attributes())
					newfeature.setGeometry(QgsGeometry.fromPolygon(polygon))
					outfile.addFeature(newfeature)
					out_count = out_count + 1

			elif (newtype == QGis.WKBMultiLineString) or \
			     (newtype == QGis.WKBMultiPolygon):
				polygons = feature.geometry().asMultiPolygon()
				newfeature = QgsFeature()
				newfeature.setAttributes(feature.attributes())
				newfeature.setGeometry(QgsGeometry.fromMultiPolygon(polygons))
				outfile.addFeature(newfeature)
				out_count = out_count + 1

			else:
				return "Invalid Conversion: " + mmqgis_wkbtype_to_text(feature.geometry().wkbType()) + \
					" to " + mmqgis_wkbtype_to_text(newtype)
			
	del outfile

	if addlayer:
		qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")

	mmqgis_completion_message(qgis, unicode(feature_count) + " features converted to " + unicode(out_count) + " features")

	return None

# --------------------------------------------------------
#    mmqgis_geometry_to_multipart - Convert singlepart 
#		to multipart geometries
# --------------------------------------------------------

def mmqgis_geometry_to_multipart(qgis, layername, mergefield, mergeattop, savename, addlayer):

	# Error checking
	layer = mmqgis_find_layer(layername)
	if (layer == None) and (layer.type() != QgsMapLayer.VectorLayer):
		return "Invalid Vector Layer " + layername

	if (layer.dataProvider().geometryType() == QGis.WKBPoint) or \
	   (layer.dataProvider().geometryType() == QGis.WKBPoint25D):
		newtype = QGis.WKBMultiPoint

	elif (layer.dataProvider().geometryType() == QGis.WKBLineString) or \
	     (layer.dataProvider().geometryType() == QGis.WKBLineString25D):
		newtype = QGis.WKBMultiLineString

	elif (layer.dataProvider().geometryType() == QGis.WKBPolygon) or \
	     (layer.dataProvider().geometryType() == QGis.WKBPolygon25D):
		newtype = QGis.WKBMultiPolygon

	else:
		return "Geometry is already multipart: " + mmqgis_wkbtype_to_text(layer.dataProvider().geometryType())

	merge_index = layer.dataProvider().fields().indexFromName(mergefield)
	if merge_index < 0:
		return "Invalid merge field: " + mergefield

	
	# Create output file
	if len(savename) <= 0:
		return "Invalid output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", 
		layer.dataProvider().fields(), newtype, layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Have to read features into memory because nested loops of getFeature() don't work
	feature_count = layer.dataProvider().featureCount()
        features = []
	for index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (index % 10) == 0:
			mmqgis_status_message(qgis, "Reading feature " + unicode(index) \
				+ " of " + unicode(feature_count))
		features.append(feature)
	

	# Iterate through each feature in the source layer
	merge_count = 0
	for x in range(0, len(features)):
		if (x % 10) == 0:
			mmqgis_status_message(qgis, "Converting feature " + str(x) \
				+ " of " + unicode(len(features)))

		if features[x] != None:
			attributes = features[x].attributes()
			# key = unicode(attributes[merge_index].toString()).lower()
			key = unicode(attributes[merge_index]).lower()
			# print "Processing " + unicode(x) + ": " + key

			newgeometry = []
			if newtype == QGis.WKBMultiPoint:
				if (feature.geometry().wkbType() == QGis.WKBPoint) or \
				   (feature.geometry().wkbType() == QGis.WKBPoint25D):
					newgeometry.append(features[x].geometry().asPoint())

				elif (feature.geometry().wkbType() == QGis.WKBMultiPoint) or \
				     (feature.geometry().wkbType() == QGis.WKBMultiPoint25D):
					for point in features[x].geometry().asMultiPoint():
						newgeometry.append(point)
				else:
					return "Invalid multipoint geometry type: " + \
						mmqgis_wkbtype_to_text(features[x].geometry().wkbType())

			elif newtype == QGis.WKBMultiLineString:
				# This is a workaround since shapefiles do not distinguish
				# between polylines and multipolylines - all polygons can have multiple
				# parts. QgsGeometry.wkbType() returns WKBLineString even if the 
				# geometry is WKBMultiLineString

				#if (feature.geometry().wkbType() == QGis.WKBLineString) or \
				#   (feature.geometry().wkbType() == QGis.WKBLineString25D):

				if len(features[x].geometry().asPolyline()) > 0:
					newgeometry.append(features[x].geometry().asPolyline())

				#elif (feature.geometry().wkbType() == QGis.WKBMultiLineString) or \
				#     (feature.geometry().wkbType() == QGis.WKBMultiLineString25D):

				elif len(features[x].geometry().asMultiPolyline()) > 0:
					for polyline in features[x].geometry().asMultiPolyline():
						newgeometry.append(polyline)
				else:
					return "Invalid multilinestring geometry type: " + \
						mmqgis_wkbtype_to_text(features[x].geometry().wkbType())

			else: # newtype == QGis.WKBMultiPolygon:
				# This is a workaround since shapefiles do not distinguish
				# between polygons and multipolygons - all polygons can have multiple
				# parts. QgsGeometry.wkbType() returns WKBPolygon even if the 
				# geometry is WKBMultiPolygon

				#if (feature.geometry().wkbType() == QGis.WKBPolygon) or \
				#   (feature.geometry().wkbType() == QGis.WKBPolygon25D):

				if len(features[x].geometry().asPolygon()) > 0:
					newgeometry.append(features[x].geometry().asPolygon())

				#elif (feature.geometry().wkbType() == QGis.WKBMultiPolygon) or \
				#     (feature.geometry().wkbType() == QGis.WKBMultiPolygon25D):

				elif len(features[x].geometry().asMultiPolygon()) > 0:
					for polygon in features[x].geometry().asMultiPolygon():
						newgeometry.append(polygon)
				else:
					return "Invalid multipolygon geometry type: " + \
						mmqgis_wkbtype_to_text(features[x].geometry().wkbType())

			for y in range(x + 1, len(features)):
				#print "   Comparing " + unicode(y)
				#if (features[y] != None) and \
				#   (unicode(features[y].attributes()[merge_index].toString()).lower() == key):
				if (features[y] != None) and \
				   (unicode(features[y].attributes()[merge_index]).lower() == key):
					# print "  " + unicode(features[y].geometry().wkbType())

					if newtype == QGis.WKBMultiPoint:
						newgeometry.append(features[y].geometry().asPoint())

					elif newtype == QGis.WKBMultiLineString:
						newgeometry.append(features[y].geometry().asPolyline())

					# MultiPolygons must be broken apart into separate polygons
					elif features[y].geometry().wkbType() == QGis.WKBMultiPolygon:
						for polygon in features[y].geometry().asMultiPolygon():
							newgeometry.append(polygon)
						
					else: # QGis.WKBMultiPolygon:
						newgeometry.append(features[y].geometry().asPolygon())
					
					if mergeattop == "Sum":
						for zindex, zfield in enumerate(layer.dataProvider().fields()):
							zvalue = features[y].attributes()[zindex]
							if (zfield.type() == QVariant.Int):
								#xval, test = attributes[zindex].toInt()
								#yval, test = features[y].attributes()[zindex].toInt()
								#attributes[zindex] = QVariant(xval + yval)
								try:
									xval = int(attributes[zindex])
									yval = int(zvalue)
									attributes[zindex] = xval + yval
								except:
									attributes[zindex] = 0

							elif (zfield.type() == QVariant.Double):
								# xval, test = attributes[zindex].toDouble()
								# yval, test = features[y].attributes()[zindex].toDouble()
								# attributes[zindex] = QVariant(xval + yval)
								try:
									xval = float(attributes[zindex])
									yval = float(zvalue)
									attributes[zindex] = xval + yval
								except:
									attributes[zindex] = 0

							# print "      Sum " + unicode(zindex) + ": " + \
							#	unicode(attributes[zindex].typeName())

					features[y] = None

			# print unicode(key) + ": " + unicode(type(newgeometry)) + ": " + unicode(len(newgeometry))

			newfeature = QgsFeature()
			newfeature.setAttributes(attributes)

			if newtype == QGis.WKBMultiPoint:
				newfeature.setGeometry(QgsGeometry.fromMultiPoint(newgeometry))

			elif newtype == QGis.WKBMultiLineString:
				newfeature.setGeometry(QgsGeometry.fromMultiPolyline(newgeometry))

			else: # WKBMultiPolygon:
				newfeature.setGeometry(QgsGeometry.fromMultiPolygon(newgeometry))

			outfile.addFeature(newfeature)
			merge_count = merge_count + 1

	del outfile

	if addlayer:
		qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")

	mmqgis_completion_message(qgis, unicode(feature_count) + 
		" features merged to " + unicode(merge_count) + " features")

	return None



# --------------------------------------------------------
#    mmqgis_geometry_export_to_csv - Shape node dump to CSV
# --------------------------------------------------------

def mmqgis_geometry_export_to_csv(qgis, layername, node_filename, attribute_filename, field_delimiter, line_terminator):
	layer = mmqgis_find_layer(layername)

	if (layer == None) or (layer.type() != QgsMapLayer.VectorLayer):
		return "Invalid Vector Layer " + layername

	node_header = ["shapeid", "x", "y"]
	attribute_header = ["shapeid"]
	for index, field in enumerate(layer.dataProvider().fields()):
		if (layer.geometryType() == QGis.Point):
			node_header.append(field.name())
		else:
			attribute_header.append(field.name())

	try:
		nodefile = open(node_filename, 'w')
    	except:
		return "Failure opening " + node_filename

	node_writer = csv.writer(nodefile, delimiter = field_delimiter, 
		lineterminator = line_terminator, quoting=csv.QUOTE_NONNUMERIC)

	# Encoding is forced to UTF-8 because CSV writer doesn't support Unicode
	node_writer.writerow([field.encode("utf-8") for field in node_header])

	if (layer.geometryType() != QGis.Point):
		try:
			attributefile = open(attribute_filename, 'w')
 	   	except:
			return "Failure opening " + attribute_filename

		attribute_writer = csv.writer(attributefile, delimiter = field_delimiter,
			lineterminator = line_terminator, quoting=csv.QUOTE_NONNUMERIC)

		# Encoding is forced to UTF-8 because CSV writer doesn't support Unicode
		attribute_writer.writerow([field.encode("utf-8") for field in attribute_header])


	# Iterate through each feature in the source layer

	#feature = QgsFeature()
	#layer.dataProvider().select(layer.dataProvider().attributeIndexes())
	#layer.dataProvider().rewind()
        #while layer.dataProvider().nextFeature(feature):

	feature_type = ""
	feature_count = layer.dataProvider().featureCount()
	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		feature_type = unicode(mmqgis_wkbtype_to_text(feature.geometry().wkbType()))
		# shapeid = unicode(feature.id()).strip()
		# print "Feature " + str(feature_index) + " = " + feature_type

		if (feature_index % 10) == 0:
			mmqgis_status_message(qgis, "Exporting feature " + unicode(feature_index) \
				+ " of " + unicode(feature_count))

		if (feature.geometry() == None):
			return "Cannot export layer with no shape data"

		elif (feature.geometry().wkbType() == QGis.WKBPoint) or \
		     (feature.geometry().wkbType() == QGis.WKBPoint25D):
			point = feature.geometry().asPoint()
			row = [ unicode(feature_index), unicode(point.x()), unicode(point.y()) ]
			for attindex, attribute in enumerate(feature.attributes()):
				row.append(unicode(attribute).encode("utf-8"))
			node_writer.writerow(row)

		elif (feature.geometry().wkbType() == QGis.WKBMultiPoint) or \
		     (feature.geometry().wkbType() == QGis.WKBMultiPoint25D):
			points = feature.geometry().asMultiPoint()
			for point_index, point in enumerate(points):
				shape_id = unicode(feature_index) + "." + unicode(point_index)
				row = [ shape_id, unicode(point.x()), unicode(point.y()) ]
				row.extend(feature.attributes())
				node_writer.writerow([unicode(field).encode("utf-8") for field in row])

		elif (feature.geometry().wkbType() == QGis.WKBLineString) or \
		     (feature.geometry().wkbType() == QGis.WKBLineString25D):
			polyline = feature.geometry().asPolyline()
			for point in polyline:
				# print "  Point " + str(point.x()) + ", " + str(point.y())
				row = [ unicode(feature_index), unicode(point.x()), unicode(point.y()) ]
				node_writer.writerow(row)

			row = [ feature_index ]
			row.extend(feature.attributes())
			attribute_writer.writerow([unicode(field).encode("utf-8") for field in row])

		elif (feature.geometry().wkbType() == QGis.WKBMultiLineString) or \
		     (feature.geometry().wkbType() == QGis.WKBMultiLineString25D):
			polylines = feature.geometry().asMultiPolyline()
			for polyline_index, polyline in enumerate(polylines):
				shape_id = unicode(feature_index) + "." + unicode(polyline_index)
				for point in polyline:
					# print "  Point " + str(point.x()) + ", " + str(point.y())
					row = [ shape_id, unicode(point.x()), unicode(point.y()) ]
					node_writer.writerow(row)

				row = [ shape_id ]
				row.extend(feature.attributes())
				attribute_writer.writerow([unicode(field).encode("utf-8") for field in row])

		elif (feature.geometry().wkbType() == QGis.WKBPolygon) or \
		     (feature.geometry().wkbType() == QGis.WKBPolygon25D):
			# The first polyline in the polygon is the outer ring
			# Subsequent polylines (if any) are inner rings (holes)
			ring_number = 0
			polygon = feature.geometry().asPolygon()
			for polyline in polygon:
				shape_id = unicode(feature_index)
				if ring_number > 0:
					shape_id = shape_id + ".ring" + unicode(ring_number)
				ring_number = ring_number + 1

				for point in polyline:
					row = [ shape_id, unicode(point.x()), unicode(point.y()) ]
					node_writer.writerow(row)

				row = [ shape_id ]
				row.extend(feature.attributes())
				attribute_writer.writerow([unicode(field).encode("utf-8") for field in row])

		elif (feature.geometry().wkbType() == QGis.WKBMultiPolygon) or \
		     (feature.geometry().wkbType() == QGis.WKBMultiPolygon25D):
			multipolygon = feature.geometry().asMultiPolygon()
			for polygon_index, polygon in enumerate(multipolygon):
				ring_number = 0
				for polyline in polygon:
					shape_id = unicode(feature_index) + "." + unicode(polygon_index)
					if ring_number > 0:
						shape_id = shape_id + ".ring" + unicode(ring_number)
					ring_number = ring_number + 1

					for point in polyline:
						row = [ shape_id, unicode(point.x()), unicode(point.y()) ]
						node_writer.writerow(row)

					row = [ shape_id ]
					row.extend(feature.attributes())
					attribute_writer.writerow([unicode(field).encode("utf-8") for field in row])

		else:
			return "Unsupported geometry: " + unicode(mmqgis_wkbtype_to_text(feature.geometry().wkbType()))
			
	del nodefile
	if (layer.geometryType() != QGis.Point):
		del attributefile

	mmqgis_completion_message(qgis, unicode(feature_count) + " records exported (" + feature_type + ")")

	return None


# ----------------------------------------------------------------
#    mmqgis_geometry_import_from_csv - Shape node import from CSV
# ----------------------------------------------------------------

def mmqgis_geometry_import_from_csv(qgis, node_filename, long_colname, lat_colname, 
	shapeid_colname, geometry_type, shapefile_name, addlayer):
	try:
		infile = open(node_filename, 'r')
		dialect = csv.Sniffer().sniff(infile.read(4096))
		infile.seek(0)
		reader = csv.reader(infile, dialect)
		header = reader.next()

	except Exception as e:
		return unicode(node_filename) + ": " + unicode(e)
			
	# Decode from UTF-8 characters because csv.reader can only handle 8-bit characters
	try:
		header = [unicode(field, "utf-8") for field in header]
	except:
		return "CSV file must be in UTF-8 encoding"

	lat_col = -1
	long_col = -1
	shapeid_col = -1
	for x in range(len(header)):
		# print header[x]
		if (header[x] == lat_colname):
			lat_col = x
		elif (header[x] == long_colname):
			long_col = x
		elif (header[x] == shapeid_colname):
			shapeid_col = x

	if (lat_col < 0):
		return "Invalid latitude column name: " + lat_colname

	if (long_col < 0):
		return "Invalid longitude column name: " + long_colname

	if (shapeid_col < 0):
		return "Invalid shape ID column name: " + shapeid_colname

	if (geometry_type == "Point"):
		wkb_type = QGis.WKBPoint

	elif (geometry_type == "Polyline"):
		wkb_type = QGis.WKBLineString

	elif (geometry_type == "Polygon"):
		wkb_type = QGis.WKBPolygon
	else:
		return "Invalid geometry type: " + geometry_type

	# Create the output shapefile
	if QFile(shapefile_name).exists():
		if not QgsVectorFileWriter.deleteShapeFile(shapefile_name):
			return "Failure deleting existing shapefile: " + shapefile_name

	if qgis.activeLayer() and qgis.activeLayer().dataProvider():
		crs = qgis.activeLayer().crs()
	else:
		crs = QgsCoordinateReferenceSystem()
		crs.createFromSrid(4326) # WGS 84

	fields = QgsFields()
	fields.append(QgsField(shapeid_colname, QVariant.String))
	if (geometry_type == "Point"):
		for x in range(len(header)):
			if ((x != lat_col) and (x != long_col) and (x != shapeid_col)):
				fields.append(QgsField(header[x], QVariant.String))

	outfile = QgsVectorFileWriter(shapefile_name, "utf-8", fields, wkb_type, crs)

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	polyline = []
	node_count = 0
	shape_count = 0
	current_shape_id = False
	reading = True
	while reading:
		try:
			row = reader.next()
		except:
			reading = False

		if reading and (len(row) > long_col) and (len(row) > lat_col) and (len(row) > shapeid_col) \
				and mmqgis_is_float(row[long_col]) and mmqgis_is_float(row[lat_col]):
			node_count += 1
			if (node_count % 10) == 0:
				mmqgis_status_message(qgis, "Importing node " + unicode(node_count))
			point = QgsPoint(float(row[long_col]), float(row[lat_col]))
		else:
			point = False

		if reading and (wkb_type != QGis.WKBPoint) and (row[shapeid_col] == current_shape_id):
			polyline.append(point)

		else:
			#print str(wkb_type) + ": " + str(current_shape_id)
			#print polyline

			bad_feature = False
			if wkb_type == QGis.WKBPoint:
				if point:
					geometry = QgsGeometry.fromPoint(point)
					current_shape_id = row[shapeid_col]
				else:
					bad_feature = True

			elif wkb_type == QGis.WKBLineString:
				if len(polyline) < 2:
					bad_feature = True
				else:
					geometry = QgsGeometry.fromPolyline(polyline)

			elif wkb_type == QGis.WKBPolygon:
				if len(polyline) < 3:
					bad_feature = True
				else:
					# polyline[len(polyline) - 1] = polyline[0] # must close polygons
					polygon = [ polyline ]
					geometry = QgsGeometry.fromPolygon(polygon)

			if not bad_feature:
				# attributes = QgsAttributes()
				# attributes = [ QVariant(str(current_shape_id)) ]
				attributes = [ unicode(current_shape_id) ]
				if (geometry_type == "Point"):
					for x in range(len(header)):
						if x >= len(row):
							attributes.append("")

						elif ((x != lat_col) and (x != long_col) and (x != shapeid_col)):
							attributes.append(unicode(row[x], 'utf-8'))

				#print attributes
				newfeature = QgsFeature()
				newfeature.setAttributes(attributes)
				newfeature.setGeometry(geometry)
				outfile.addFeature(newfeature)
				shape_count += 1
	
			polyline = []
			if reading and point:
				current_shape_id = row[shapeid_col]
				polyline.append(point)

	del infile
	del outfile

	if addlayer:
		qgis.addVectorLayer(shapefile_name, os.path.basename(shapefile_name), "ogr")
		
	mmqgis_completion_message(qgis, "Loaded " + unicode(shape_count) + " shapes (" + unicode(node_count) + " nodes)")

	return None

# --------------------------------------------------------
#    mmqgis_grid - Grid shapefile creation
# --------------------------------------------------------

def mmqgis_grid(qgis, savename, hspacing, vspacing, width, height, originx, originy, gridtype, addlayer):
	if len(savename) <= 0:
		return "No output filename given"

	if (hspacing <= 0) or (vspacing <= 0):
		return "Invalid grid spacing: " + unicode(hspacing) + " / " + unicode(vspacing)
	
	if (width <= hspacing) or (width < vspacing):
		return "Invalid width / height: " + unicode(width) + " / " + unicode(height)

	fields = QgsFields()
	fields.append(QgsField("left", QVariant.Double, "real", 24, 16, "left"))
	fields.append(QgsField("top", QVariant.Double, "real", 24, 16, "top"))
	fields.append(QgsField("right", QVariant.Double, "real", 24, 16, "right"))
	fields.append(QgsField("bottom", QVariant.Double, "real", 24, 16, "bottom"))

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	if gridtype.find("polygon") >= 0:
		shapetype = QGis.WKBPolygon
	else:
		shapetype = QGis.WKBLineString

	# print gridtype + "," + str(shapetype)
		
	outfile = QgsVectorFileWriter(savename, "utf-8", 
		fields, shapetype, QgsCoordinateReferenceSystem());

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	feature_count = 0
	if gridtype == "Rectangle (line)":
		columns = int(floor(float(width) / hspacing))
		rows = int(floor(float(height) / vspacing))
		
		# Longitude lines
		for column in range(0, columns + 1):
			polyline = []
			x = originx + (column * hspacing)
			for row in range(0, rows + 1):
				y = originy + (row * vspacing)	
				polyline.append(QgsPoint(x, y))

			feature = QgsFeature()
			feature.setGeometry(QgsGeometry.fromPolyline(polyline))
			#feature.setAttributes([QVariant(x), QVariant(originy), 
			#	QVariant(x), QVariant(originy + (rows * vspacing))])
			feature.setAttributes([ x, originy + (rows * vspacing), x, originy ])
			outfile.addFeature(feature)

		# Latitude lines
		for row in range(0, rows + 1):
			polyline = []
			y = originy + (row * vspacing)	
			for column in range(0, columns + 1):
				x = originx + (column * hspacing)
				polyline.append(QgsPoint(x, y))
			
			feature.setGeometry(QgsGeometry.fromPolyline(polyline))
			#feature.setAttributes([QVariant(originx), QVariant(y), 
			#	QVariant(originx + (columns * hspacing)), QVariant(y) ])
			feature.setAttributes([ originx, y, originx + (columns * hspacing), y ])
			outfile.addFeature(feature)

		feature_count = (rows + 1) * (columns + 1)

	elif gridtype == "Rectangle (polygon)":
		columns = int(floor(float(width) / hspacing))
		rows = int(floor(float(height) / vspacing))

		for column in range(0, columns):
			# (column + 1) and (row + 1) calculation is used to maintain 
			# topology between adjacent shapes and avoid overlaps/holes 
			# due to rounding errors

			x1 = originx + (column * hspacing)
			x2 = originx + ((column + 1) * hspacing)
			for row in range(0, rows):
				y1 = originy + (row * vspacing)
				y2 = originy + ((row + 1) * vspacing)

				polyline = []
				polyline.append(QgsPoint(x1, y1))
				polyline.append(QgsPoint(x2, y1))
				polyline.append(QgsPoint(x2, y2))
				polyline.append(QgsPoint(x1, y2))
				polyline.append(QgsPoint(x1, y1))

				feature = QgsFeature()
				feature.setGeometry(QgsGeometry.fromPolygon([polyline]))
				# feature.setAttributes([ QVariant(x1), QVariant(y1), QVariant(x2), QVariant(y2) ])
				feature.setAttributes([ x1, y1, x2, y2 ])
				outfile.addFeature(feature)

		feature_count = rows * columns

	elif gridtype == "Diamond (polygon)":
		columns = int(floor(float(width) / (hspacing / 2)))
		rows = int(floor(float(height) / vspacing))

		for column in range(0, columns):
			x1 = originx + ((column + 0) * (hspacing / 2))
			x2 = originx + ((column + 1) * (hspacing / 2))
			x3 = originx + ((column + 2) * (hspacing / 2))

			for row in range(0, rows):
				if (column % 2) == 0:
					y1 = originy + (((row * 2) + 0) * (vspacing / 2))
					y2 = originy + (((row * 2) + 1) * (vspacing / 2))
					y3 = originy + (((row * 2) + 2) * (vspacing / 2))
				else:
					y1 = originy + (((row * 2) + 1) * (vspacing / 2))
					y2 = originy + (((row * 2) + 2) * (vspacing / 2))
					y3 = originy + (((row * 2) + 3) * (vspacing / 2))

				polyline = []
				polyline.append(QgsPoint(x1,  y2))
				polyline.append(QgsPoint(x2,  y1))
				polyline.append(QgsPoint(x3,  y2))
				polyline.append(QgsPoint(x2,  y3))
				polyline.append(QgsPoint(x1,  y2))

				feature = QgsFeature()
				feature.setGeometry(QgsGeometry.fromPolygon([polyline]))
				# feature.setAttributes([ QVariant(x1), QVariant(y1), QVariant(x3), QVariant(y3) ])
				feature.setAttributes([ x1, y1, x3, y3 ])
				outfile.addFeature(feature)

		feature_count = rows * columns

	elif gridtype == "Hexagon (polygon)":
		# To preserve symmetry, hspacing is fixed relative to vspacing
		xvertexlo = 0.288675134594813 * vspacing;
		xvertexhi = 0.577350269189626 * vspacing;
		hspacing = xvertexlo + xvertexhi

		columns = int(floor(float(width) / hspacing))
		rows = int(floor(float(height) / vspacing))

		for column in range(0, columns):
			# (column + 1) and (row + 1) calculation is used to maintain 
			# topology between adjacent shapes and avoid overlaps/holes 
			# due to rounding errors

			x1 = originx + (column * hspacing)		# far left
			x2 = x1 + (xvertexhi - xvertexlo)		# left
			x3 = originx + ((column + 1) * hspacing)	# right
			x4 = x3 + (xvertexhi - xvertexlo)		# far right

			for row in range(0, rows):
				if (column % 2) == 0:
					y1 = originy + (((row * 2) + 0) * (vspacing / 2))	# hi
					y2 = originy + (((row * 2) + 1) * (vspacing / 2))	# mid
					y3 = originy + (((row * 2) + 2) * (vspacing / 2))	# lo
				else:
					y1 = originy + (((row * 2) + 1) * (vspacing / 2))	# hi
					y2 = originy + (((row * 2) + 2) * (vspacing / 2))	# mid
					y3 = originy + (((row * 2) + 3) * (vspacing / 2))	#lo

				polyline = []
				polyline.append(QgsPoint(x1, y2))
				polyline.append(QgsPoint(x2, y1))
				polyline.append(QgsPoint(x3, y1))
				polyline.append(QgsPoint(x4, y2))
				polyline.append(QgsPoint(x3, y3))
				polyline.append(QgsPoint(x2, y3))
				polyline.append(QgsPoint(x1, y2))

				feature = QgsFeature()
				feature.setGeometry(QgsGeometry.fromPolygon([polyline]))
				# feature.setAttributes([ QVariant(x1), QVariant(y1), QVariant(x4), QVariant(y3) ])
				feature.setAttributes([ x1, y1, x4, y3 ])
				outfile.addFeature(feature)

		feature_count = rows * columns

	del outfile

	if addlayer:
		qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
		
	mmqgis_completion_message(qgis, unicode(feature_count) + " feature grid shapefile created")

	return None

# --------------------------------------------------------
#    mmqgis_gridify - Snap shape verticies to grid
# --------------------------------------------------------

def mmqgis_gridify_layer(qgis, layername, hspacing, vspacing, savename, addlayer):
	layer = mmqgis_find_layer(layername)
	if not layer:
		return "Project has no active vector layer to gridify"
	
	if (hspacing <= 0) or (vspacing <= 0):
		return "Invalid grid spacing: " + unicode(hspacing) + "/" + unicode(vspacing)

	if len(savename) <= 0:
		return "No output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", layer.dataProvider().fields(),
			layer.dataProvider().geometryType(), layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	point_count = 0
	deleted_points = 0

	feature_count = layer.dataProvider().featureCount()

	#feature = QgsFeature()
	#layer.dataProvider().select(layer.dataProvider().attributeIndexes())
	#layer.dataProvider().rewind()
        #while layer.dataProvider().nextFeature(feature):

	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (feature_index % 10) == 0:
			mmqgis_status_message(qgis, "Gridifying feature " + unicode(feature_index))

		geometry = feature.geometry()

		if (geometry.wkbType() == QGis.WKBPoint) or \
		   (geometry.wkbType() == QGis.WKBPoint25D):
			points, added, deleted = mmqgis_gridify_points(hspacing, vspacing, [geometry.asPoint()])
			geometry = geometry.fromPoint(points[0])
			point_count += added
			deleted_points += deleted

		elif (geometry.wkbType() == QGis.WKBLineString) or \
		     (geometry.wkbType() == QGis.WKBLineString25D):
			#print "LineString"
			polyline, added, deleted = mmqgis_gridify_points(hspacing, vspacing, geometry.asPolyline())
			if len(polyline) < 2:
				geometry = None
			else:
				geometry = geometry.fromPolyline(polyline)
			point_count += added
			deleted_points += deleted

		elif (geometry.wkbType() == QGis.WKBPolygon) or \
		     (geometry.wkbType() == QGis.WKBPolygon25D):
			newpolygon = []
			for polyline in geometry.asPolygon():
				newpolyline, added, deleted = mmqgis_gridify_points(hspacing, vspacing, polyline)
				point_count += added
				deleted_points += deleted

				if len(newpolyline) > 1:
					newpolygon.append(newpolyline)

			if len(newpolygon) <= 0:
				geometry = None
			else:
				geometry = geometry.fromPolygon(newpolygon)

		elif (geometry.wkbType() == QGis.WKBMultiPoint) or \
		     (geometry.wkbType() == QGis.WKBMultiPoint25D):
			newmultipoints = []
			for index, point in enumerate(geometry.asMultiPoint()):
				# print unicode(index) + ": " + unicode(type(point))
				gridded, added, deleted = mmqgis_gridify_points(hspacing, vspacing, [ point ])
				# append() causes fail in fromMultiPoint(), extend() doesn't
				newmultipoints.extend(gridded)
				point_count += added
				deleted_points += deleted

			geometry = geometry.fromMultiPoint(newmultipoints)

		elif (geometry.wkbType() == QGis.WKBMultiLineString) or \
		     (geometry.wkbType() == QGis.WKBMultiLineString25D):
			#print "MultiLineString"
			newmultipolyline = []
			for polyline in geometry.asMultiPolyline():
				newpolyline, added, deleted = mmqgis_gridify_points(hspacing, vspacing, polyline)
				if len(newpolyline) > 1:
					newmultipolyline.append(newpolyline)
				point_count += added
				deleted_points += deleted

			if len(newmultipolyline) <= 0:
				geometry = None
			else:
				geometry = geometry.fromMultiPolyline(newmultipolyline)


		elif (geometry.wkbType() == QGis.WKBMultiPolygon) or \
		     (geometry.wkbType() == QGis.WKBMultiPolygon25D):
			#print "MultiPolygon"
			newmultipolygon = []
			for polygon in geometry.asMultiPolygon():
				newpolygon = []
				for polyline in polygon:
					newpolyline, added, deleted = mmqgis_gridify_points(hspacing, vspacing, polyline)

					if len(newpolyline) > 2:
						newpolygon.append(newpolyline)

					point_count += added
					deleted_points += deleted

				if len(newpolygon) > 0:
					newmultipolygon.append(newpolygon)

			if len(newmultipolygon) <= 0:
				geometry = None
			else:
				geometry = geometry.fromMultiPolygon(newmultipolygon)

		else:
			return "Unknown geometry type " + mmqgis_wkbtype_to_text(geometry.wkbType()) + \
				" on feature " + unicode(feature_index)

		# print "Closing feature"
	
		if geometry != None:
			out_feature = QgsFeature()
			out_feature.setGeometry(geometry)
			out_feature.setAttributes(feature.attributes())
			outfile.addFeature(out_feature)

	del outfile

	if addlayer:
		vlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
			
	mmqgis_completion_message(qgis, "Gridified shapefile created (" + \
		unicode(deleted_points) + " of " + unicode(point_count) + " points deleted)")

	return None


# --------------------------------------------------------
#    mmqgis_hub_distance - Create shapefile of distances
#			   from points to nearest hub
# --------------------------------------------------------

def mmqgis_hub_distance(qgis, sourcename, destname, nameattributename, units, addlines, savename, distribute, addlayer):

	# Error checks
	sourcelayer = mmqgis_find_layer(sourcename)
	if (sourcelayer == None) or (sourcelayer.featureCount() <= 0):
		return "Origin Layer " + sourcename + " not found"

	hubslayer = mmqgis_find_layer(destname)
	if (hubslayer == None) or (hubslayer.featureCount() <= 0):
		return "Hub layer " + destname + " not found"

	if sourcename == destname:
		return "Same layer given for both hubs and spokes"

	nameindex = hubslayer.dataProvider().fieldNameIndex(nameattributename)
	if nameindex < 0:
		return "Invalid name attribute: " + nameattributename

	outputtype = QGis.WKBPoint
	if addlines:
		outputtype = QGis.WKBLineString

	# Create output file
	if len(savename) <= 0:
		return "Invalid output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename


	outfields = sourcelayer.dataProvider().fields()
	outfields.append(QgsField("HubName", QVariant.String))
	outfields.append(QgsField("HubDist", QVariant.Double))

	wgs84 = QgsCoordinateReferenceSystem()
	wgs84.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")

	outfile = QgsVectorFileWriter(savename, "utf-8", outfields, outputtype, wgs84)

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Distance calculations using mmqgis_distance() need 
	# points in unprojected WGS 84 coordinates

	htransform = QgsCoordinateTransform(hubslayer.crs(), wgs84)
	stransform = QgsCoordinateTransform(sourcelayer.crs(), wgs84)


	# Create array of hubs in memory with WGS84 centroids and hub name
	hubs = [] # point, hub_name
	for index, feature in enumerate(hubslayer.dataProvider().getFeatures()):
		if (index % 20) == 0:
			mmqgis_status_message(qgis, "Reading hub " + unicode(feature.id()))

		wgs84_hub = feature.geometry().boundingBox().center()
		if units <> "Layer Units":
			wgs84_hub = htransform.transform(wgs84_hub)
		
		hubs.append([wgs84_hub, feature.attributes()[nameindex]])


	# Create array of points in memory with WGS84 centroids and attributes
	points = [] # point, attributes
	for index, feature in enumerate(sourcelayer.dataProvider().getFeatures()):
		if (index % 20) == 0:
			mmqgis_status_message(qgis, "Reading point " + unicode(feature.id()))

		wgs84_point = feature.geometry().boundingBox().center()
		if units <> "Layer Units":
			wgs84_point = stransform.transform(wgs84_point)

		points.append([wgs84_point, feature.attributes()])


	lines = [] # source_point, hub_point, source_attributes, hub_name, hub_distance (meters)

	# Even distribution of points
	if distribute:
		# Sequentially assign points to hubs for even distribution
		for index in range(0, len(points)):
			lines.append([points[index][0], hubs[index % len(hubs)][0], 
				points[index][1], hubs[index % len(hubs)][1], 0])

		# Optimize distances by swapping hubs when distance would be shorter for both
		# Arbitrary loop limit of 100 to prevent infinite looping
		for optimizing in range(0, 100):
			swaps = 0
			for x in range(0, len(lines) - 1):
				if (x % 10) == 0:
					mmqgis_status_message(qgis, "Optimizing line " + \
						unicode(x) + " of " + unicode(len(points)) + \
						"(pass " + unicode(optimizing + 1) + ")")

				for y in range(x + 1, len(lines)):
					# Calculate distances with possible point/hub combinations
					xx = sqrt(pow(lines[x][0].x() - lines[x][1].x(), 2) + \
						  pow(lines[x][0].y() - lines[x][1].y(), 2))
					yy = sqrt(pow(lines[y][0].x() - lines[y][1].x(), 2) + \
						  pow(lines[y][0].y() - lines[y][1].y(), 2))
					xy = sqrt(pow(lines[x][0].x() - lines[y][1].x(), 2) + \
						  pow(lines[x][0].y() - lines[y][1].y(), 2))
					yx = sqrt(pow(lines[y][0].x() - lines[x][1].x(), 2) + \
						  pow(lines[y][0].y() - lines[x][1].y(), 2))

					# Swap hubs if that would shorten both lines or overall length is less
					# if ((xy < xx) and (yx < yy)) or ((xy + yx) < (xx + yy)):
					if ((xy + yx) < (xx + yy)):
						hubx = lines[x][1]
						namex = lines[x][3]
						lines[x][1] = lines[y][1]
						lines[x][3] = lines[y][3]
						lines[y][1] = hubx
						lines[y][3] = namex
						swaps = swaps + 1

			# Keep repeating until minimal length has been reached
			if swaps <= 0:
				break

		# Calculate actual distance
		for x in range(0, len(lines)):
			if units == "Layer Units":
				lines[x][4] = sqrt(pow(lines[x][0].x() - lines[x][1].x(), 2.0) + \
					pow(lines[x][0].y() - lines[0][1].y(), 2.0))
			else:
				lines[x][4] = mmqgis_distance(lines[x][0], lines[x][1])


	# Assign points to closes hub (uneven distribution)
	else:
		for point_index, source in enumerate(points):
			# Status message
			if (point_index % 50) == 0:
				mmqgis_status_message(qgis, "Creating line " + \
					unicode(point_index) + " of " + unicode(len(points)))

			# Find closest hub
			closest_index = -1
			closest_distance = 0

			for hub_index, hub in enumerate(hubs):
				if units == "Layer Units":
					hubdist = sqrt(pow(source[0].x() - hub[0].x(), 2.0) + \
						pow(source[0].y() - hub[0].y(), 2.0))
				else:
					hubdist = mmqgis_distance(source[0], hub[0])

				if (closest_index < 0) or (hubdist < closest_distance):
					closest_index = hub_index
					closest_distance = hubdist

			# Append to line
			lines.append([source[0], hubs[closest_index][0], source[1],
				hubs[closest_index][1], closest_distance])



	# Write points/lines to file
	for index, line in enumerate(lines):

		# Status message
		if (index % 50) == 0:
			mmqgis_status_message(qgis, "Writing feature " + unicode(index) + " of " + unicode(len(lines)))

		# Convert distance to appropriate output unit
		if units == "Feet":
			hubdist = mmqgis_meters_to_feet(line[4])

		elif units == "Miles":
			hubdist = mmqgis_meters_to_miles(line[4])

		elif units == "Kilometers":
			hubdist = line[4] / 1000

		elif units != "Meters": # Euclidian distance in layer units
			hubdist = line[4]

		# Create feature
		attributes = line[2]
		attributes.append(line[3])
		attributes.append(hubdist)

		outfeature = QgsFeature()
		outfeature.setAttributes(attributes)

		if outputtype == QGis.WKBPoint:
			outfeature.setGeometry(QgsGeometry.fromPoint(line[0]))

		else:
			outfeature.setGeometry(QgsGeometry.fromPolyline([line[0], line[1]]))

		outfile.addFeature(outfeature)


	del outfile
	del hubslayer
	del sourcelayer

	if addlayer:
		vlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
			
	mmqgis_completion_message(qgis, unicode(len(lines)) + " node hub distance file created")

	return None


# --------------------------------------------------------
#    mmqgis_hub_lines - Create shapefile of lines from
#			spoke points to matching hubs
# --------------------------------------------------------


def mmqgis_hub_lines(qgis, hubname, hubattr, spokename, spokeattr, savename, addlayer):

	# Find layers
	if hubname == spokename:
		return "Same layer given for both hubs and spokes"

	hublayer = mmqgis_find_layer(hubname)
	if (hublayer == None) or (hublayer.featureCount() <= 0):
		return "Hub layer " + hubname + " not found"

	spokelayer = mmqgis_find_layer(spokename)
	if spokelayer == None:
		return "Spoke Point Layer " + spokename + " not found"

	# Find Hub ID attribute indices
	hubindex = hublayer.dataProvider().fieldNameIndex(hubattr)
	if hubindex < 0:
		return "Invalid name attribute: " + hubattr

	spokeindex = spokelayer.dataProvider().fieldNameIndex(spokeattr)
	if spokeindex < 0:
		return "Invalid name attribute: " + spokeattr

	# Create output file
	if len(savename) <= 0:
		return "No output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfields = spokelayer.dataProvider().fields()

	outfile = QgsVectorFileWriter(savename, "utf-8", outfields, QGis.WKBLineString, spokelayer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Scan spoke points
	linecount = 0
	for spokepoint in spokelayer.dataProvider().getFeatures():
		spokex = spokepoint.geometry().boundingBox().center().x()
		spokey = spokepoint.geometry().boundingBox().center().y()
		# spokeid = unicode(spokepoint.attributes()[spokeindex].toString())
		spokeid = unicode(spokepoint.attributes()[spokeindex])
		mmqgis_status_message(qgis, "Reading spoke " + unicode(spokepoint.id()))
		#print "Spoke " + str(spokex) + ", " + str(spokey)

		# Scan hub points to find first matching hub
		for hubpoint in hublayer.dataProvider().getFeatures():
			# hubid = unicode(hubpoint.attributes()[hubindex].toString())
			hubid = unicode(hubpoint.attributes()[hubindex])
			if hubid == spokeid:
				hubx = hubpoint.geometry().boundingBox().center().x()
				huby = hubpoint.geometry().boundingBox().center().y()
				#print "   Hub " + str(hubx) + ", " + str(huby)

				# Write line to the output file
				outfeature = QgsFeature()
				outfeature.setAttributes(spokepoint.attributes())

				polyline = []
				polyline.append(QgsPoint(spokex, spokey))
				polyline.append(QgsPoint(hubx, huby))
				geometry = QgsGeometry()
				outfeature.setGeometry(geometry.fromPolyline(polyline))
				outfile.addFeature(outfeature)
				linecount = linecount + 1
				break

	del spokelayer
	del hublayer
	del outfile

	if linecount <= 0:
		return "No spoke/hub matches found to create lines"

	if addlayer:
		qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")

	mmqgis_completion_message(qgis, unicode(linecount) + " hub/spoke lines written")

	return None

# ----------------------------------------------------------
#    mmqgis_kml_export - Export attributes to KML file
#			 suitable for display in Google Maps
# ----------------------------------------------------------

def mmqgis_kml_export(qgis, layername, nameattribute, description, separator, outfilename, addlayer):
	layer = mmqgis_find_layer(layername)
	if not layer:
		return "Layer not found: " + layername

	if (separator == None) or (len(separator) <= 0):
		return "Invalid description field separator"

	nameindex = layer.dataProvider().fieldNameIndex(nameattribute)
	if nameindex < 0:
		return "Invalid name attribute: " + nameattribute

	descindices = []
	for fieldname in description:
		index = layer.dataProvider().fieldNameIndex(fieldname)
		if index < 0:
			return "Invalid description attribute: " + fieldname
		descindices.append(index)


	# Create output file
	try:
		outfile = io.open(outfilename, 'w', encoding="utf-8")
		# outfile = sys.stdout
    	except:
		return "Failure opening " + outfilename

	outfile.write(u'<?xml version="1.0" encoding="UTF-8"?>\n')
	outfile.write(u'<kml xmlns="http://earth.google.com/kml/2.2">\n')
	outfile.write(u'<Document>\n')
	outfile.write(u'<name>' + unicode(layername) + u'</name>\n')
	#  <description><![CDATA[Test description]]></description>

	# 8/25/2014 startRender()/stopRender() kludge needed so symbolsForFeature() does not crash
	# http://osgeo-org.1560.x6.nabble.com/symbolForFeature-does-not-works-td5149509.html
	renderer = layer.rendererV2()
	render_context = QgsRenderContext()
	renderer.startRender(render_context, layer.dataProvider().fields())
	# print unicode(renderer.dump())


	# Build stylesheet
	stylecount = 0
	symbolcount = len(renderer.symbols())
	for index, symbol in enumerate(renderer.symbols()):
		# print u'<Style id="style' + unicode(index + 1) + u'">'

		outfile.write(u'<Style id="style' + unicode(index + 1) + u'">\n')

		if symbol.type() == QgsSymbolV2.Fill:
			outfile.write(u'\t<LineStyle>\n')
			outfile.write(u'\t\t<color>40000000</color>\n')
			outfile.write(u'\t\t<width>3</width>\n')
			outfile.write(u'\t</LineStyle>\n')

			# KML colors are AABBGGRR
			color = (int(round(symbol.alpha() * 255)) << 24) + (symbol.color().blue() << 16) + \
				(symbol.color().green() << 8) + symbol.color().red()
			# print "Color " + unicode(symbol.alpha()) + ", " + unicode(symbol.color().blue()) + \
			#	", " + unicode(symbol.color().green()) + ", " + unicode(symbol.color().red())

			outfile.write(u'\t<PolyStyle>\n')
			outfile.write(u'\t\t<color>' + unicode(format(color, '08x')) + u'</color>\n')
			outfile.write(u'\t\t<fill>1</fill>\n')
			outfile.write(u'\t\t<outline>1</outline>\n')
			outfile.write(u'\t</PolyStyle>\n')

		elif symbol.type() == QgsSymbolV2.Line:
			# KML colors are AABBGGRR
			color = (int(round(symbol.alpha() * 255)) << 24) + (symbol.color().blue() << 16) + \
				(symbol.color().green() << 8) + symbol.color().red()
			outfile.write(u'\t<LineStyle>\n')
			outfile.write(u'\t\t<color>' + unicode(format(color, '08x')) + u'</color>\n')
			outfile.write(u'\t\t<width>5</width>\n')
			outfile.write(u'\t</LineStyle>\n')

		else: # Marker
			icon = mmqgis_kml_icon(symbol.color().red(), symbol.color().green(), symbol.color().blue())
			outfile.write(u'\t<IconStyle>\n')
			outfile.write(u'\t\t<Icon>\n')
			outfile.write(u'\t\t\t<href>' + unicode(icon) + u'</href>\n')
			outfile.write(u'\t\t</Icon>\n')
			outfile.write(u'\t</IconStyle>\n')

		# print unicode(index) + ") " + unicode(symbol.color().name())

		outfile.write(u'</Style>\n')


	# Transform projection to WGS84 long/lat
	wgs84 = QgsCoordinateReferenceSystem()
	wgs84.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")
	transform = QgsCoordinateTransform(layer.crs(), wgs84)

	# Write features to KML
	featurecount = 0
	for featureindex, feature in enumerate(layer.dataProvider().getFeatures()):

		# Find style for feature
		style = '#style0'
		for symbolsindex, featuresymbol in enumerate(renderer.symbolsForFeature(feature)):
			# print "  Feature symbol " + unicode(symbolsindex) + ": " + unicode(featuresymbol.dump())
			for renderindex, rendersymbol in enumerate(renderer.symbols()):
				# print "    Render symbol: " + unicode(rendersymbol.dump())
				if featuresymbol.dump() == rendersymbol.dump():
					# print "      Render: " + unicode(renderindex)
					style = '#style' + unicode(renderindex + 1)


		# Build name/description strings for feature
		# name = unicode(feature.attributes()[nameindex].toString())
		name = unicode(feature.attributes()[nameindex])
		description = ""
		if (separator != 'Paragraphs') and (separator != 'Field Names'):
			description = "<p>"

		for index, fieldindex in enumerate(descindices):
			if separator == 'Paragraphs':
				description = description + "<p>"
			elif separator == 'Field Names':
				description = description + "<p>" + \
					unicode(layer.dataProvider().fields()[fieldindex].name()) + ": "

			# attribute = unicode(feature.attributes()[fieldindex].toString())
			attribute = unicode(feature.attributes()[fieldindex])
			attribute = attribute.replace('[', '\\[')
			attribute = attribute.replace(']', '\\]')
			description = description + attribute

			if (separator == 'Paragraphs') or (separator == 'Field Names'):
				description = description + "</p>"
			elif index < (len(descindices) - 1):
				if separator == 'Commas':
					description = description + ','
				else:
					description = description + unicode(separator)

		if (separator != 'Paragraphs') and (separator != 'Field Names'):
			description = description + "</p>"
		

		# KML always in WGS 84 long/lat
		geometry = feature.geometry()
		geometry.transform(transform)

		# print unicode(geometry.wkbType()) + ": " + unicode(geometry.type()) + ": " + name

		# Write features
		if (geometry.wkbType() == QGis.WKBPoint) or \
		   (geometry.wkbType() == QGis.WKBPoint25D):
			mmqgis_kml_write_point(geometry.asPoint(), name, description, style, outfile)
			featurecount = featurecount + 1

		elif (geometry.wkbType() == QGis.WKBMultiPoint) or \
		     (geometry.wkbType() == QGis.WKBMultiPoint25D):
			for point in geometry.asMultiPoint():
				mmqgis_kml_write_point(point, name, description, style, outfile)
				featurecount = featurecount + 1

		elif (geometry.wkbType() == QGis.WKBLineString) or \
		     (geometry.wkbType() == QGis.WKBLineString25D):
			mmqgis_kml_write_line(geometry.asPolyline(), name, description, style, outfile)
			featurecount = featurecount + 1

		elif (geometry.wkbType() == QGis.WKBMultiLineString) or \
		     (geometry.wkbType() == QGis.WKBMultiLineString25D):
			for line in geometry.asMultiPolyline():
				mmqgis_kml_write_line(line, name, description, style, outfile)
				featurecount = featurecount + 1

		elif (geometry.wkbType() == QGis.WKBPolygon) or \
		     (geometry.wkbType() == QGis.WKBPolygon25D):
			mmqgis_kml_write_polygon(geometry.asPolygon(), name, description, style, outfile)
			featurecount = featurecount + 1

		elif (geometry.wkbType() == QGis.WKBMultiPolygon) or \
		     (geometry.wkbType() == QGis.WKBMultiPolygon25D):
			for polygon in geometry.asMultiPolygon():
				mmqgis_kml_write_polygon(polygon, name, description, style, outfile)
				featurecount = featurecount + 1

	outfile.write(u'</Document>\n')
	outfile.write(u'</kml>')
	outfile.close()

	renderer.stopRender(render_context)

	mmqgis_completion_message(qgis, unicode(featurecount) + " features exported to KML")

	return None

def mmqgis_kml_icon(red, green, blue):
	# Placemarks in Google (tm) maps are images referenced with a URL
	# These are the standard placemark icons used in Google maps
	# red = (color & 0xff0000) >> 16
	# green = (color & 0xff00) >> 8
	# blue = (color & 0xff)
	threshold = (min(red, green, blue) + max(red, green, blue)) / 2
	composite = 0
	if red >= threshold:
		composite = composite + 4
	if green >= threshold:
		composite = composite + 2
	if blue >= threshold:
		composite = composite + 1

	# print "rgb(" + unicode(red) + "," + unicode(green) + "," + unicode(blue) + ") = " + unicode(composite)

	if composite == 0: # black
        	return 'http://maps.gstatic.com/mapfiles/ms2/micons/blue-dot.png'
	elif composite == 1: # blue
		return 'http://maps.gstatic.com/mapfiles/ms2/micons/blue-dot.png'
	elif composite == 2: # green
		return 'http://maps.gstatic.com/mapfiles/ms2/micons/green-dot.png'
	elif composite == 3: # cyan
		return 'http://maps.gstatic.com/mapfiles/ms2/micons/ltblue-dot.png'
	elif composite == 4: # red
		return 'http://maps.gstatic.com/mapfiles/ms2/micons/red-dot.png'
	elif composite == 5: # magenta
		return 'http://maps.gstatic.com/mapfiles/ms2/micons/pink-dot.png'
	elif composite == 6: # yellow
		return 'http://maps.gstatic.com/mapfiles/ms2/micons/yellow-dot.png'
	else: # 7: white
		return 'http://maps.gstatic.com/mapfiles/ms2/micons/purple-dot.png'

def mmqgis_kml_write_point(point, name, description, style, outfile):
	outfile.write(u'<Placemark>\n')
	outfile.write(u'<name>' + unicode(name) + u'</name>\n')
	outfile.write(u'<description><![CDATA[' + unicode(description) + u']]></description>\n')
	outfile.write(u'<styleUrl>' + unicode(style) + '</styleUrl>\n')
	outfile.write(u'\t<Point>\n')
	outfile.write(u'\t\t<coordinates>' + unicode(point.x()) + u',' + unicode(point.y()) + u',0.00000</coordinates>\n')
	outfile.write(u'\t</Point>\n')
	outfile.write(u'</Placemark>\n')

def mmqgis_kml_write_line(line, name, description, style, outfile):
	outfile.write(u'<Placemark>\n')
	outfile.write(u'<name>' + unicode(name) + u'</name>\n')
	outfile.write(u'<description><![CDATA[' + unicode(description) + u']]></description>\n')
	outfile.write(u'<styleUrl>' + unicode(style) + u'</styleUrl>\n')
	outfile.write(u'\t<LineString>\n')
	outfile.write(u'\t\t<tessellate>1</tessellate>\n')
	outfile.write(u'\t\t<coordinates>\n')
	for point in line:
		outfile.write(u'\t\t\t' + unicode(point.x()) + u',' + unicode(point.y()) + u',0.00000\n')
	outfile.write(u'\t\t</coordinates>\n')
	outfile.write(u'\t</LineString>\n')
	outfile.write(u'</Placemark>\n')

def mmqgis_kml_write_polygon(polygon, name, description, style, outfile):
	outfile.write(u'<Placemark>\n')
	outfile.write(u'<name>' + unicode(name) + u'</name>\n')
	outfile.write(u'<description><![CDATA[' + unicode(description) + u']]></description>\n')
	outfile.write(u'<styleUrl>' + unicode(style) + u'</styleUrl>\n')
	outfile.write(u'\t<Polygon>\n')

	for ringnum, ring in enumerate(polygon):
		if (ringnum == 0):
			outfile.write(u'\t\t<outerBoundaryIs>\n')
		else:
			outfile.write(u'\t\t<innerBoundaryIs>\n')

		outfile.write(u'\t\t\t<LinearRing>\n')
		outfile.write(u'\t\t\t\t<tessellate>1</tessellate>\n')
		outfile.write(u'\t\t\t\t<coordinates>\n')

		for point in ring:
			outfile.write(u'\t\t\t\t\t' + unicode(point.x()) + u',' + unicode(point.y()) + u',0.00000\n')

		outfile.write(u'\t\t\t\t</coordinates>\n')
		outfile.write(u'\t\t\t</LinearRing>\n')

		if (ringnum == 0):
			outfile.write(u'\t\t</outerBoundaryIs>\n')
		else:
			outfile.write(u'\t\t</innerBoundaryIs>\n')

	outfile.write(u'\t</Polygon>\n')
	outfile.write(u'</Placemark>\n')



# --------------------------------------------------------
#    mmqgis_label - Create single label points for
#		    single- or multi-feature items
# --------------------------------------------------------

class mmqgis_label():
	def __init__(self, name, attribute_list, bounding_box):
		self.name = name
		self.attributes = attribute_list
		self.bounding_box = bounding_box

def mmqgis_label_point(qgis, layername, labelattributename, savename, addlayer):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Invalid layer name " + unicode(layername)

	labelindex = layer.dataProvider().fieldNameIndex(labelattributename)
	if labelindex < 0:
		return "Invalid label field name: " + labelattributename

	# print  "labelindex = " + str(labelindex)

	if len(savename) <= 0:
		return "No output filename given"

	# Open file (delete any existing)
	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", layer.dataProvider().fields(),
				QGis.WKBPoint, layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Build dictionary of items, averaging center for multi-feature items
	label_features = {}
	readcount = 0
	feature_count = layer.featureCount()

	for feature in layer.dataProvider().getFeatures():
		# key = unicode(feature.attributes()[labelindex].toString())
		key = unicode(feature.attributes()[labelindex])
		# print "Feature: " + str(feature.id()) + " = " + key
		if not label_features.has_key(key):
			label_features[key] = mmqgis_label(key, feature.attributes(), feature.geometry().boundingBox())
		else:
			label_features[key].bounding_box.combineExtentWith(feature.geometry().boundingBox())

		readcount += 1
		if not (readcount % 10):
			mmqgis_status_message(qgis,  \
				"Reading feature " + unicode(readcount) + " of " + unicode(feature_count))



	# Sort keys so features appear in alphabetical order
	keys = label_features.keys()
	keys.sort()

	# Calculate points and write them to the output file
	writecount = 0
	for key in keys:
		label_point = label_features[key]

		feature = QgsFeature()
		feature.setAttributes(label_features[key].attributes)
		feature.setGeometry(QgsGeometry.fromPoint(label_features[key].bounding_box.center()))

		if not outfile.addFeature(feature):
			return "Failure writing feature to shapefile"

		writecount += 1
		if not (writecount % 50):
			mmqgis_status_message(qgis,  \
				"Writing feature " + unicode(writecount) + " of " + unicode(len(label_features)))

	del outfile

	if addlayer:
		newlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")

		newsymbol = QgsSymbolV2.defaultSymbol(newlayer.geometryType())
		newsymbol.setAlpha(0)
		renderer = QgsSingleSymbolRendererV2(newsymbol)
		newlayer.setRendererV2(renderer)

		settings = QgsPalLayerSettings()
		settings.readFromLayer(newlayer)
		settings.enabled = True
		settings.fieldIndex = labelindex
		# settings.fieldName = QString(labelattributename)
		settings.fieldName = labelattributename
		settings.placement = QgsPalLayerSettings.OverPoint
		settings.bufferColor = QColor(255, 255, 255)
		settings.bufferSize = 1.0
		settings.textColor = QColor(0, 0, 0)
		settings.textFont = QFont("Sans Serif", 10)
		settings.fontSizeInMapUnits = False
		settings.writeToLayer(newlayer)

		# Deprecated labeling configuration
		# newlayer.enableLabels(True)
		# newlayer.label().setLabelField(0, labelindex)
		# newlayer.label().setBufferColor(QColor(255, 255, 255))
		# newlayer.label().setSize(12.0, QgsLabelAttributes.PointUnits)

		# for index, field in enumerate(newlayer.dataProvider().fields()):
		#	print unicode(index) + ": " + unicode(field.name())
		# print unicode(newlayer.label().labelAttributes()) + ": " + unicode(newlayer.label().labelField(0))

		newlayer.triggerRepaint()
		qgis.legendInterface().refreshLayerSymbology(newlayer)

		#labelfields = QgsFields()
		#labelfields.append(newlayer.dataProvider().fields()[labelindex])
		#labelindex = layer.dataProvider().fieldNameIndex(labelattributename)
		# print unicode(layer.label())

	mmqgis_completion_message(qgis, unicode(writecount) + " label shapefile created from " + layername)

	return None

# --------------------------------------------------------
#    mmqgis_merge - Merge layers to single shapefile
# --------------------------------------------------------

def mmqgis_merge(qgis, layernames, savename, addlayer):
	fields = QgsFields()
	layers = []
	totalfeaturecount = 0

	for x in range(0, len(layernames)):
		layername = layernames[x]
		layer = mmqgis_find_layer(layername)
		if layer == None:
			return "Layer " + layername + " not found"

		# Verify that all layers are the same type (point, polygon, etc)
		if (len(layers) > 0):
			if (layer.dataProvider().geometryType() != layers[0].dataProvider().geometryType()):
				return "Merged layers must all be same type of geometry (" + \
					mmqgis_wkbtype_to_text(layer.dataProvider().geometryType()) + " != " + \
					mmqgis_wkbtype_to_text(layers[0].dataProvider().geometryType()) + ")"

			#if (layer.dataProvider().crs() != layers[0].dataProvider().crs()):
			#	QMessageBox.critical(qgis.mainWindow(), 
			#		"Merge Layers", "Merged layers must all have same coordinate system")
			#	return None
				
		layers.append(layer)
		totalfeaturecount += layer.featureCount()

		# Add any fields not in the composite field list
		for sindex, sfield in enumerate(layer.dataProvider().fields()):
			found = None
			for dfield in fields:
				if (dfield.name().upper() == sfield.name().upper()):
					found = dfield
				 	if (dfield.type() != sfield.type()):
						return unicode(sfield.name()) + " attribute type " + \
							unicode(sfield.typeName()) + " in layer " +\
							unicode(layer.name()) + " does not match type " +\
							unicode(dfield.typeName()) + " in other layers"

			if not found:
				fields.append(sfield)

	# for sindex, sfield in enumerate(fields):
	#	print unicode(sindex) + ": " + sfield.name()
			
	if (len(layers) <= 0):
		return "No layers given to merge"
	
	# Create the output shapefile
	if len(savename) <= 0:
		return "No output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", fields,
		layers[0].dataProvider().geometryType(), layers[0].crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Copy layer features to output file
	featurecount = 0
	for layer in layers:
		#feature = QgsFeature()
		#layer.dataProvider().select(layer.dataProvider().attributeIndexes())
		#layer.dataProvider().rewind()
                #while layer.dataProvider().nextFeature(feature):

		for feature in layer.dataProvider().getFeatures():
			sattributes = feature.attributes()
			dattributes = []
			for dindex, dfield in enumerate(fields):
				# dattribute = QVariant(dfield.type())
				# print str(dindex) + ": " + str(dfield.type())

				if (dfield.type() == QVariant.Int):
					dattribute = 0
				elif (dfield.type() == QVariant.Double):
					dattribute = 0.0
				else:
					dattribute = ""

				for sindex, sfield in enumerate(layer.dataProvider().fields()):
					if (sfield.name().upper() == dfield.name().upper()):
						if (sfield.type() != dfield.type()):
							return "Attribute " + unicode(sfield.name()) + \
								" type mismatch " + sfield.typeName() + \
								" != " + dfield.typeName()
						dattribute = sattributes[sindex]
						break

				dattributes.append(dattribute)

			#for dindex, dfield in dattributes.iteritems():
			#	print layer.name() + " (" + str(dindex) + ") " + str(dfield.toString())

			feature.setAttributes(dattributes)
			outfile.addFeature(feature)
			featurecount += 1
			if (featurecount % 50) == 0:
				mmqgis_status_message(qgis, "Writing feature " + \
					unicode(featurecount) + " of " + unicode(totalfeaturecount))

	del outfile

	# Add the merged layer to the project
	if addlayer:
		qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")

	mmqgis_completion_message(qgis, unicode(featurecount) + " records exported")

	return None


# ----------------------------------------------------------
#    mmqgis_points - Create point grid
# ----------------------------------------------------------

def mmqgis_points(qgis, savename, hspacing, vspacing, hoffset, voffset, extent, crs, polygon_layer):

	# Error checks
	if hspacing <= 0:
		return "Horizontal spacing <= 0"

	if vspacing <= 0:
		return "Horizontal spacing <= 0"

	if extent.width() <= 0:
		return "Extent width <= 0"

	if extent.height() <= 0:
		return "Extent height <= 0"

	polygons = None
	if polygon_layer != None:
		polygons = mmqgis_find_layer(polygon_layer)
		if polygons == None:
			return "Invalid polygon layer: " + polygon_layer

	left = (ceil(extent.xMinimum() / hspacing) * hspacing) + hoffset
	right = (floor(extent.xMaximum() / hspacing) * hspacing)
	bottom = (ceil(extent.yMinimum() / vspacing) * vspacing) + voffset
	top = (ceil(extent.yMaximum() / vspacing) * vspacing)

	columns = int(floor((right - left) / hspacing)) + 1
	rows = int(floor((top - bottom) / vspacing)) + 1
	if (columns * rows) > 1048576:
		return "Given dimensions will create over 1 million points"


	# Create the output point shapefile
	if len(savename) <= 0:
		return "No output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	fields = QgsFields()
	fields.append(QgsField("ID", QVariant.Int))
	fields.append(QgsField("POLYGON", QVariant.Int))
	fields.append(QgsField("X", QVariant.Double))
	fields.append(QgsField("Y", QVariant.Double))

	outfile = QgsVectorFileWriter(savename, "utf-8", fields, QGis.WKBPoint, crs)

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())


	# Scan the grid and insert points
	point_id = 0

	for column in range(0, columns):
		for row in range(0, rows):
			x = left + (column * hspacing)
			y = bottom + (row * vspacing)
			point = QgsPoint(x, y)

			# Check if within polygon when bounding polygons are given
			polygon_id = -1
			if polygons != None:
				for index, polygon in enumerate(polygons.dataProvider().getFeatures()):
					if polygon.geometry().contains(point):
						polygon_id = index
						break

			# Add point to output shapefile
			if (polygons == None) or (polygon_id >= 0):
				point_id = point_id + 1
				attributes = [ point_id, polygon_id, x, y ]

				feature = QgsFeature()
				feature.setGeometry(QgsGeometry.fromPoint(point))
				feature.setAttributes(attributes)
				outfile.addFeature(feature)
				
	del outfile

	# Add the merged layer to the project
	qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")

	mmqgis_completion_message(qgis, unicode(point_id) + " points generated")

	return None
	

# ----------------------------------------------------------
#    mmqgis_search - Select features by attribute
# ----------------------------------------------------------

def mmqgis_search(qgis, layername, attributes, comparisons, values, maxfeatures = 0):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Project has no active vector layer to search from"

	if len(attributes) <= 0:
		return "No attributes given for search"

	if len(comparisons) != len(attributes):
		return "Invalid number of comparisons given"

	if len(values) != len(attributes):
		return "Invalid number of comparison values given"

	string_comparisons = ['begins with', 'contains', 'like']
	valid_comparisons = string_comparisons + ['=', '<>', '>', '>=', '<', '<=']

	# Assemble query while error checking
	query = ""
	attribute_indices = []
	for index, attribute in enumerate(attributes):
		if len(attribute) <= 0:
			return "Invalid attribute given"

		if comparisons[index].lower() not in valid_comparisons:
			return "Invalid comparison: " + comparisons[index]

		if len(values[index]) <= 0:
			return "Invalid comparison value given"

		if values[index].find("\'") >= 0:
			return "Search values cannot contain single quote characters"

		x = layer.dataProvider().fieldNameIndex(attribute)
		if x < 0:
			return "Invalid attribute name: " + unicode(attribute)

		attribute_indices.append(x)
		field = layer.dataProvider().fields()[x]

		# print unicode(field.name()) + " = " + unicode(field.type())

		if ((field.type() == int) or (field.type() == float)): # this doesn't seem to catch numeric types
			if comparisons[index] in string_comparisons:
				return comparisons[index] + " cannot be used with numeric types"
			
			newquery = "\"" + attribute + "\" " + comparisons[index] + " " + values[index]

		elif comparisons[index].lower() == 'contains':
			newquery = "\"" + attribute + "\" ILIKE \'%" + values[index] + "%\'"

		elif comparisons[index].lower() == 'begins with':
			newquery = "LOWER(LEFT(\"" + attribute + "\", " + \
				unicode(len(values[index])) + ")) = \'" + values[index].lower() + "\'"

		else: # other string comparisons
			newquery = "LOWER(\"" + attribute + "\") " + comparisons[index] + \
				" LOWER(\'" + values[index] + "\')"

		if index == 0:
			query = newquery
		elif index == 1:	
			query = "(" + query + ") AND (" + newquery + ")"
		else:
			query = query + " AND (" + newquery + ")"
		
	# print query
	expression = QgsExpression(query)

	if not expression.prepare(layer.dataProvider().fields()):
		return "Invalid query: " + query

	found = []
	for index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (index % 500) == 0:
			mmqgis_status_message(qgis, "Scanning feature " + \
				unicode(index) + " of " + unicode(layer.dataProvider().featureCount()))

		if expression.evaluate(feature):
			attributes = ""
			for x in attribute_indices:
				attributes = attributes + unicode(feature.attributes()[x]) + " "

			found.append([feature.id(), attributes])
			if (maxfeatures > 0) and (len(found) > maxfeatures):
				return "Over " + unicode(maxfeatures) + " features found. Narrow your search."

	if len(found) <= 0:
		return "No features found"
	else:
		mmqgis_status_message(qgis, unicode(len(found)) + " features found")
		return found

# ----------------------------------------------------------
#    mmqgis_search_explicit - Find features by attribute
# ----------------------------------------------------------

# This is the old mmqgis_search() function before an upgrade
# to use QgsExpression for evaluation. It is retained here
# as a backup and will be removed in future versions.

def mmqgis_search_explicit(qgis, layername, attributes, comparisons, values, maxfeatures = 0):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Project has no active vector layer to search from"

	if len(attributes) <= 0:
		return "No attributes given for search"
	if len(comparisons) != len(attributes):
		return "Invalid number of comparisons given"
	if len(values) != len(attributes):
		return "Invalid number of comparison values given"

	attribute_indices = []
	valid_comparisons = ['==', '!=', '>', '>=', '<', '<=', 'begins with', 'contains']
	for index, attribute in enumerate(attributes):
		if len(attribute) <= 0:
			return "Invalid attribute given"
		if comparisons[index] not in valid_comparisons:
			return "Invalid comparison: " + comparisons[index]
		if len(values[index]) <= 0:
			return "Invalid comparison value given"

		x = layer.dataProvider().fieldNameIndex(attribute)
		if x < 0:
			return "Invalid attribute name: " + unicode(attribute)
		else:
			attribute_indices.append(x)
		
		# print "Comp " + unicode(index) + " = " + unicode(attribute) + " = attribute " + unicode(x)


	found = []
	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (feature_index % 100) == 0:
			mmqgis_status_message(qgis, "Scanning feature " + \
				unicode(feature_index) + " of " + unicode(layer.dataProvider().featureCount()))

		match_all = True
		match_attributes = ""
		for comp_index in range(0, len(attribute_indices)):
			if (type(feature.attributes()[attribute_indices[comp_index]]) == int) or \
			   (type(feature.attributes()[attribute_indices[comp_index]]) == float):
				if (comparisons[comp_index] == 'begins with') or (comparisons[comp_index] == 'contains'):
					return "Begins with or contains cannot be used with numeric types"

				try:
					x = float(feature.attributes()[attribute_indices[comp_index]])
					y = float(values[comp_index])
				except:
					return "Non-numeric value used in comparison with numeric field: " + \
						unicode(comparisons[comp_index])

			else: # string comparisons
				x = unicode(feature.attributes()[attribute_indices[comp_index]]).lower()
				y = unicode(values[comp_index]).lower()
			
			match = False
			if (comparisons[comp_index] == '=='):
				match = (x == y)
			elif (comparisons[comp_index] == '!='):
				match = (x != y)
			elif (comparisons[comp_index] == '>'):
				match = (x > y)
			elif (comparisons[comp_index] == '>='):
				match = (x >= y)
			elif (comparisons[comp_index] == '<'):
				match = (x < y)
			elif (comparisons[comp_index] == '<='):
				match = (x <= y)
			elif (comparisons[comp_index] == 'begins with'):
				match = x.startswith(y)
			elif (comparisons[comp_index] == 'contains'):
				match = (x.find(y) >= 0)

			if not match:
				match_all = False
			elif comp_index == 0:
				match_attributes = unicode(x)
			else:
				match_attributes = match_attributes + "," + unicode(x)

			# print "Comparing: " + unicode(x) + " " + comparisons[comp_index] + " " + \
			# 	unicode(y) + " = " + unicode(match) + "/" + unicode(match_all)

		if match_all:
			found.append([feature.id(), match_attributes])
			if (maxfeatures > 0) and (len(found) > maxfeatures):
				return "Over " + unicode(maxfeatures) + " features found. Narrow your search."

	if len(found) <= 0:
		return "No features found"
	else:
		return found

# ----------------------------------------------------------
#    mmqgis_select - Select features by attribute
# ----------------------------------------------------------

def mmqgis_select(qgis, layername, attributes, comparisons, values, savename, addlayer):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Project has no active vector layer to save from"

	feature_list = mmqgis_search(qgis, layername, attributes, comparisons, values)
	if type(feature_list) != list:
		return feature_list # error message

	feature_ids = []
	for feature_id, value in feature_list:
		feature_ids.append(feature_id)

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", layer.dataProvider().fields(),
			layer.dataProvider().geometryType(), layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	writecount = 0
	for index, feature in enumerate(layer.dataProvider().getFeatures()):
		if feature.id() in feature_ids:
			outfile.addFeature(feature)
			writecount += 1

		if (index % 20) == 0:
			mmqgis_status_message(qgis, "Scanning feature " + \
				unicode(index) + " of " + unicode(layer.dataProvider().featureCount()) + \
				"(" + unicode(writecount) + " selected)")

	del outfile

	if addlayer:
		vlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
		
	mmqgis_completion_message(qgis, "Selected " + unicode(writecount) + " features to " + savename)

	return None

# --------------------------------------------------------
#    mmqgis_sort - Sort shapefile by attribute
# --------------------------------------------------------

def mmqgis_sort(qgis, layername, sortattributename, savename, direction, addlayer):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Project has no active vector layer to sort"

	sortindex = layer.dataProvider().fieldNameIndex(sortattributename)
	if sortindex < 0:
		return "Invalid sort field name: " + sortattributename
	
	# print  "sortindex = " + str(sortindex)

	if len(savename) <= 0:
		return "No output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", layer.dataProvider().fields(),
			layer.dataProvider().geometryType(), layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	#feature = QgsFeature()
	#layer.dataProvider().select(layer.dataProvider().attributeIndexes())
	#layer.dataProvider().rewind()
	#while layer.dataProvider().nextFeature(feature):

	table = []
	for index, feature in enumerate(layer.dataProvider().getFeatures()):
		# featuretype = feature.attributes()[sortindex].type()
		# if (featuretype == QVariant.Int):
		#	record = feature.id(), feature.attributes()[sortindex].toInt()
		# elif (featuretype == QVariant.Double):
		#	record = feature.id(), feature.attributes()[sortindex].toDouble()
		# else:
		#	record = feature.id(), unicode(feature.attributes()[sortindex].toString())

		if (index % 50) == 0:
			mmqgis_status_message(qgis, "Reading feature " + unicode(feature.id()))

		record = feature.id(), feature.attributes()[sortindex]

		table.append(record)

	if (direction.lower() == "descending"):
		table.sort(key = operator.itemgetter(1), reverse=True)
	else:
		table.sort(key = operator.itemgetter(1))

	writecount = 0
	for index, record in enumerate(table):
		# feature = QgsFeature()
		# layer.featureAtId(record[0], feature)
		feature = mmqgis_feature_at_id(layer, record[0])
		outfile.addFeature(feature)
		writecount += 1

		if (index % 50) == 0:
			mmqgis_status_message(qgis, "Writing feature " + unicode(writecount) +\
				" of " + unicode(len(table)))

	del outfile

	if addlayer:
		vlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
		
	mmqgis_completion_message(qgis, "Sorted shapefile created from " + layername)

	return None

# ----------------------------------------------------------
#    mmqgis_spatial_join - Spatial Join
# ----------------------------------------------------------

def mmqgis_spatial_join(qgis, targetname, spatialop, joinname, fields, fieldop, outfilename, addlayer):
	target_layer = mmqgis_find_layer(targetname)
	if target_layer == None:
		return "Invalid target layer name: " + targetname

	join_layer = mmqgis_find_layer(joinname)
	if join_layer == None:
		return "Invalid join layer name: " + joinname

	if len(fields) != len(set(fields)):
		return "Duplicate output field names from different layers"

	# Rasters don't have fields()
	if (not hasattr(target_layer.dataProvider(), "fields")):
		return "Target layer has no fields (raster layer?)";

	if (not hasattr(join_layer.dataProvider(), "fields")):
		return "Join layer has no fields (raster layer?)";

	transform = None
	if target_layer.crs() != join_layer.crs():
		transform = QgsCoordinateTransform(join_layer.crs(), target_layer.crs())


	# Build composite field list
	field_info = [] # [ layer, index, QgsField ]
	newfields = QgsFields()
	for index, field in enumerate(target_layer.dataProvider().fields()):
		if field.name() in fields:
			newfields.append(field)
			field_info.append([target_layer, index, field])
			# print unicode(len(field_info) - 1) + " = " + field.name()

	# Add fields from join features
	for index, field in enumerate(join_layer.dataProvider().fields()):
		if field.name() in fields:
			if target_layer.dataProvider().fields().indexFromName(field.name()) >= 0:
				return "Ambiguous field name in both target and join layers: " + field.name()
				
			# INT fields converted to DOUBLE to avoid overflow and rounding errors
			if field.type() == QVariant.Int:
				field = QgsField(field.name(), QVariant.Double)
				# print "Int to Double"

			newfields.append(field)
			field_info.append([join_layer, index, field])
			# print unicode(len(field_info) - 1) + " = " + field.name() + " " + unicode(field.type())

	# Add field to count number of joined features
	count_field = QgsField("COUNT", QVariant.Int)
	newfields.append(count_field)
	field_info.append([None, 0, count_field])

	# Open file (delete any existing)
	if QFile(outfilename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(outfilename):
			return "Failure deleting existing shapefile: " + outfilename

	outfile = QgsVectorFileWriter(outfilename, "utf-8", newfields,
		target_layer.dataProvider().geometryType(), target_layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Interate through target features
	target_count = 0
	feature_count = target_layer.featureCount()
	for target_index, target_feature in enumerate(target_layer.dataProvider().getFeatures()):
		if (target_index % 10) == 0:
			mmqgis_status_message(qgis, "Joining feature " + unicode(target_index) + \
				" of " + unicode(feature_count))

		target_geometry = target_feature.geometry()

		# Copy all selected target attributes
		attributes = []
		for fieldlayer, fieldindex, field in field_info:
			if fieldlayer == target_layer:
				attributes.append(target_feature.attributes()[fieldindex])
			elif fieldlayer == join_layer:
				attributes.append(None)
			else:
				attributes.append(0) # count

		# Iterate through join features
		join_count = 0
		for join_index, join_feature in enumerate(join_layer.dataProvider().getFeatures()):
			join_geometry = join_feature.geometry()
			if transform:
				join_geometry.transform(transform)
			
			if ((spatialop == 'Intersects') and (target_geometry.intersects(join_geometry))) or \
			   ((spatialop == 'Within') and (target_geometry.within(join_geometry))) or \
			   ((spatialop == 'Contains') and (target_geometry.contains(join_geometry))):

				join_count = join_count + 1
				# print unicode(target_index) + " -> " + unicode(join_index) + " = " + unicode(join_count)

				for dest_index, field in enumerate(field_info):
					if field[0] == join_layer:
						attribute = join_feature.attributes()[field[1]]

						# print "   " + fieldop + ": " + unicode(dest_index) + " = join " + unicode(field[1])

						# Since strings cannot be mathematically combined,
						# non-scalar attributes are always the first encountered
						if (fieldop == "First") or (field[2].type() != QVariant.Double):
							if (join_count == 1):
								attributes[dest_index] = attribute

						else:
							ratio = 1.0
							if fieldop == "Proportional Sum":
								total_area = join_geometry.area()
								intersect_area = target_geometry.intersection(join_geometry).area()
								if (total_area > 0):
									ratio = intersect_area / total_area
							try:
								if join_count <= 1:
									target_value = 0
								else:
									target_value = float(attributes[dest_index])

								join_value = float(join_feature.attributes()[field[1]])
								attributes[dest_index] = target_value + (ratio * join_value)
							except:
								attributes[dest_index] = 0

						# print unicode(target_index) + ":" + unicode(join_index) + ") " + \
						#	unicode(target_value) + " + " + unicode(join_value) + " * " + \
						#	unicode(ratio)
						

		# Divide sums to get averages
		if (fieldop == "Average") and (join_count > 0):
			for dest_index, field in enumerate(field_info):
				if (field[0] == join_layer) and (field[2].type() == QVariant.Double):
					attributes[dest_index] = float(attributes[dest_index]) / float(join_count)

		# Counter
		attributes[len(field_info) - 1] = join_count

		# Add the feature
		# if join_count > 0:
		target_count = target_count + 1
		newfeature = QgsFeature()
		newfeature.setGeometry(target_feature.geometry())
		newfeature.setAttributes(attributes)
		# print unicode(target_count) + ") " + unicode(attributes[0].toString())
		if not outfile.addFeature(newfeature):
			return "Failure writing feature to shapefile"

	del outfile

	if addlayer:
		qgis.addVectorLayer(outfilename, os.path.basename(outfilename), "ogr")
		
	mmqgis_completion_message(qgis, unicode(target_count) + " features joined")

	return None

# ---------------------------------------------------------
#    mmqgis_text_to_float - Change text fields to numbers
# ---------------------------------------------------------

def mmqgis_text_to_float(qgis, layername, attributes, savename, addlayer):
	layer = mmqgis_find_layer(layername)
	if layer == None:
		return "Project has no active vector layer to convert: " + layername

	if len(savename) <= 0:
		return "No output filename given"

	# Build list of fields with selected fields changed to floating point
	changecount = 0
	destfields = QgsFields()
	fieldchanged = []
	for index, field in enumerate(layer.dataProvider().fields()):
		if (field.name() in attributes) and ((field.type() == QVariant.String) or (field.type() == QVariant.Int)):
			fieldchanged.append(True)
			# Arbitrary floating point length/precision 14.6 = nnnnnnnnnnnnnn.dddddd
			destfields.append(QgsField (field.name(), QVariant.Double, field.typeName(), \
				14, 6, field.comment()))
		else:
			changecount += 1
			fieldchanged.append(False)
			destfields.append(QgsField (field.name(), field.type(), field.typeName(), \
				field.length(), field.precision(), field.comment()))

	if (changecount <= 0):
		return "No string or integer fields selected for conversion to floating point"


	# Create the output file
	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", destfields,
			layer.dataProvider().geometryType(), layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())


	# Write the features with modified attributes
	featurecount = layer.dataProvider().featureCount();
	for feature_index, feature in enumerate(layer.dataProvider().getFeatures()):
		if (feature_index % 50) == 0:
			mmqgis_status_message(qgis, "Writing feature " + \
				unicode(feature.id()) + " of " + unicode(featurecount))

		attributes = feature.attributes()
		for index, field in enumerate(layer.dataProvider().fields()):
			if fieldchanged[index]:
				# string = unicode(attributes[index].toString())
				string = unicode(attributes[index])
				multiplier = 1.0
				if string.find("%") >= 0:
					multiplier = 1 / 100.0
					string = string.replace("%", "")
				if string.find(",") >= 0:
					string = string.replace(",", "")

				try:	
					value = float(string) * multiplier
				except:
					value = 0
						
				# attributes[index] = QVariant(value)
				attributes[index] = value

		feature.setAttributes(attributes)
		outfile.addFeature(feature)

	del outfile

	if addlayer:
		vlayer = qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")
		
	mmqgis_completion_message(qgis, unicode(changecount) + " text fields converted to numeric")

	return None


# --------------------------------------------------------
#    mmqgis_voronoi - Voronoi diagram creation
# --------------------------------------------------------

def mmqgis_voronoi_diagram(qgis, sourcelayer, savename, addlayer):
	layer = mmqgis_find_layer(sourcelayer)
	if layer == None:
		return "Layer " + sourcename + " not found"
	
	if len(savename) <= 0:
		return "No output filename given"

	if QFile(savename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(savename):
			return "Failure deleting existing shapefile: " + savename

	outfile = QgsVectorFileWriter(savename, "utf-8", layer.dataProvider().fields(), \
			QGis.WKBPolygon, layer.crs())

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	points = []
	xmin = 0
	xmax = 0
	ymin = 0
	ymax = 0

	#feature = QgsFeature()
	#layer.dataProvider().select(layer.dataProvider().attributeIndexes())
	#layer.dataProvider().rewind()
	#while layer.dataProvider().nextFeature(feature):

	for feature in layer.dataProvider().getFeatures():
		# Re-read by feature ID because nextFeature() doesn't always seem to read attributes
		# layer.featureAtId(feature.id(), feature)
		geometry = feature.geometry()
		mmqgis_status_message(qgis, "Reading feature " + unicode(feature.id()))
		# print str(feature.id()) + ": " + str(geometry.wkbType())
		if geometry.wkbType() == QGis.WKBPoint:
			points.append( (geometry.asPoint().x(), geometry.asPoint().y(), feature.attributes()) )
			if (len(points) <= 1) or (xmin > geometry.asPoint().x()):
				xmin = geometry.asPoint().x()
			if (len(points) <= 1) or (xmax < geometry.asPoint().x()):
				xmax = geometry.asPoint().x()
			if (len(points) <= 1) or (ymin > geometry.asPoint().y()):
				ymin = geometry.asPoint().y()
			if (len(points) <= 1) or (ymax < geometry.asPoint().y()):
				ymax = geometry.asPoint().y()

	if (len(points) < 3):
		return "Too few points to create diagram"

	for point_number, center in enumerate(points):
	# for center in [ points[17] ]:
		# print "\nCenter, " + str(center[0]) + ", " + str(center[1])
		if (point_number % 20) == 0:
			#mmqgis_status_message(qgis, "Processing point " + \
			#	unicode(center[0]) + ", " + unicode(center[1]))
			mmqgis_status_message(qgis, "Processing point " + unicode(point_number) + " of " + unicode(len(points)))

		# Borders are tangents to midpoints between all neighbors
		tangents = []
		for neighbor in points:
			border = mmqgis_voronoi_line((center[0] + neighbor[0]) / 2.0, (center[1] + neighbor[1]) / 2.0)
			if ((neighbor[0] != center[0]) or (neighbor[1] != center[1])):
				tangents.append(border)

		# Add edge intersections to clip to extent of points
		offset = (xmax - xmin) * 0.01
		tangents.append(mmqgis_voronoi_line(xmax + offset, center[1]))
		tangents.append(mmqgis_voronoi_line(center[0], ymax + offset))
		tangents.append(mmqgis_voronoi_line(xmin - offset, center[1]))
		tangents.append(mmqgis_voronoi_line(center[0], ymin - offset))
		#print "Extent x = " + str(xmax) + " -> " + str(xmin) + ", y = " + str(ymax) + " -> " + str(ymin)

		# Find vector distance and angle to border from center point
		for scan in range(0, len(tangents)):
			run = tangents[scan].x - center[0]
			rise = tangents[scan].y - center[1]
			tangents[scan].distance = sqrt((run * run) + (rise * rise))
			if (tangents[scan].distance <= 0):
				tangents[scan].angle = 0
			elif (tangents[scan].y >= center[1]):
				tangents[scan].angle = acos(run / tangents[scan].distance)
			elif (tangents[scan].y < center[1]):
				tangents[scan].angle = (2 * pi) - acos(run / tangents[scan].distance)
			elif (tangents[scan].x > center[0]):
				tangents[scan].angle = pi / 2.0
			else:
				tangents[scan].angle = 3 * pi / 4

			#print "  Tangent, " + str(tangents[scan].x) + ", " + str(tangents[scan].y) + \
			#	", angle " + str(tangents[scan].angle * 180 / pi) + ", distance " + \
			#	str(tangents[scan].distance)


		# Find the closest line - guaranteed to be a border
		closest = -1
		for scan in range(0, len(tangents)):
			if ((closest == -1) or (tangents[scan].distance < tangents[closest].distance)):
				closest = scan

		# Use closest as the first border
		border = mmqgis_voronoi_line(tangents[closest].x, tangents[closest].y)
		border.angle = tangents[closest].angle
		border.distance = tangents[closest].distance
		borders = [ border ]

		#print "  Border 0) " + str(closest) + " of " + str(len(tangents)) + ", " \
		#	+ str(border.x) + ", " + str(border.y) \
		#	+ ", (angle " + str(border.angle * 180 / pi) + ", distance " \
		#	+ str(border.distance) + ")"

		# Work around the tangents in a CCW circle
		circling = 1
		while circling:
			next = -1
			scan = 0
			while (scan < len(tangents)):
				anglebetween = tangents[scan].angle - borders[len(borders) - 1].angle
				if (anglebetween < 0):
					anglebetween += (2 * pi)
				elif (anglebetween > (2 * pi)):
					anglebetween -= (2 * pi)

				#print "    Scanning " + str(scan) + " of " + str(len(borders)) + \
				#	", " + str(tangents[scan].x) + ", " + str(tangents[scan].y) + \
				#	", angle " + str(tangents[scan].angle * 180 / pi) + \
				#	", anglebetween " + str(anglebetween * 180 / pi)

				# If border intersects to the left
				if (anglebetween < pi) and (anglebetween > 0):
					# A typo here with a reversed slash cost 8/13/2009 debugging
					tangents[scan].iangle = atan2( (tangents[scan].distance / 
						borders[len(borders) - 1].distance) \
						- cos(anglebetween), sin(anglebetween))
					tangents[scan].idistance = borders[len(borders) - 1].distance \
						/ cos(tangents[scan].iangle)

					tangents[scan].iangle += borders[len(borders) - 1].angle

					# If the rightmost intersection so far, it's a candidate for next border
					if (next < 0) or (tangents[scan].iangle < tangents[next].iangle):
						# print "      Take idistance " + str(tangents[scan].idistance)
						next = scan

				scan += 1

			# iangle/distance are for intersection of border with next border
			borders[len(borders) - 1].iangle = tangents[next].iangle
			borders[len(borders) - 1].idistance = tangents[next].idistance

			# Stop circling if back to the beginning
			if (borders[0].x == tangents[next].x) and (borders[0].y == tangents[next].y):
				circling = 0

			else:
				# Add the next border
				border = mmqgis_voronoi_line(tangents[next].x, tangents[next].y)
				border.angle = tangents[next].angle
				border.distance = tangents[next].distance
				border.iangle = tangents[next].iangle
				border.idistance = tangents[next].idistance
				borders.append(border)
				#print "  Border " + str(len(borders) - 1) + \
				#	") " + str(next) + ", " + str(border.x) + \
				#	", " + str(border.y) + ", angle " + str(border.angle * 180 / pi) +\
				#	", iangle " + str(border.iangle * 180 / pi) +\
				#	", idistance " + str(border.idistance) + "\n"

			# Remove the border from the list so not repeated
			tangents.pop(next)
			if (len(tangents) <= 0):
				circling = 0

		polygon = []
		if len(borders) >= 3:
			for border in borders:
				ix = center[0] + (border.idistance * cos(border.iangle))
				iy = center[1] + (border.idistance * sin(border.iangle))
				#print "  Node, " + str(ix) + ", " + str(iy) + \
				#	", angle " + str(border.angle * 180 / pi) + \
				#	", iangle " + str(border.iangle * 180 / pi) + \
				#	", idistance " + str(border.idistance) + ", from " \
				#	+ str(border.x) + ", " + str(border.y)
				polygon.append(QgsPoint(ix, iy))

			#print "Polygon " + unicode(point_number)
			#for x in range(0, len(polygon)):
			#	print "  Point " + unicode(polygon[x].x()) + ", " + unicode(polygon[x].y())

			# Remove duplicate nodes
			# Compare as strings (unicode) to avoid odd precision discrepancies
			# that sometimes cause duplicate points to be unrecognized
			dup = 0
			while (dup < (len(polygon) - 1)):
				if (unicode(polygon[dup].x()) == unicode(polygon[dup + 1].x())) and \
				   (unicode(polygon[dup].y()) == unicode(polygon[dup + 1].y())):
					polygon.pop(dup)
					# print "  Removed duplicate node " + unicode(dup) + \
					#	" in polygon " + unicode(point_number)
				else:
					# print "  " + unicode(polygon[dup].x()) + ", " + \
					#	unicode(polygon[dup].y()) + " != " + \
					#	unicode(polygon[dup + 1].x()) + ", " + \
					#	unicode(polygon[dup + 1].y())
					dup = dup + 1

			# attributes = { 0:QVariant(center[0]), 1:QVariant(center[1]) }

		if len(polygon) >= 3:
			geometry = QgsGeometry.fromPolygon([ polygon ])
			feature = QgsFeature()
			feature.setGeometry(geometry)
			feature.setAttributes(center[2])
			outfile.addFeature(feature)
				
	del outfile

	if addlayer:
		qgis.addVectorLayer(savename, os.path.basename(savename), "ogr")

	mmqgis_completion_message(qgis, "Created " + unicode(len(points)) + " polygon Voronoi diagram")

	return None

class mmqgis_voronoi_line:
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.angle = 0
		self.distance = 0

	def list(self, title):
		print title + ", " + unicode(self.x) + ", " + unicode(self.y) + \
			", angle " + unicode(self.angle * 180 / pi) + ", distance " + unicode(self.distance)

	def angleval(self):
		return self.angle


