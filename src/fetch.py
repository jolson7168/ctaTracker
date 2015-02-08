import glob
import os
import json
import csv
import logging
import sys
import getopt
import time
import decimal
import requests
import xmltodict


config = {}
apiKeys=[]
routes = {}

class apiKey:
  def __init__(self):
    self.key = ""
    self.counter = 0

def initAPIKeys(configAPIKeys):
	apiKeys = []
	for x in range (0, len(configAPIKeys)):
		newKey = apiKey()
		newKey.key = configAPIKeys[x]
		newKey.counter = 0
		apiKeys.append(newKey)

	return apiKeys	

def currentDayStr():
	return time.strftime("%Y%m%d")

def currentTimeStr():
	return time.strftime("%H:%M:%S")

def initLog():
	logger = logging.getLogger(config["logname"])
	hdlr = logging.FileHandler(config["logFile"])
	formatter = logging.Formatter(config["logFormat"],config["logTimeFormat"])
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr) 
	logger.setLevel(logging.INFO)
	return logger

def fetchRoutes(url, apiKeys):
	whichKey = int(time.strftime("%H")) % len(apiKeys)
	logger = logging.getLogger(config["logname"])
	tempRoutes = {}
	r1=requests.get(url+apiKeys[whichKey].key)
	apiKeys[whichKey].counter = apiKeys[whichKey].counter+1
	logger.info("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") Requesting Routes...")
	routes = dict(xmltodict.parse(r1.text)['bustime-response'])
	for route in routes["route"]:
		tempRoutes[route["rt"]]=route
	logger.info("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") Got "+ str(len(tempRoutes.keys()))+" routes")
	return tempRoutes

def breakupRoutes(routes, numPerReq):
	routeRequests=[]
	count = 0
	thisEntry = ""
	for route in routes.keys():
		count=count+1
		thisEntry = thisEntry+route+","
		if (count % numPerReq == 0):
			routeRequests.append(thisEntry[:-1])
			thisEntry = ""
	routeRequests.append(thisEntry[:-1])
	return routeRequests

def makeRouteRequest(url, routes, apiKeys):

	logger = logging.getLogger(config["logname"])
	whichKey = int(time.strftime("%H")) % len(apiKeys)
	fixArray = []
	tempFixes = {}
	f1=requests.get(url+apiKeys[whichKey].key+"&rt="+routes)
	apiKeys[whichKey].counter = apiKeys[whichKey].counter+1
	logger.info("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") Requesting fixes by routes ("+routes+")"+"...")
	fixes = dict(xmltodict.parse(f1.text)['bustime-response'])
	if "error" in fixes:
		errorStr=""
		for error in fixes["error"]:
			if isinstance(error, basestring):
				errorStr=fixes["error"]["rt"]
			else:
				if "rt" in error:
					errorStr=errorStr+error["rt"]+","
		if (errorStr == ""):
			logger.info("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") General error: "+error)
		else:
			if errorStr[-1:]==",":
				errorStr = errorStr[:-1] 	
			logger.info("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") No data reported on the following routes: "+errorStr)

	if "vehicle" in fixes:
		for vehicle in fixes["vehicle"]:
			if "vid" in vehicle: 
				vehicle["vid"] = int(vehicle["vid"])
			if "lat" in vehicle:
				vehicle["lat"] = float(vehicle["lat"])
			if "lon" in vehicle:
				vehicle["lon"] = float(vehicle["lon"])
			if "hdg" in vehicle:
				vehicle["hdg"] = int(vehicle["hdg"])
			if "pid" in vehicle:
				vehicle["pid"] = int(vehicle["pid"])
			if "pdist" in vehicle:
				vehicle["pdist"] = int(vehicle["pdist"])
			if "spd" in vehicle:
				vehicle["spd"] = int(vehicle["spd"])
			if "tatripid" in vehicle:
				vehicle["tatripid"] = int(vehicle["tatripid"])
			# Nice to have, but takes up too much space...			
			#if "tmstmp" in vehicle:
			#	vehicle["javascripttime"] = int(time.mktime(time.strptime(vehicle["tmstmp"], "%Y%m%d %H:%M"))*1000)
			fixArray.append(vehicle)
		logger.info("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") Number of vehicle fixes returned: "+str(len(fixArray)))
	return fixArray

def dumpFixes(fixes, fileName):
	#figure out a better way to do this...
	strWrite = json.dumps(fixes)
	strWrite = strWrite.replace("[","").replace("]","").replace("}, {","}{")  				
	strWrite = strWrite.replace("}","}\n")
	with open(config["datafilePath"]+"/"+fileName+".json", "a") as dumpFile:
    		dumpFile.write(strWrite)

def main(argv):
 	try:
      		opts, args = getopt.getopt(argv,"hc:",["configfile="])
	except getopt.GetoptError:
		print ('fetchData.py -c <configfile>')
      		sys.exit(2)
	for opt, arg in opts:
      		if opt == '-h':
         		print ('fetchData.py -c <configfile>')
         		sys.exit()
		elif opt in ("-c", "--configfile"):
			configFile=arg
			try:
   				with open(configFile): pass
			except IOError:
   				print ('Configuration file: '+configFile+' not found')
				sys.exit(2)
	execfile(configFile, config)
	logger=initLog()
	logger.info('Starting Run: '+currentDayStr()+'  ========================================')
	apiKeys=initAPIKeys(config["apiKeys"])
	currentDay = currentDayStr()
	#Get the routes
	routes = fetchRoutes(config["routesURL"],apiKeys)
	routeRequests = breakupRoutes(routes,config["routesPerRequest"])
	done = False
	while not done:
		if int(time.strftime("%S")) == 0:  #Once per minute
			for x in range (0,len(routeRequests)):
				fixes=makeRouteRequest(config["vehiclesURL"],routeRequests[x], apiKeys)
				if currentDay<>currentDayStr():    # A new day is upon us
					logger.info("Doing end of day. From "+currentDay+" to "+currentDayStr() +". Resetting API counters, and archiving log.")
					logger.info('Done: '+currentDayStr()+'  ========================================')
					logger.handlers[0].stream.close()
					logger.removeHandler(logger.handlers[0])
					os.rename(config["logFile"],config["logFile"].replace(".log","_"+currentDay+".log"))
					logger=initLog()
					logger.info('Starting Run: '+currentDayStr()+'  ========================================')
					currentDay = currentDayStr()
					apiKeys=initAPIKeys(config["apiKeys"])  #reset the counters
				dumpFixes(fixes, currentDay)
		if (int(time.strftime("%M")) == 0) and (int(time.strftime("%S")) == 30):	#Once per hour (per day??)
			routes = fetchRoutes(config["routesURL"],apiKeys)
			routeRequests = breakupRoutes(routes,config["routesPerRequest"])


if __name__ == "__main__":
	main(sys.argv[1:])
