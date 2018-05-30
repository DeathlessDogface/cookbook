import socket
import fcntl
import struct
import psutil
def get_ip_address(ifname):
    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fileno=skt.fileno()
    SIOCGIFADDR=0x8915
    pack = struct.pack('256s', ifname[:15])
    info=fcntl.ioctl(fileno,SIOCGIFADDR,pack)
    ip = socket.inet_ntoa(info[20:24])
    return ip
def local_addrs():
    ifnames = psutil.net_io_counters(pernic=True).keys()
    ips = {}
    for ifname in ifnames:
        ip = get_ip_address(ifname)
        if len(ip)>=7:
            ips.update({ifname:ip})
    return ips
print local_addrs()
