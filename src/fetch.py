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
import boto
from boto.s3.key import Key

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
	#trap exception here.
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
	goodRequest = False
	tries = 0
	while (not goodRequest) and (tries <=5):
		try:
			f1=requests.get(url+apiKeys[whichKey].key+"&rt="+routes)
			goodRequest = True
			apiKeys[whichKey].counter = apiKeys[whichKey].counter+1
			logger.info("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") Requesting fixes by routes ("+routes+")"+"...")
		except:
			apiKeys[whichKey].counter = apiKeys[whichKey].counter+1
			tries = tries+1
			logger.error("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") HTTP Request error - try: "+str(tries))
			time.sleep(3)
	if (tries == 6):
		logger.error("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") HTTP Request error - Max tries: "+str(tries))
		return None

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
			try:
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
			except:
				logger.error("Type Conversion Error: "+json.dumps(vehicle))
		logger.info("(Key "+apiKeys[whichKey].key[:3]+" count: "+str(apiKeys[whichKey].counter)+") Number of vehicle fixes returned: "+str(len(fixArray)))
	return fixArray

def dumpFixes(fixes, fileName):
	#figure out a better way to do this...
	strWrite = json.dumps(fixes)
	strWrite = strWrite.replace("[","").replace("]","").replace("{","\t\t{").replace("},","},\n") 
	#Try-catch here
	newFile = os.path.isfile(config["datafilePath"]+"/"+fileName+".json") 
	with open(config["datafilePath"]+"/"+fileName+".json", "a") as dumpFile:
		if not newFile:
			dumpFile.write('{\n\t"fixes":[\n')	
    		dumpFile.write(strWrite)
		dumpFile.close()

def closeJSON(filepath):
	with open(filepath, "a") as aFile:
    		aFile.write("\n\t]\n}")
    		aFile.close()

def upload_to_s3(aws_access_key_id, aws_secret_access_key, file, bucket, key, callback=None, md5=None, reduced_redundancy=False, content_type=None):

    try:
        size = os.fstat(file.fileno()).st_size
    except:
        # Not all file objects implement fileno(),
        # so we fall back on this
        file.seek(0, os.SEEK_END)
        size = file.tell()

    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = conn.get_bucket(bucket, validate=True)
    k = Key(bucket)
    k.key = key
    if content_type:
        k.set_metadata('Content-Type', content_type)
    sent = k.set_contents_from_file(file, cb=callback, md5=md5, reduced_redundancy=reduced_redundancy, rewind=True)

    # Rewind for later use
    file.seek(0)

    if sent == size:
        return True
    return False

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
					closeJSON(config["logFile"].replace(".log","_"+currentDay+".log"))
					#file = open(config["logFile"].replace(".log","_"+currentDay+".log"), 'r+')
					#if uploadToS3(config["AWS_ACCESS_KEY"],config["AWS_ACCESS_SECRET_KEY"],file,config["bucket-name"],content_type="application/json"):
					#	logger.info("File: "+config["logFile"].replace(".log","_"+currentDay+".log")+" uploaded to S3 bucket "+config["bucket-name"])
					#else:
					#	logger.error("File: "+config["logFile"].replace(".log","_"+currentDay+".log")+" NOT uploaded to S3 bucket "+config["bucket-name"])
					logger=initLog()
					logger.info('Starting Run: '+currentDayStr()+'  ========================================')
					currentDay = currentDayStr()
					apiKeys=initAPIKeys(config["apiKeys"])  #reset the counters
					routes = fetchRoutes(config["routesURL"],apiKeys) #re-load the routes
					routeRequests = breakupRoutes(routes,config["routesPerRequest"])
				if fixes is not None:
					dumpFixes(fixes, currentDay)
				sleepSec = 57-int(time.strftime("%S"))
				logger.info('Sleeping for '+str(sleepSec)+" seconds"))
				time.sleep(57-int(time.strftime("%S")))


if __name__ == "__main__":
	main(sys.argv[1:])
