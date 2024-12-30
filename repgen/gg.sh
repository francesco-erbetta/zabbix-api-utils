#!/bin/bash
#
# Gen graphs via zapi utils.
# Luca Maranzano <liuk@linux.it> - 2024
#
# This program should be rewritten in python for better performance.
# set -x

usage() {
    echo "Generate zabbix graphs via zapi utils."
    echo "Usage: $0 [ -s starttime ] [ -t endtime ]"
    echo "Default values: starttime=now-7d, endtime=now"
    echo ""
    echo "Example: $0 -s now-10d -t now"
    exit 1
}

# Imposta le opzioni e specifica quali accettano un argomento (indicato con ':')
OPTIONS="s:t:"
LONGOPTS="starttime:,endtime:"

# Analizza gli argomenti usando getopt
PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
if [[ $? -ne 0 ]]; then usage; fi

# Riorganizza gli argomenti secondo l'output di getopt
eval set -- "$PARSED"

# Variabili per memorizzare i valori degli argomenti
starttime="now-7d"
endtime="now"

# Ciclo per analizzare gli argomenti
while true; do
    case "$1" in
        -s|--starttime)
            starttime="$2"
            shift 2
            ;;
        -t|--endtime)
            endtime="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Opzione non riconosciuta: $1" >&2
            usage
            exit 1
            ;;
    esac
done

BASEDIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPDATA=$BASEDIR/repdata

echo "Graph timeframe: from $starttime to $endtime"

# Graph sizes
GRW=900
GRH=200

cd $BASEDIR

# Create additional info file for a given host, they will be placed
# in the top section of every page
# Infofile generation is common for every kind of host
# Use HTML tags for text formatting
generate_infofile() {
  h=$1
  info_file="$REPDATA/$h/info.txt"
  printf "\tInfo file %s\n" "$info_file"
  # system.uname is valid for both windows and linux
  sysuname_key=$(../zhitemfinder.py -n -k system.uname $h)
  sysdescr=$(../zgethistory.py --count 1 -t 86400 $sysuname_key)
  printf "System description: <b>%s</b><br>\n" "$sysdescr" >$info_file
  # Get zabbix interfaces
  interfaces=$(../zhinterface.py $h | paste -s -d, )
  printf "Zabbix interface(s): <b>%s</b><br>\n" "$interfaces" >>$info_file
  # List of templates
  linked_templates=$(../zhtmplfinder.py $h | paste -s -d, )
  printf "Linked Templates: <b>%s</b><br>\n" "$linked_templates" >>$info_file
  # List of group(s)
  group_list=$(../zhgroupfinder.py $h | paste -s -d, )
  printf "Host groups: <b>%s</b><br>\n" "$group_list" >>$info_file
}

# Template Windows
for h in $(../zthostfinder.py "Windows by Zabbix agent" | sort ); do
  let counter=1
  echo Generating data for host: $h
  # Create data dir for this host
  if [ ! -d "$REPDATA/$h" ]; then mkdir -p "$REPDATA/$h"; fi
  generate_infofile "$h"
  
  current_graph="$REPDATA/$h/g$counter.png"; printf "\tGraph %s\n" $current_graph
  gid=$(../zhgraphfinder.py -e $h | grep "Windows: CPU utilization" | cut -d':' -f1)
  ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $gid
  counter=$((counter+1))
  
  current_graph="$REPDATA/$h/g$counter.png"; printf "\tGraph %s\n" $current_graph
  gid=$(../zhgraphfinder.py -e $h | grep "Windows: Memory utilization" | cut -d':' -f1)
  ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $gid
  counter=$((counter+1))
  
  # Loop for all disks/file systems
  for fsgrph in $(../zhgraphfinder.py -e $h | grep "Disk space usage (BVREP)" | cut -d':' -f1 | sort -n) ; do 
    current_graph="$REPDATA/$h/g$counter.png"; printf "\tGraph %s\n" $current_graph
    ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $fsgrph
    counter=$((counter+1))
  done
done

./r1.py "Zabbix performances report" "ACME Corporation" "Last 7 days from today 30-12-2024"

okular report.pdf &

exit 0

