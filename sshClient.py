#!/usr/bin/python
import paramiko
from paramiko.ssh_exception import AuthenticationException

SSH_PORT = 22
SSH_USER = 'root'
SSH_PASSWORD = 'passw0rd'


class LoginError(Exception):
    def __init__(self):
        super(LoginError, self).__init__("user or password error!")


class SSHClient(object):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()

    def ssh_cmd(self, cmd):
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.host, port=SSH_PORT, username=self.username, password=self.password,
                                timeout=60)
        except AuthenticationException:
            raise LoginError()
        (_, stdout, stderr) = self.client.exec_command(cmd)
        out = stdout.read()
        err = stderr.read()
        return (out, err)

    def close(self):
        self.client.close()


if __name__ == '__main__':
    try:
        sc = SSHClient('10.100.211.62', 'root', 'root')
        print sc.ssh_cmd('ls')
    except Exception as e:
        print e
