from __future__ import print_function
import glob
import os
import json
import csv
import logging
from collections import defaultdict
import sys
import getopt
import time
import decimal
import requests
import xmltodict


config = {}
apiKeys=[]
routes = {}
requestCount = 0

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

def fetchRoutes(url, apiKey):
	global requestCount

	logger = logging.getLogger(config["logname"])
	tempRoutes = {}
	r1=requests.get(url+apiKey)
	requestCount = requestCount+1
	logger.info("(Request count: "+str(requestCount)+") Requesting Routes...")
	routes = dict(xmltodict.parse(r1.text)['bustime-response'])
	for route in routes["route"]:
		tempRoutes[route["rt"]]=route
	logger.info("(Request count: "+str(requestCount)+") Got "+ str(len(tempRoutes.keys()))+" routes")
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

def makeRouteRequest(url, routes, apiKey):
	global requestCount

	logger = logging.getLogger(config["logname"])
	fixArray = []
	tempFixes = {}
	f1=requests.get(url+apiKey+"&rt="+routes)
	requestCount = requestCount+1
	logger.info("(Request count: "+str(requestCount)+") Requesting Fixes by routes ("+routes+")"+"...")
	fixes = dict(xmltodict.parse(f1.text)['bustime-response'])
	if "error" in fixes:
		errorStr=""
		for error in fixes["error"]:
			if isinstance(error, basestring):
				errorStr=fixes["error"]["rt"]
				logger.info("(Request count: "+str(requestCount)+") No data reported on the following route: "+errorStr)
			else:
				if "rt" in error:
					errorStr=errorStr+error["rt"]+","
					logger.info("(Request count: "+str(requestCount)+") No data reported on the following routes: "+errorStr[:-1])
				else:
					logger.info("(Request count: "+str(requestCount)+") General error: "+error)
								
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
			if "tmstmp" in vehicle:
				vehicle["timestr"] = vehicle["tmstmp"].split(' ')[0]
				vehicle["datestr"] = vehicle["tmstmp"].split(' ')[1]
				vehicle["javascripttime"] = int(time.mktime(time.strptime(vehicle["tmstmp"], "%Y%m%d %H:%M"))*1000)
			fixArray.append(vehicle)
		logger.info("(Request count: "+str(requestCount)+") Number of vehicle fixes returned: "+str(len(fixArray)))
	return fixArray

def dumpFixes(fixes, fileName):
	strWrite = json.dumps(fixes)
	strWrite = strWrite.replace("[","").replace("]","")  #figure out a better way to do this
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
	logger.info('Starting Run  ========================================')
	apiKeys=config["apiKeys"]	
	currentKey = apiKeys[0]
	currentDay = currentDayStr() 	
	#Get the routes
	routes = fetchRoutes(config["routesURL"],currentKey)
	routeRequests = breakupRoutes(routes,config["routesPerRequest"])
	done = False
	while not done:
		for x in range (0,len(routeRequests)):
			fixes=makeRouteRequest(config["vehiclesURL"],routeRequests[x], currentKey)
			if currentDay<>currentDayStr():    # A new day is upon us
				currentDay = currentDayStr()
			dumpFixes(fixes, currentDay)
		time.sleep(60) 
		logger.info('Sleeping  ========================================')
	logger.info('Done!  ========================================')

if __name__ == "__main__":
	main(sys.argv[1:])
