#!/bin/bash
#
# Gen graphs via zapi utils.
# Luca Maranzano <liuk@linux.it> - 2024
#
# This program should be rewritten in python for better performance.

# Bash safety
set -e
set -u
set -o pipefail
#set -x

usage() {
    echo "Generate zabbix graphs via zapi utils."
    echo "Usage: $0 [ -s starttime ] [ -t endtime ] [ -o repdata ]" 
    echo "Default values: starttime=now-7d, endtime=now, outdir=repdata"
    echo ""
    echo "Example: $0 -s now-10d -t now --outdir myoutput"
    exit 1
}

# Imposta le opzioni e specifica quali accettano un argomento (indicato con ':')
OPTIONS="s:t:o:"
LONGOPTS="starttime:,endtime:,outdir:"

# Analizza gli argomenti usando getopt
PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
if [[ $? -ne 0 ]]; then usage; fi

# Riorganizza gli argomenti secondo l'output di getopt
eval set -- "$PARSED"

# Variabili per memorizzare i valori degli argomenti
starttime="now-7d"
endtime="now"
outdir="repdata"

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
        -o|--outdir)
            outdir="$2"
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
REPDATA=$BASEDIR/$outdir

echo "Graph timeframe: from $starttime to $endtime"
echo "repdata=$REPDATA"

# Graph sizes
GRW=900
GRH=200

cd $BASEDIR || usage
if [ "$(/bin/ls -A $REPDATA)" ]
then
  echo "Cleaning $REPDATA"
  /bin/rm -fr $REPDATA/* 2>/dev/null
else
  echo "$REPDATA is empty or is missing (will be created)"
fi

# Create additional info file for a given host, they will be placed
# in the top section of every page
# Infofile generation is common for every host, at least if you are using 
# Windows and Linux templates, beware YMMV
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

# NOTE: Use "zhgraphfinder.py -e YOURHOST" to find your suitable patterns 
# to get the graphs that you need

# Template Windows
let hcounter=1
total=$(../zthostfinder.py -m "Windows by Zabbix agent" | wc -l)
IFS=$'\n'; for h in $(../zthostfinder.py -m "Windows by Zabbix agent" | sort ); do
  let counter=1
  printf "Generating data for host: %s (%s/%s)\n" $h $hcounter $total
  # Create data dir for this host
  if [ ! -d "$REPDATA/$h" ]; then mkdir -p "$REPDATA/$h"; fi
  generate_infofile "$h"
  
  printf -v current_graph "%s/%s/g%03d.png" $REPDATA $h $counter
  printf "\tGraph %s\n" $current_graph
  gid=$(../zhgraphfinder.py -e $h | grep "Windows: CPU utilization" | cut -d':' -f1)
  ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $gid
  counter=$((counter+1))
  
  printf -v current_graph "%s/%s/g%03d.png" $REPDATA $h $counter
  printf "\tGraph %s\n" $current_graph
  gid=$(../zhgraphfinder.py -e $h | grep "Windows: Memory utilization" | cut -d':' -f1)
  ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $gid
  counter=$((counter+1))
  
  # Loop for all disks/file systems
  for fsgrph in $(../zhgraphfinder.py -e $h | grep "Disk space usage (BVREP)" | cut -d':' -f1 | sort -n) ; do 
    printf -v current_graph "%s/%s/g%03d.png" $REPDATA $h $counter
    printf "\tGraph %s\n" $current_graph
    ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $fsgrph
    counter=$((counter+1))
  done
  hcounter=$((hcounter+1))
done

# Template Linux
let hcounter=1
total=$(../zthostfinder.py -m "Linux by Zabbix agent" | wc -l)
for h in $(../zthostfinder.py -m "Linux by Zabbix agent" | sort ); do
  let counter=1
  printf "Generating data for host: %s (%s/%s)\n" $h $hcounter $total
  # Create data dir for this host
  if [ ! -d "$REPDATA/$h" ]; then mkdir -p "$REPDATA/$h"; fi
  generate_infofile "$h"
  
  printf -v current_graph "%s/%s/g%03d.png" $REPDATA $h $counter
  printf "\tGraph %s\n" $current_graph
  gid=$(../zhgraphfinder.py -e $h | grep "Linux: CPU utilization" | cut -d':' -f1)
  ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $gid
  counter=$((counter+1))
  
  printf -v current_graph "%s/%s/g%03d.png" $REPDATA $h $counter
  printf "\tGraph %s\n" $current_graph
  gid=$(../zhgraphfinder.py -e $h | grep "Linux: Memory usage" | cut -d':' -f1)
  ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $gid
  counter=$((counter+1))
  
  # Loop for all disks/file systems
  for fsgrph in $(../zhgraphfinder.py -e $h | grep "Disk space usage (BVREP)" | cut -d':' -f1 | sort -n) ; do 
    printf -v current_graph "%s/%s/g%03d.png" $REPDATA $h $counter
    printf "\tGraph %s\n" $current_graph
    ../zgetgraph.py -s "$starttime" -t "$endtime" -W $GRW -H $GRH -f $current_graph $fsgrph
    counter=$((counter+1))
  done
  hcounter=$((hcounter+1))
done

unset IFS

tstamp=$(date +%Y-%m-%d-H%H%M)
./r1.py "Infrastructure report by Zabbix" "ACME Corporation" "Last 7 days from $tstamp"

#Generazione testo mail
if [[ $2 == now-1M ]] ; then
	sdate=$(date --date="-1 month" +"%d/%m/%Y")
	edate=$(date +"%d/%m/%Y")
	echo "Buongiorno,
in allegato il report mensile di performances dell'infrastruttura per il periodo $sdate - $edate. 
 
Cordiali saluti
Bvtech
 
Questa è una mail automatica, si prega di non rispondere, per ogni esigenza [placeholder]" > ./mailtext.txt
elif [[ $2 == now-1w ]] ; then
	sdate=$(date --date="-1 week" +"%d/%m/%Y")
	edate=$(date +"%d/%m/%Y")
	echo "Buongiorno,
in allegato il report settimanale di performances dell'infrastruttura per il periodo $sdate - $edate. 
 
Cordiali saluti
Bvtech
 
Questa è una mail automatica, si prega di non rispondere, per ogni esigenza [placeholder]" > ./mailtext.txt
fi
exit 0

