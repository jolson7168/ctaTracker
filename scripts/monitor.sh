#!/bin/sh
pid0=`ps -ef | grep -v grep |grep fetch|awk '{print $2}'`
if [ $pid0 ]
then
  echo `date` Fetcher running...>>../logs/restart.out
  ext='.json'
  path='../logs'
  datapath='../data'
  checkfile=$path'/fs.txt'
  now=$datapath'/'`date +'%Y%m%d'`$ext
  current=`ls -la $now|cut -f5 -d' '`
  old=`cat $checkfile`
  if [ $current -eq $old ]; then
     echo `date` Fetcher frozen. Killing and restarting >>../logs/restart.out
     kill -9 $pid0
     ../scripts/fetch.sh
  else
    echo $current>../logs/fs.txt
    echo `date` Fetcher writing >>../logs/restart.out
  fi
else
  echo `date` Fetcher not running...>>../logs/restart.out
  ../scripts/fetch.sh
  pid1=`ps -ef | grep -v grep |grep fetch|awk '{print $2}'`
  if [ $pid1 ]
  then
     echo `date` Fetcher restarted...>>../logs/restart.out
  else
     echo `date` Fetcher still not restarted...>>../logs/restart.out
  fi
fi
