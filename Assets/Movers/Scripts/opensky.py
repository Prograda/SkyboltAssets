import urllib.request as request
import json
import logging
import echelon
import math

logger = logging.getLogger(__name__)

class Plane:
	def __init__(self):
		self.name = ""
		self.lla = echelon.LatLonAlt()
		self.heading = 0

def readPlanes():
	planes = []

	# Format documentation: https://opensky-network.org/apidoc/rest.html#all-state-vectors
	f = request.urlopen("https://opensky-network.org/api/states/all")
	data = json.load(f)
	counter = 0
	for state in data["states"]:
		name = state[1]
		lon = state[5]
		lat = state[6]
		alt = state[7]
		heading = state[10]
		if name != None and lon != None and lat != None and alt != None and heading != None:
			plane = Plane()
			plane.name = name.strip()
			if plane.name != "":
				plane.lla.lat = math.radians(lat)
				plane.lla.lon = math.radians(lon)
				plane.lla.alt = alt
				plane.heading = math.radians(heading)
				planes.append(plane)

	return planes

class Planes():
	def __init__(self, ownerEntity, utc_time):
	
		planes = readPlanes()
		self.entities = {}
		
		count = 0
		for plane in planes:
			entity = echelon.getEntityFactory().createEntity("Shuttle", plane.name, echelon.Vector3(), echelon.Quaternion())
			entity.dynamicsEnabled = False
			entity.addComponent(echelon.ParentReferenceComponent(ownerEntity))
			entity.addComponent(echelon.ProceduralLifetimeComponent())
			echelon.getWorld().addEntity(entity)
			self.entities[entity] = plane
			
			# Limit total planes
			count += 1
			if (count > 100):
				break
		
		self.update(utc_time)
		
	def __del__(self):
		for entity in self.entities:
			echelon.getWorld().removeEntity(entity)
		
	def update(self, utc_time):
		for entity, plane in self.entities.items():
			position = echelon.toGeocentricPosition(echelon.LatLonAltPosition(plane.lla))
			entity.setPosition(position.position)
			
			ltpNedOrientation = echelon.quaternionFromEuler(echelon.Vector3(0,0,plane.heading))
			orientation = echelon.toGeocentricOrientation(echelon.LtpNedOrientation(ltpNedOrientation), echelon.toLatLon(plane.lla))
			entity.setOrientation(orientation.orientation)
