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
		elif opt in ("-v", "--validate"):
			jsonFile=arg
			mode = "validate"
			try:
				with open(jsonFile): pass
			except IOError:
				print ('json file: '+jsonFile+' not found')
				sys.exit(2)
		elif opt in ("-c", "--close"):
			jsonFile=arg
			mode = "close"
			try:
				with open(jsonFile): pass
			except IOError:
				print ('json file: '+jsonFile+' not found')
				sys.exit(2)


		if (mode == "validate"):
			with open (jsonFile, "r") as inFile:
			    data=inFile.read().replace('\n', '')
			try:
				json_object = json.loads(data)
				print("Valid JSON!")
				sys.exit()
			except Exception, e:
				print("Invalid JSON: "+str(e))
				sys.exit(2)
		elif (mode == "close"):
			with open(jsonFile, "a") as aFile:
				aFile.write("\n\t]\n}")
				aFile.close()




if __name__ == "__main__":
	main(sys.argv[1:])
