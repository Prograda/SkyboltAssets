import urllib.request as request
from pyorbital.orbital import Orbital
import logging
import echelon
import math

logger = logging.getLogger(__name__)

def readOrbitals(url):
	orbitals = {}

	f = request.urlopen(url)
	name = f.readline()
	while name:
		name = name.decode("utf-8").strip()
		line1 = f.readline().decode("utf-8")
		line2 = f.readline().decode("utf-8")
		try:
			orbitals[name] = Orbital(name, None, line1, line2)
		except Exception as e:
			logger.warning("Skipping satellite '{0}'. {1}".format(name, str(e)))
		name = f.readline()

	return orbitals

def pyorbitalLlaToechelon(lonLatAlt):
	return echelon.LatLonAlt(math.radians(lonLatAlt[1]), math.radians(lonLatAlt[0]), lonLatAlt[2]*1000.0);
	
	# From https://en.wikipedia.org/wiki/True_anomaly#From_the_mean_anomaly
def meanAnomalyToTrue(m, e):
	return m + 2 * e - 0.25 * pow(e, 3) * math.sin(m) + 5.0/4.0 * e*e * math.sin(2 * m) + 13.0/12.0 * pow(e, 3) * math.sin(3 * m)
	
def pyorbitalOrbitalElementToechelon(element):
	orbit = echelon.Orbit()
	orbit.semiMajorAxis = element.semi_major_axis  * 6378135.0
	orbit.eccentricity = element.excentricity
	orbit.inclination = element.inclination
	orbit.rightAscension = element.right_ascension
	orbit.argumentOfPeriapsis = element.arg_perigee
	orbit.trueAnomaly = meanAnomalyToTrue(element.mean_anomaly, element.excentricity);
	return orbit
	
class Satellites():
	def __init__(self, ownerEntity, utc_time):
		self.orbitals = readOrbitals("https://www.celestrak.com/NORAD/elements/active.txt")
		
		count = 0
		self.entities = {}
		for name, orbital in self.orbitals.items():
		
			entity = echelon.getEntityFactory().createEntity("Satellite", name, echelon.Vector3(), echelon.Quaternion())
			entity.dynamicsEnabled = False
			entity.addComponent(echelon.ParentReferenceComponent(ownerEntity))
			entity.addComponent(echelon.ProceduralLifetimeComponent())
			
			orbit = echelon.OrbitComponent()
			orbit.orbit = pyorbitalOrbitalElementToechelon(orbital.orbit_elements)
			entity.addComponent(orbit)

			echelon.getWorld().addEntity(entity)
			self.entities[entity] = orbital

			# Limit total satellites
			count += 1
			if (count >= 100):
				break

		self.update(utc_time)

	def __del__(self):
		for entity in self.entities:
			echelon.getWorld().removeEntity(entity)
		
	def update(self, utc_time):
		for entity, orbital in self.entities.items():
			lla = pyorbitalLlaToechelon(orbital.get_lonlatalt(utc_time))
			position = echelon.toGeocentricPosition(echelon.LatLonAltPosition(lla))
			entity.setPosition(position.position)
