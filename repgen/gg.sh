#!/bin/bash
#
# Gen graphs via zapi utils.
# This program should be rewritten in python for better performance.
#set -x
BASEDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPDATA=$BASEDIR/repdata

# Graph sizes
GRW=900
GRH=200

cd $BASEDIR

# Template Windows
for h in $(../zthostfinder.py "Windows by Zabbix agent"); do
  let counter=1
  # Create data dir for this host
  if [ ! -d "$REPDATA/$h" ]; then mkdir "$REPDATA/$h"; fi
  # Create additional info file for this host
  info_file="$REPDATA/$h/info.txt"
  printf "\tInfo file: %s\n" "$info_file"
  # List of templates
  linked_templates=$(../zhtmplfinder.py $h | paste -s -d, )
  printf "Linked Templates: %s\n" "$linked_templates" >$info_file

  echo Generating graphs for host: $h
  current_graph="$REPDATA/$h/g$counter.png"; printf "\tGraph %s\n" $current_graph
  gid=$(../zhgraphfinder.py -e $h | grep "Windows: CPU utilization" | cut -d':' -f1)
  ../zgetgraph.py -s now-7d -t now -W $GRW -H $GRH -f $current_graph $gid
  counter=$((counter+1))
  
  current_graph="$REPDATA/$h/g$counter.png"; printf "\tGraph %s\n" $current_graph
  gid=$(../zhgraphfinder.py -e $h | grep "Windows: Memory utilization" | cut -d':' -f1)
  ../zgetgraph.py -s now-7d -t now -W $GRW -H $GRH -f $current_graph $gid
  counter=$((counter+1))
  
  # Loop for all disks/file systems
  for fsgrph in $(../zhgraphfinder.py -e $h | grep "Disk space usage (BVREP)" | cut -d':' -f1 | sort -n) ; do 
    current_graph="$REPDATA/$h/g$counter.png"; printf "\tGraph %s\n" $current_graph
    ../zgetgraph.py -s now-7d -t now -W $GRW -H $GRH -f $current_graph $fsgrph
    counter=$((counter+1))
  done
done

./r1.py

okular report.pdf &

exit 0

