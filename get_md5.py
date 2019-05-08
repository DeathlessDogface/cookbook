#! /usr/bin/python
import hashlib
import sys
import os
#file_name = "sds_bs_type1/ThinkCloud-SDS-1.0.12.1181-daily_20190503_sds_bs_type1.tar.gz"


def main():
    args = sys.argv
    if args[0]=='python':
        args=args[1:]
    if 'get_MD5' in args[0]:
        args=args[1:]
    file_name=args[0]
    if not os.path.isfile(file_name):
        raise ValueError("{} is not a file!".format(file_name))
    
    
    MD5 = hashlib.md5()
    with open(file_name, 'r') as f:
        for line in f.readlines():
            MD5.update(line)
    
    return  MD5.hexdigest()
print main()
