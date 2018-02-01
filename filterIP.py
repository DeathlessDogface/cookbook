#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
从大文本文件中搜索IP地址
@author：jiaoshijie
@date：2016.10.3
"""
from multiprocessing import Pool, Queue
from os import walk, path
from random import randint, choice
from re import compile
from string import ascii_letters, digits
from sys import stdout
from time import time, sleep

FILENAME = 'hugetext.txt'
RE_IP = compile(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}")


def __generate_huge_text(filename=FILENAME):
    """
    生成大文本文件，用于测试
    """
    with open(filename, 'a') as f:
        count = 1024
        size = 1024 * 1024
        while count > 0:
            random_ip = "%d.%d.%d.%d" % (randint(0, 300), randint(0, 255), randint(0, 255), randint(0, 300))
            f.write(random_ip)
            while size > 0:
                f.write(choice(ascii_letters + digits))
                size -= 1
            count -= 1
            size = 1024 * 1024


def __analyse_ip(s_ip):
    """
    IP解析函数用于ip地址的二次过滤，配合map()使用
    """
    try:
        fst, sec, thi, fou = [int(x) for x in s_ip.split('.')]
    except:
        return
    if 0 <= sec < 255 and 0 <= thi < 255:
        if fst >= 0 and fou >= 0:
            if fst >= 255:
                fst = int(fst % 100)
            if fou >= 255:
                fou = int(fou / 10)
            return "%d.%d.%d.%d" % (fst, sec, thi, fou)
    return


#
# read方法，适用于1G以下文件
#
def filter_ip_read(filename):
    with open(filename, 'r') as f:
        content = f.read()
    ips = RE_IP.findall(content)
    del content
    return set([x for x in map(__analyse_ip, ips) if x])


#
# 文件对象迭代法，试用于1G以上大文件
#
def filter_ip_iter(filename):
    with open(filename, 'r') as f:
        ips = set()
        for line in f:
            ips = ips | set(RE_IP.findall(line))
    return set([x for x in map(__analyse_ip, ips) if x])


#
# 进程池法，用于多文件批量处理
#
def process(filepath, size):
    if size < 1024 * 1024 * 1024:
        ips = filter_ip_read(filepath)
    else:
        ips = filter_ip_iter(filepath)

    return filepath, ips


class FilterIP(object):
    def __init__(self, show=False):
        self.show = show
        self.taskpool = Pool(processes=4)
        self.queue = Queue()
        self.tasks = []
        self.result = {}
        self.total = 0
        self.current = 0

    @property
    def IPs(self):
        return reduce(lambda a, b: a | b, self.result.values())

    def start(self, dirpath):
        for parent, dirs, files in walk(dirpath):
            for f in files:
                filepath = path.join(parent, f)
                if filepath not in self.tasks:
                    print "add %s" % filepath
                    size = path.getsize(filepath)
                    self.total += size
                    task = self.taskpool.apply_async(process, args=(filepath, size))
                    self.tasks.append([filepath, task, size])
        print 'add over'
        while self.tasks:
            rst = self.check_task()
            if rst:
                if rst[1]:
                    self.result.update({rst[0]: rst[1]})
            if self.show:
                self.status()
            sleep(0.1)
        self.taskpool.close()
        self.taskpool.join()
        self.taskpool.terminate()

    def check_task(self):
        for i, task in enumerate(self.tasks):
            if task[1].ready():
                self.current += task[2]
                del self.tasks[i]
                if task[1].successful():
                    return task[1].get()
                else:
                    return
        return

    def status(self):
        line = "\r>>> {} / {} : {:.2f}% ".format(self.current, self.total, self.current * 100.0 / self.total)
        stdout.write(line)
        stdout.flush()
        if not self.total > self.current:
            print "完成！"


def main(*args):
    start = time()
    fi = FilterIP(show=True)
    fi.start(args[0])
    print fi.IPs
    stop = time()
    t = int(stop - start)
    m, s = divmod(t, 60)
    h, m = divmod(m, 60)
    print "time:%d:%d:%d" % (h, m, s)


if __name__ == '__main__':
    main("/root/")
