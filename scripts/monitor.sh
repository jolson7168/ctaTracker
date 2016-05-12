#!/bin/sh
pid0=`ps -ef | grep -v grep |grep fetch|awk '{print $2}'`
if [ $pid0 ]
then
  echo `date` Fetcher running...>>/home/ubuntu/git/ctaTracker/logs/restart.out
  ext='.json'
  path='/home/ubuntu/git/ctaTracker/logs'
  datapath='/home/ubuntu/git/ctaTracker/data'
  checkfile=$path'/fs.txt'
  now=$datapath'/'`date +'%Y%m%d'`$ext
  current=`ls -la $now|cut -f5 -d' '`
  old=`cat $checkfile`
  if [ $current -eq $old ]; then
     echo `date` Fetcher frozen. Killing and restarting >>/home/ubuntu/git/ctaTracker/logs/restart.out
     kill -9 $pid0
     /home/ubuntu/git/ctaTracker/scripts/fetch.sh
  else
    echo $current>/home/ubuntu/git/ctaTracker/logs/fs.txt
    echo `date` Fetcher writing >>/home/ubuntu/git/ctaTracker/logs/restart.out
  fi
else
  echo `date` Fetcher not running...>>/home/ubuntu/git/ctaTracker/logs/restart.out
  /home/ubuntu/git/ctaTracker/scripts/fetch.sh
  pid1=`ps -ef | grep -v grep |grep fetch|awk '{print $2}'`
  if [ $pid1 ]
  then
     echo `date` Fetcher restarted...>>/home/ubuntu/git/ctaTracker/logs/restart.out
  else
     echo `date` Fetcher still not restarted...>>/home/ubuntu/git/ctaTracker/logs/restart.out
  fi
fi
