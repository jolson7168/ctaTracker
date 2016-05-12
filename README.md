# ctaTracker
Python code that interacts with the Chicago Transit Agency's bus and train tracker API. 

The purpose of this project is to sit in a continuous loop and hit the public CTA API every X minutes to collect fix information on CTA assets.

Just want the historical CTA fix data? Check out the [ctaData project](https://github.com/jolson7168/ctaData).

## Installation
External packages needed:
```
[xmltodict](https://github.com/martinblech/xmltodict)	(sudo pip install xmltodict)
[boto](https://github.com/boto/boto)		(sudo pip install boto)
```

### Config Files
There are two config files in the ./config directory. Drop the '_template' part of the filename, and change the settings in the file to your preference.


### API key
You will need an official CTA API key. You can get it [here](http://www.transitchicago.com/developers/traintrackerapply.aspx). Once acquired, put it in ./config/ctaTracker.conf

## Operation
You can launch the app using ./scripts/fetch_template. Logging goes into ./logs and data into ./data, by default. 

./scripts/monitor.sh is a support script used to monitor the task. Use this in conjunction with cron. Be careful of the relative paths included in this file. 

### End of Day
./src/eod.py and ./scripts/eod_template_.sh are designed to run once a day after midnight. This task archives the previous days data, and uploads it to S3. Rename eod_template.sh to eod.sh and put an entry to execute it in cron. Be careful of the relative paths included in ./config/eod.config . 
