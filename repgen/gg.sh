#!/bin/bash
#
#Gen graphs
#set -x
BASEDIR=/home/liuk/Workspace/mygithub/zabbix-api-utils/repgen
REPDATA=$BASEDIR/repdata

# Graph sizes
GRW=900
GRH=200

cd $BASEDIR

for h in $(../zthostfinder.py "Windows by Zabbix agent"); do
  let counter=1
  echo Generating graphs for host: $h
  if [ ! -d "$REPDATA/$h" ]; then mkdir "$REPDATA/$h"; fi
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


