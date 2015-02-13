import json
import glob
import os
import sys
import getopt

def main(argv):
	try:
		opts, args = getopt.getopt(argv,"hv:",["jsonfile="])
	except getopt.GetoptError:
		print ('validate.py -v <jsonfile>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
	 		print ('validate.py -v <jsonfile>')
	 		sys.exit()
		elif opt in ("-v", "--jsonfile"):
			jsonFile=arg
			try:
				with open(jsonFile): pass
			except IOError:
				print ('json file: '+jsonFile+' not found')
				sys.exit(2)

	with open (jsonFile, "r") as inFile:
	    data=inFile.read().replace('\n', '')
	try:
		json_object = json.loads(data)
		print("Valid JSON!")
		sys.exit()
	except Exception, e:
		print("Invalid JSON: "+str(e))
		sys.exit(2)

if __name__ == "__main__":
	main(sys.argv[1:])
