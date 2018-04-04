#!/usr/bin/python
# -*- coding:utf-8 -*-
# date : 2018-04-04
# author : SunDay



class test(object):
    f='hahah'
    def __init__(self):
        self.a = 1
        self.b = 3
        self._c = "asdf"
        self.__d__ = [2,43,7,3]
        self.e = {"a":3,"b":8}
    def run(self):
        return
    def __str__(self,show_private=False):
        import json
        need_show={}
        for k in dir(self):
            if k.startswith("_") and not show_private:
                continue
            v = getattr(self,k)
            if callable(v):
                continue
            need_show[k]=v
        lines=json.dumps(need_show, sort_keys=True, indent=4)
        return lines

if __name__ == "__main__":
    t=test()
    print t.__str__(show_private=True)
