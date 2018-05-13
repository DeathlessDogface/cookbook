# -*- coding:utf-8 -*-
import pymssql
import sys
import os
import time

__author__="jiaoshijie"




def progress_bar(current, total, msg, length=50):
	progress = (current * 1.0) / total
	pro_index = int(length * progress)
	bar = "#"*pro_index+"_"*(length-pro_index)
	line = "\r{}:{}".format(bar,msg)
	sys.stdout.write(line.ljust(length+40,' '))
	sys.stdout.flush()


class Scanner(object):
	def __init__(self,host='127.0.0.1',port=1433,safe=0):
		self.host=host
		self.port=int(port)
		self.safe=safe
	def test_one(self,host,port,user,password):
		try:
			conn = pymssql.connect(host=host,port=port,user=user,password=password)
			cur=conn.cursor() 
			cur.execute('Select Name From Master..SysDatabases order By Name')
			cur.fetchall()
			cur.close()
			conn.close()
			return True
		except Exception as e:
			return False
	def test_all(self,users='users.txt',passwords='passwords.txt'):
		count = 0
		if os.path.isfile(users):
			with open(users,'r') as f:
				users = f.readlines()
		else:
			users = ['sa']
		
		if os.path.isfile(passwords):
			with open(passwords,'r') as f:
				passwords = f.readlines()
		else:
			passwords = ['admin']
		total = len(users)*len(passwords)
		for user in users:
			user = user.strip('\n')
			for password in passwords:
				password = password.strip('\n')
				count += 1
				progress_bar(count, total,msg="{}/{}".format(user,password))
				if self.test_one(self.host,self.port,user,password):
					return self.host,self.port,user,password
				time.sleep(self.safe)
		return self.host,self.port,count


def main(args):
	host_port={}
	user_password={}
	if "-h" in args:
		host_port['host']=args[args.index('-h')+1]
	if "-p" in args:
		host_port['port']=args[args.index('-p')+1]
	if "-u" in args:
		user_password['users']=args[args.index('-u')+1]
	if "-pw" in args:
		user_password['passwords']=args[args.index('-pw')+1]
	if "--safe" in args:
		try:
			host_port['safe'] = float(args[args.index('--safe')+1])
		except Exception:
			host_port['safe'] = 0.1
	else:
		host_port['safe'] = 0
	sc = Scanner(**host_port)
	ret = sc.test_all(**user_password)
	print
	if len(ret) == 4:
		print "login to {}:{} successfully by {}/{}".format(*ret)
	else:
		print "login to {}:{} failed after try {} times.".format(*ret)


if __name__ == "__main__":
	args = sys.argv
	main(args)