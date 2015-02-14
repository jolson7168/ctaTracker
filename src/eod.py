import glob
import os
import json
import csv
import logging
import sys
import getopt
import time
import boto
import zipfile
from boto.s3.key import Key
import datetime

config = {}

def currentDayStr():
	return time.strftime("%Y%m%d")

def getYesterdayStr():
	t = datetime.date.fromordinal(datetime.date.today().toordinal()-1)
	return t.strftime("%Y%m%d")

def initLog():
	logger = logging.getLogger(config["logname"])
	hdlr = logging.FileHandler(config["logFile"])
	formatter = logging.Formatter(config["logFormat"],config["logTimeFormat"])
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr) 
	logger.setLevel(logging.INFO)
	return logger

def logProgress(sent, totalSize):
    logger = logging.getLogger(config["logname"])
    perDone = round(((sent/float(totalSize))*100),2)
    logger.info(str(round(((sent/float(totalSize))*100),2))+"% complete") 
	
def uploadToS3(aws_access_key_id, aws_secret_access_key, file, bucket, key, callback=None, md5=None, reduced_redundancy=False, content_type=None):

    logger = logging.getLogger(config["logname"])
    logger.info('Starting upload.')

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

    file.seek(0)
    k.set_canned_acl('public-read')

    if sent == size:
        return True
    return False


def main(argv):
 	try:
      		opts, args = getopt.getopt(argv,"hc:",["configfile="])
	except getopt.GetoptError:
		print ('eod.py -c <configfile>')
      		sys.exit(2)
	for opt, arg in opts:
      		if opt == '-h':
         		print ('eod.py -c <configfile>')
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
	logger.info('Starting EOD for: '+getYesterdayStr()+'  ===========================')
	logger.info('Validating JSON...')
	if not os.path.isfile(config["dataDir"]+"/"+getYesterdayStr()+".json"):
		logger.error("Missing yesterday's data file: "+config["dataDir"]+"/"+getYesterdayStr()+".json")
	else:
		with open (config["dataDir"]+"/"+getYesterdayStr()+".json", "r") as inFile:
			data=inFile.read()
			goodJSON = True
			try:
				json_object = json.loads(data)
				logger.info('Valid JSON!')
				json_object = None
			except Exception, e:
				logger.error('Invalid JSON: '+str(e))
				goodJSON = False
		if goodJSON:
			logger.info('Zipping file: '+getYesterdayStr()+'.json')
			with zipfile.ZipFile(config["dataDir"]+"/"+getYesterdayStr()+".zip", 'w') as myzip:
				try:
			    		myzip.write(config["dataDir"]+"/"+getYesterdayStr()+".json",compress_type=zipfile.ZIP_DEFLATED)
					logger.info("File: "+config["dataDir"]+"/"+getYesterdayStr()+".zip zipped!")
				finally:
			    		myzip.close()
			if os.path.isfile(config["dataDir"]+"/"+getYesterdayStr()+".zip"):
				zfile = open(config["dataDir"]+"/"+getYesterdayStr()+".zip", 'r+')
				key = getYesterdayStr()+".zip"
				if uploadToS3(config["AWS_ACCESS_KEY"],config["AWS_ACCESS_SECRET_KEY"],zfile,config["bucketname"],key,callback=logProgress,content_type="application/zip"):
					logger.info("File: "+getYesterdayStr()+".zip"+" uploaded to S3 bucket "+config["bucketname"])
					try:		
						os.remove(config["dataDir"]+"/"+getYesterdayStr()+".json")
						logger.info("File: "+getYesterdayStr()+".json"+" deleted.")
					except:
						logger.error("File: "+getYesterdayStr()+".json"+" NOT deleted!")
				else:
					logger.error("File: "+getYesterdayStr()+".zip"+" NOT uploaded to S3 bucket "+config["bucketname"])
			else:
				logger.error("Zip file missing??")
	logger.info('Done! '+getYesterdayStr()+'  =======================================')


if __name__ == "__main__":
	main(sys.argv[1:])
