import telnetlib

username="root"
password="2188,al"
TIMEOUT=3
ip = '192.168.1.1'


tn = telnetlib.Telnet(ip, timeout=TIMEOUT)
try:
    un = tn.read_until("username:", TIMEOUT)
    if un.find("username:") < 0:
        print un
        tn.close()
except:
    print 'No Received From Remote.'
    tn.close()

tn.write(username + "\n")
pw = tn.read_until("password:", TIMEOUT)

tn.write(password + "\n")

try:
    lg = tn.read_very_eager()

    print lg
    tn.close()
except:
    print 'No default login.'
    tn.close()


tn.write("wlctl show\n")
wlctl = tn.read_until("cmd:SUCC", TIMEOUT)
tn.write("lan show info\n")
laninfo = tn.read_until("cmd:SUCC", TIMEOUT)
tn.close()
wlctl = dict([x.split("=",1) for x in wlctl.split() if len(x.split("=",1))==2])
laninfo = dict([x.split("=",1) for x in laninfo.split() if len(x.split("=",1))==2])

try:
    SSID = wlctl['SSID']
except:
    SSID = ''
try:
    Key = wlctl['Key']
except:
    Key = ''
try:
    X_TPLINK_MACAddress = laninfo['X_TPLINK_MACAddress']
except:
    X_TPLINK_MACAddress = ''
try:
    IPRouters = laninfo['IPRouters']
except:
    IPRouters = ''
try:
    IPInterfaceIPAddress = laninfo['IPInterfaceIPAddress']
except:
    IPInterfaceIPAddress = ''

print((ip,
                     SSID,
                     Key,
                     X_TPLINK_MACAddress,
                     IPRouters,
                     IPInterfaceIPAddress))

