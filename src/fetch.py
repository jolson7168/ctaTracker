from __future__ import print_function
import glob
import os
import json
import csv
import logging
from collections import defaultdict
import sys
import getopt
from time import gmtime, strftime
import decimal
import requests

config = {}
logger = logging.getLogger("GlobalLog")
apiKeys=[]

def initLog():
	logger = logging.getLogger(config["logname"])
	hdlr = logging.FileHandler(config["logFile"])
	formatter = logging.Formatter(config["logFormat"],config["logTimeFormat"])
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr) 
	logger.setLevel(logging.INFO)
	return logger

def fetchRoutes(url, apiKey):
	r1=requests.get(url+apiKey)
	return r1.text

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
	routes = fetchRoutes(config["routesURL"],currentKey)
	print (routes)
	logger.info('Done!  ========================================')

if __name__ == "__main__":
	main(sys.argv[1:])
