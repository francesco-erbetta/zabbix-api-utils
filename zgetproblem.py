#!/usr/bin/env python3
#
#
import argparse
import configparser
import os
import os.path
import sys
import textwrap
import time
from datetime import datetime, timedelta, timezone
from icecream import ic
from zabbix_utils import ZabbixAPI
from zoneinfo import ZoneInfo
from termcolor import colored

def strtobool(value):
    """
    Convert a string to a boolean represented as an integer.
    - Returns 1 for "true" values (e.g., "y", "yes", "true", "on", "1").
    - Returns 0 for "false" values (e.g., "n", "no", "false", "off", "0").
    - Raises ValueError for invalid inputs.
    """
    true_values = {"y", "yes", "true", "on", "1"}
    false_values = {"n", "no", "false", "off", "0"}
    
    value_lower = value.strip().lower()
    if value_lower in true_values:
        return 1
    elif value_lower in false_values:
        return 0
    else:
        raise ValueError(f"Invalid truth value: {value}")

def timestamp_to_age(timestamp, now):
    """
    Print the delta time between the timestamp from zabbix event "clock" 
    and current time in a nice human readable format
    """
    timestamp_dt = datetime.fromtimestamp(int(timestamp))
    delta = now - timestamp_dt
    # humanize is too verbose IMHO
    # return humanize.precisedelta(now - timestamp_dt, minimum_unit="minutes")
    # return humanize.naturaltime(now - timestamp_dt)
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    # ic(delta, days, seconds, hours, minutes)
    if days > 0:
        return f"{days:02d}d {hours:02d}h {minutes:02d}m"
    else:
        return f"{hours:02d}h {minutes:02d}m"

# define config helper function
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                # DebugPrint("skip: %s" % option)
                ic(option)
        except:
            print(("exception on %s!" % option))
            dict1[option] = None
    return dict1

# conversion of timestamp
def timestr(timestamp):
    if timestamp.isdigit:
        timestring = datetime.fromtimestamp(int(timestamp), tz=ZoneInfo("Europe/Rome"))
    return timestring

# Zabbix severity mapper
def severitymap(level,interactive):
    level = int(level)
    if level < 6:
        map = ['NOT CLASSIFIED', 'INFORMATION',
               'WARNING', 'AVERAGE', 'HIGH', 'DISASTER']
        color = [None, None, 'yellow', 'yellow', 'red', 'red']
        if interactive == True:
            try:
                from termcolor import colored
                return colored(map[level], color[level])
            except:
                return map[level]
        else:
            return map[level]

# Zabbix acknowledge status mapper
def ackmap(acknowledged):
    acknowledged = int(acknowledged)
    if acknowledged < 2:
        return bool(acknowledged)

# Zabbix Alert type mapper
def alerttypemap(atype):
    atype = int(atype)
    if atype < 2:
        map = ['Message', 'Remote Command']
        return map[atype]

# Zabbix alert status mapper
def alertstatusmap(status, atype=0):
    status = int(status)
    atype = int(atype)
    if atype == 0:
        map = ['Not sent', 'Sent', 'Failed to sent']
    elif atype == 1:
        map = ['Run', 'Not run']
    return map[status]

def gen_html_table(log_entries, ts, outfile):
    mydate = ts.strftime("%a %Y-%m-%d H%H:%M")
    if(len(log_entries)>0):
        html = """
        <html>
        <head>
            <style>
                table {
                    width: 80%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 12px;
                    text-align: left;
                }
                th, td {
                    padding: 8px;
                    border: 1px solid black;
                }
                th {
                    background-color: #f2f2f2;
                }
                .INFO { background-color: #7499FF; }
                .WARNING { background-color: #FFC859; }
                .AVERAGE { background-color: #FFA059; }
                .HIGH { background-color: #E97659; }
                .DISASTER { background-color: #E45959; }
            </style>
        </head>
        <body>"""

        html += f"""
            <h2>Zabbix Open Problems Status - {mydate}</h2>
            """
        
        html += """
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>Severity</th>
                    <th>Host</th>
                    <th>Problem</th>
                    <th>Age</th>
                </tr>
        """
    
        for entry in log_entries:
            html += f"""
                <tr class="{entry['severity']}">
                    <td>{entry['etime']}</td>
                    <td>{entry['severity']}</td>
                    <td>{entry['hostname']}</td>
                    <td>{entry['trigger']}</td>
                    <td>{entry['age']}</td>
                </tr>
            """

        html += """
            </table>
            <br><hr>Sincerely, Your kind Zabbix majordomo
        </body>
        </html>
        """
    else:
        html += f"""
            <html><body><h2>Urrah! No open problems at {mydate}</h2>
            <br><hr>Sincerely, Your kind Zabbix majordomo
            </body>
            </html>
            """
    with open(outfile, "w", encoding="utf-8") as file:
        file.write(html)
    
    return

# set default vars
try:
    defconf = os.getenv("HOME") + "/.zabbix-api.conf"
except:
    defconf = None
username = ""
password = ""
api = ""
noverify = ""

