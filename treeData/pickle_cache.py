#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
cache object by pickle
"""
import pickle


class PickleCache(object):
    def __init__(self, cache_file_path="pickle_cache"):
        self.cache_file_path = cache_file_path
        self.cache_obj = None

    def __enter__(self):
        try:
            with open(self.cache_file_path, 'r') as io_in:
                self.cache_obj = pickle.load(io_in)
            return lambda x:setattr(self,'cache_obj',x),self.cache_obj
        except IOError:
            return lambda x:setattr(self,'cache_obj',x),None

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.cache_file_path, 'w') as io_out:
            pickle.dump(self.cache_obj, io_out)


if __name__ == '__main__':

    while True:
        with PickleCache() as cache:
            cache,old=cache
            print old
            if not old:
                old=[]
            old.append(raw_input("add:"))
            cache(old)
