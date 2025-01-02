# Zabbix Hosts Report generator POC

Using the zapi utilities we can try to build a Report Generator for a selection 
of hosts monitored by your Zabbix instance.

In this directory you'll find a sort of POC about what I mean.

## High level logic
For a given host on Zabbix, the graphs you may be interested in fundamentally depend on the Template associated with the host itself, for example:

- "Windows by Zabbix agent"
- "Linux by Zabbix agent"

So we'll start from some common templates to get the list of the associated hosts:

```
$ zthostfinder.py "Windows by Zabbix agent"
WINHOST01
WINHOST02
WINHOST03
...
```

Then let's dig into the available graphs for a given host:

```
$ zhgraphfinder.py -e WINHOST02
3066:Windows: CPU jumps
3067:Windows: CPU usage
3068:Windows: CPU utilization
3069:Windows: Memory utilization
3070:Windows: Swap usage
3071:OS DISK(C:): Disk space usage
3072:Software Archive(E:): Disk space usage
3073:Interface Intel(R) 82574L Gigabit Network Connection(VLAN100): Network traffic
3074:0 C:: Disk average queue length
3075:1 E:: Disk average queue length
3076:0 C:: Disk average waiting time
3077:1 E:: Disk average waiting time
3078:0 C:: Disk read/write rates
3079:1 E:: Disk read/write rates
3080:0 C:: Disk utilization and queue
3081:1 E:: Disk utilization and queue
```

Interesting graphs to include in the report can be the following:
```
3068:Windows: CPU utilization
3069:Windows: Memory utilization
3071:OS DISK(C:): Disk space usage
3072:Software Archive(E:): Disk space usage
```

With the "Disk space usage" there is a problem (at least for me): by default it's a Pie graph which will not show
the time trend. So my solution is the following:
1. Go to the Template definition -> Discover Rules
2. Click on the "Graph prototypes" where the current Pie graph get defined
3. Clone the current Pie graph changing the following:
    - The name of the graph should contain a UNIQUE pattern added to the default name (eg. MYREP)
    - The Graph type will be "Normal"
    - The Size will be 900x200
    - tune all the options that can be useful for you
4. Wait for the discovery process to generate the graph (60 mintues at max)

Now if you search again your graph the output will appear like this:

```
$ zhgraphfinder.py -e WINHOST02 | grep "Disk space usage"
3071:OS DISK(C:): Disk space usage
3072:Software Archive(E:): Disk space usage
4093:OS DISK(C:): Disk space usage (MYREP)
4094:Software Archive(E:): Disk space usage (MYREP)
```

Let's generate the graph in PNG format:

```
$ zgetgraph.py -s now-7d -t now -f mygraph.png 4093
```

Et voilà, we have the graph that we need ready to be included in the Report!

With some more zapi magic invocation we can get some info about the hosts, like OS, Groups, Templates, etc. etc.

## A bit of python with a bit of bash and the POC is here
In this folder you'll find 2 programs that will do the work:
1. gg.sh: Graph Generator bash script
2. r1.py: PDF generator in python using FPDF2 module

### Graph generator
This bash script will cycle through all the ENABLED hosts associated to the Windows and Linux Templates and will dump for every host the graphs about CPU, Memory and every discovered Disk/Filesystem, producing a tree like this starting from REPDATA=./repdata:
```
repdata/
├── MYHOST01
│   ├── g001.png
│   ├── g002.png
│   ├── g003.png
│   └── info.txt
├── MYHOST02
│   ├── g001.png
│   ├── g002.png
│   ├── g003.png
│   ├── g004.png
│   ├── g005.png
│   └── info.txt
.....
```

### PDF Generator
This Python script will cycle in the repdata folder and will generate a PDF with these simple rules:
1. A Cover page with a Title, the Customer name and the period (last 7 days for example)
2. For every Host found it will produce an Header with some infos from inventory and host items, and 3 Graphs per page. Host with several file systems will generate lot of pages :-)
3. Outpuf file will be report.pdf

Please do note that PDF can be huge with several hosts (about 12MB for 200 Windows Hosts with few disk each, for example).

## Final considerations
This POC was an excellent exercise to study the Zabbix API and to produce a simple but already effective PDF report extremely quickly, thanks to the ease of use of Python.

The scripts my need some tweaking in order to be used in you environment, if you need to include Hosts from other templates you'll need to find the exact pattern name of the graphs you're interested in and modify the logic in gg.sh accordingly.

((Enjoy))





