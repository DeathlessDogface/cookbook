#! /usr/bin/python
# -*- coding:utf-8 -*-
import hashlib
import os
import sys


def get_diff(src_dir, other, arm):
    diff_file_list = []
    for cur_dir, sub_dirs, sub_files in os.walk(src_dir):
        for cur_file in sub_files:
            src_file_path = os.path.join(cur_dir, cur_file)
            other_file_path = os.path.join(other, src_file_path.split(os.path.sep, 1)[1])
            diff = False
            if os.path.isfile(other_file_path):
                src_md5 = hashlib.md5()
                with open(src_file_path, 'r') as src_f:
                    for src_line in src_f.readlines():
                        src_md5.update(src_line)
                src_md5 = src_md5.hexdigest()

                other_md5 = hashlib.md5()
                with open(other_file_path, 'r') as other_f:
                    for other_line in other_f.readlines():
                        other_md5.update(other_line)
                other_md5 = other_md5.hexdigest()

                if src_md5 != other_md5:
                    diff = True
                else:
                    print "same file:{}".format(src_file_path)
            else:
                diff = True
            if diff:
                arm_file_path = os.path.join(arm, src_file_path.split(os.path.sep, 1)[1])
                arm_file_dir = os.path.split(arm_file_path)[0]
                if not os.path.isdir(arm_file_dir):
                    os.popen("mkdir -p {}".format(arm_file_dir))
                os.popen("cp -f {} {}".format(src_file_path,arm_file_path))
                diff_file_list.append(src_file_path)
    return diff_file_list


def main():
    args = sys.argv
    if "python" in args[0]:
        args = args[1:]
    if "get_diff_file_from_dir" in args[0]:
        args = args[1:]
    print get_diff(args[0], args[1], args[2])


if __name__ == '__main__':
    main()

