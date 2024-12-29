#!/usr/bin/env python3
#
# Retrieve the interface(s) for host
#
# zabbix_utils is needed, see https://github.com/zabbix/python-zabbix-utils
import argparse
import configparser
import os
import os.path
import sys
import distutils.util
from zabbix_utils import ZabbixAPI

# define config helper function

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print(("exception on %s!" % option))
            dict1[option] = None
    return dict1


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
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Retrieve all the interface(s) for host', epilog="""
This program can use .ini style configuration files to retrieve the needed API connection information.
To use this type of storage, create a conf file (the default is $HOME/.zabbix-api.conf) that contains at least the [Zabbix API] section and any of the other parameters:

 [Zabbix API]
 username=johndoe
 password=verysecretpassword
 api=https://zabbix.mycompany.com/path/to/zabbix/frontend/
 no_verify=true

Usage example:
zhgraphfinder.py -e HOSTNAME

""")
parser.add_argument(
    'hostname', help='Hostname to find the interfaces for')
parser.add_argument('-u', '--username', help='User for the Zabbix api')
parser.add_argument('-p', '--password',
                    help='Password for the Zabbix api user')
parser.add_argument('-a', '--api', help='Zabbix API URL')
parser.add_argument(
    '--no-verify', help='Disables certificate validation when using a secure connection', action='store_true')
parser.add_argument(
    '-c', '--config', help='Config file location (defaults to $HOME/.zabbix-api.conf)')
parser.add_argument(
    '-n', '--numeric', help='Return numeric interface id instead of interface name', action='store_true')
parser.add_argument('-e', '--extended',
                    help='Return both interface id and name separated with a ":"', action='store_true')
args = parser.parse_args()

# load config module
Config = configparser.ConfigParser()
Config

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
    noverify = bool(distutils.util.strtobool(
        ConfigSectionMap("Zabbix API")["no_verify"]))
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

interface_type = {
    "1": "Agent",
    "2": "SNMP",
    "3": "IPMI",
    "4": "JMX"
}

zapi = ZabbixAPI(url=api,user=username,password=password,validate_certs=verify)

##################################
# Start actual API logic
##################################

# set the hostname we are looking for
host_name = args.hostname

# Find specified host from API
hosts = zapi.host.get(output="extend", filter={"host": host_name})

if hosts:
    # Find interfaces
    interfaces = zapi.hostinterface.get(output="extend", hostids=hosts[0]["hostid"])

    if interfaces:
        if args.extended:
            # print ids and names
            for interface in interfaces:
                print((format(interface["interfaceid"])+":"+format(interface["ip"])))
        else:
            if args.numeric:
                # print id
                for interface in interfaces:
                    print((format(interface["interfaceid"])))
            else:
                # print names and dns if available
                for interface in interfaces:
                    if interface["dns"]:
                        print((format(interface["ip"])+" (dns: "+format(interface["dns"]+")")))
                    else:
                        print((format(interface["ip"])))
    else:
        sys.exit("Error: (should NOT happen!) No interfaces defined for " + host_name)
else:
    sys.exit("Error: Could not find host " + host_name)

zapi.logout()
# And we're done...