# Define commandline arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Find open problems and print them in syslog or html table.', epilog="""
This program can use .ini style configuration files to retrieve the needed API connection information.
To use this type of storage, create a conf file (the default is $HOME/.zabbix-api.conf) that contains at least the [Zabbix API] section and any of the other parameters:

 [Zabbix API]
 username=johndoe
 password=verysecretpassword
 api=https://zabbix.mycompany.com/path/to/zabbix/frontend/
 no_verify=true

""")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-H', '--hostnames',
                   help='Hostname(s) to find events for', nargs='+')
group.add_argument('-G', '--hostgroups',
                   help='Hostgroup(s) to find events for', nargs='+')
group.add_argument('-T', '--triggerids',
                   help='Triggerid(s) to find events for', type=int, nargs='+')
group.add_argument('--all-hosts', 
                   help='Find events for all hosts', action='store_true')
parser.add_argument('-n', '--numeric', 
                    help='Use numeric ids instead of names, applies to -H and -G', action='store_true')
parser.add_argument('-L', '--limit', 
                    help='Limit the number of returned lines, default is 100. Set to 0 to disable.', 
                    default=100, type=int)
parser.add_argument('-A', '--include-ack', 
                    help='Include Acknowledged events, default is to exclude them.', action='store_true')
parser.add_argument('-t', '--time-period',
                    help='Timeperiod in seconds, default is one week. Set to 0 to disable.', 
                    type=int, default=604800)
parser.add_argument('-o', '--output-format',
                    choices=["syslog", "html"], default="syslog",
                    help='Output format: syslog (default) or html (simple table).')
parser.add_argument('-f', '--file-html', type=str, 
                    help="Output file for html, default _problems.html",
                    default="_problems.html")
parser.add_argument('-S', '--print-summary', help="Print a one-line summary count by severity", action='store_true')
group.add_argument('-s', '--start-time', help='Unix timestamp to search from', type=int)
parser.add_argument('-i', '--ids', help='Output only eventids', action='store_true')
parser.add_argument('-u', '--username', help='User for the Zabbix api')
parser.add_argument('-p', '--password', help='Password for the Zabbix api user')
parser.add_argument('-a', '--api', help='Zabbix API URL')
parser.add_argument('--no-verify', 
                    help='Disables certificate validation when using a secure connection', action='store_true')
parser.add_argument('-c', '--config', 
                    help='Config file location (defaults to $HOME/.zabbix-api.conf)')

args = parser.parse_args()

# load config module
Config = configparser.ConfigParser()

# if configuration argument is set, test the config file
if args.config:
    if os.path.isfile(args.config) and os.access(args.config, os.R_OK):
        Config.read(args.config)

# if not set, try default config file
else:
    if os.path.isfile(defconf) and os.access(defconf, os.R_OK):
        Config.read(defconf)

# try to load available settings from config file
try:
    username = ConfigSectionMap("Zabbix API")['username']
    password = ConfigSectionMap("Zabbix API")['password']
    api = ConfigSectionMap("Zabbix API")['api']
    noverify = bool(strtobool(ConfigSectionMap("Zabbix API")["no_verify"]))
except:
    pass

# override settings if they are provided as arguments
if args.username:
    username = args.username

if args.password:
    password = args.password

if args.api:
    api = args.api

if args.no_verify:
    noverify = args.no_verify

if args.output_format:
    output = args.output_format
else:
    output = "syslog"

# test for needed params
if not username:
    sys.exit("Error: API User not set")

if not password:
    sys.exit("Error: API Password not set")

if not api:
    sys.exit("Error: API URL is not set")

if noverify == True:
    verify = False
else:
    verify = True

# Create instance, get url, login and password from user config file
zapi = ZabbixAPI(url=api,user=username,password=password,validate_certs=verify)

# Fix current execution time
now = datetime.now()

##################################
# Start actual API logic
##################################

# Base API call
call = { 'sortfield': 'eventid',
        'sortorder': 'DESC',
        'output': 'extend',
        'selectHosts': 'extend',
        'selectRelatedObject': 'extend',
        'source': 0 }

if args.limit != 0:
    call['limit'] = args.limit

# If you add this parameter you can select ack problems (include/exclude)
# otherwise if you dont explicit it, all problems will be included.
# https://www.zabbix.com/documentation/current/en/manual/api/reference/problem/get#retrieving-trigger-problem-events
# true - return acknowledged problems only;
# false - unacknowledged only.
if not args.include_ack:
    call['acknowledged'] = False

if args.start_time:
    call['time_from'] = args.start_time

if args.time_period != 0:
    if args.start_time:
        call['time_till'] = args.start_time+args.time_period
    else:
        call['time_from'] = int(time.time())-args.time_period

if args.file_html:
    out_html_file = args.file_html
else:
    out_html_file = '_problems.html'

if args.hostgroups:
    if args.numeric:
        # We are getting numeric hostgroup ID's, let put them in a list
        # (ignore any non digit items)
        hgids = [s for s in args.hostgroups if s.isdigit()]
        for hgid in hgids:
            exists = zapi.hostgroup.exists(groupid=hgid)
            if not exists:
                sys.exit("Error: Hostgroupid "+hgid+" does not exist")
    else:
        # We are using hostgroup names, let's resolve them to ids.
        # First, get the named hostgroups via an API call
        hglookup = zapi.hostgroup.get(filter=({'name': args.hostgroups}))

        # hgids will hold the numeric hostgroup ids
        hgids = []
        for hg in range(len(hglookup)):
            # Create the list of hostgroup ids
            hgids.append(int(hglookup[hg]['groupid']))

    if len(hgids) > 0:
        call['groupids'] = hgids
    else:
        sys.exit("Error: No hostgroups found")

elif args.hostnames:
    if args.numeric:
        # We are getting numeric host ID's, let put them in a list
        # (ignore any non digit items)
        hids = [s for s in args.hostnames if s.isdigit()]
        for hid in hids:
            exists = zapi.host.exists(hostid=hid)
            if not exists:
                sys.exit("Error: Hostid "+hid+" does not exist")
    else:
        # We are using hostnames, let's resolve them to ids.
        # Get hosts via an API call
        hlookup = zapi.host.get(
            output='hostid', filter=({'host': args.hostnames}))
        hids = []
        for h in range(len(hlookup)):
            # Create the list of hostgroup ids
            hids.append(int(hlookup[h]['hostid']))

    if len(hids) > 0:
        call['hostids'] = hids
    else:
        sys.exit("Error: No hosts found")

elif args.triggerids:
    tids = [s for s in args.triggerids]
    if len(tids) > 0:
        call['objectids'] = tids
    else:
        sys.exit("Error: No triggers found")

def add_problem(p, plist):
    ''' add a problem to the list'''
    plist.append(p)

problem_list = []

# Manual dict to count totals by severity
severity_counts = {"NOT CLASSIFIED": 0, "INFORMATION": 0, "WARNING": 0, "AVERAGE": 0, "HIGH": 0, "DISASTER": 0}

problems = zapi.problem.get(**call)

if problems:
    # In this mode it will print ONLY Event ID
    if args.ids:
        for problem in problems:
            eventid = problem['eventid']
            print(eventid)
    else:
        triggerids = [problem['objectid'] for problem in problems]
        triggers = zapi.trigger.get(triggerids=triggerids, output='extend',
                                    expandDescription=1, preservekeys=1, expandComment=1, selectHosts='extend')
        for problem in problems:
            eventid = problem['eventid']
            etime = timestr(problem['clock'])
            age=timestamp_to_age(problem['clock'], now)
            hostname = "<Unknown Host>"
            trigger = "<Unknown Trigger>"
            triggerid = "<Unknown Triggerid>"
            severity = "<Unknown Severity>"
            try:
                hostname = triggers[problem['objectid']]['hosts'][0]['host']
                trigger = triggers[problem['objectid']]['description']
                severity = severitymap(triggers[problem['objectid']]['priority'], False)
                triggerid = problem['objectid']
            except:
                pass
            acked = ackmap(problem['acknowledged'])
            if acked == True:
                acknowledged = "Ack: Yes"
            else:
                acknowledged = "Ack: No"
            # Save in a dict for later output processing
            curr_p = {
                "etime": etime,
                "severity": severity,
                "hostname": hostname,
                "eventid": eventid,
                "trigger": trigger,
                "triggerid": triggerid,
                "acknowledged": acknowledged,
                "age": age
            }
            # We consider ONLY hosts that are ENABLED and not in maintenance
            curr_host = zapi.host.get(output="extend", filter={"host": hostname})
            if(len(curr_host)!=1):
                sys.exit("Getting host detail: host not found or too many hosts (should not happens!)")
            hmaintstatus=int(curr_host[0]["maintenance_status"])
            hstatus=int(curr_host[0]["status"])   
            if hmaintstatus==0 and hstatus==0:
                add_problem(curr_p, problem_list)
                severity_counts[severity] += 1            
                        
if args.print_summary:
    mydate = now.strftime("%a %Y-%m-%d H%H:%M")
    print("Zabbix Open Problems: %s || NC=%s I=%s W=%s A=%s H=%s D=%s - At: %s" % (len(problem_list), severity_counts['NOT CLASSIFIED'], 
          severity_counts['INFORMATION'], severity_counts['WARNING'], severity_counts['AVERAGE'],
          severity_counts['HIGH'], severity_counts['DISASTER'], mydate))

if output == "syslog":
    # Dump list of problems to stdout in syslog-like format (eventually colorful)
    for p in problem_list:
        print("%s [%s] %s [%s] %s (%s) [%s] [Age: %s]" % 
              (p["etime"], p["severity"], p["hostname"], p["eventid"], p["trigger"], 
               p["triggerid"], p["acknowledged"], p["age"] ))
elif output == "html":
    # Dump list of problems in a simple but effective HTML Table
    # Write output to file (default _problems.html)
    html_output = gen_html_table(problem_list, now, out_html_file)

zapi.logout()
sys.exit()
# And we're done...
