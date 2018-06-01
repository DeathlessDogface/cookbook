#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys, os
import multiprocessing
from time import sleep
def son():
    #从母体环境脱离  
    os.chdir("/")  #chdir确认进程不保持任何目录于使用状态，否则不能umount一个文件系统。也可以改变到对于守护程序运行重要的文件所在目录  
    os.umask(0)    #调用umask(0)以便拥有对于写的任何东西的完全控制，因为有时不知道继承了什么样的umask。  
    os.setsid()    #setsid调用成功后，进程成为新的会话组长和新的进程组长，并与原来的登录会话和进程组脱离.
    count = 120
    while count:
        with open('/root/test.log','a+') as f:
            sleep(1)
            f.write("{}\n".format(count))
            count -= 1

def main():
    print 'start'
    p = multiprocessing.Process(target=son)
    p.start()
    sleep(1)
    print 'end'
    sys.exit()
    exit()
main()
