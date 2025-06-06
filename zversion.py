#!/usr/bin/env python3

import argparse
import configparser
import os
import os.path
import sys
import cmd
import traceback
import distutils.util
import textwrap
from datetime import datetime
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
defconf = os.getenv("HOME") + "/.zabbix-api.conf"
username = ""
password = ""
api = ""
noverify = ""

# Define commandline arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Interactive Zabbix API commandline client.', epilog="""
This program can use .ini style configuration files to retrieve the needed API connection information.
To use this type of storage, create a conf file (the default is $HOME/.zabbix-api.conf) that contains at least the [Zabbix API] section and any of the other parameters:

 [Zabbix API]
 username=johndoe
 password=verysecretpassword
 api=https://zabbix.mycompany.com/path/to/zabbix/frontend/
 no_verify=true

""")
parser.add_argument('-u', '--username', help='User for the Zabbix api')
parser.add_argument('-p', '--password',
                    help='Password for the Zabbix api user')
parser.add_argument('-a', '--api', help='Zabbix API URL')
parser.add_argument(
    '--no-verify', help='Disables certificate validation when using a secure connection', action='store_true')
parser.add_argument(
    '-c', '--config', help='Config file location (defaults to $HOME/.zbx.conf)')
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
    print("Error: API User not set")
    exit()

if not password:
    print("Error: API Password not set")
    exit()

if not api:
    print("Error: API URL is not set")
    exit()

if noverify == True:
    verify = False
else:
    verify = True

# Create instance, get url, login and password from user config file
zapi = ZabbixAPI(url=api,user=username,password=password,validate_certs=verify)

# We need the API version to know if valuemap importing is supported
try:
    version = zapi.api_version()
    print(version)
except:
    error = "Error: Could not retrieve Zabbix version"
    PrintError(error)

zapi.logout()
# And we're done...
