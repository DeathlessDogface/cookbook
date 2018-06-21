#! /usr/bin/python
# -*- coding:utf-8 -*-
import ConfigParser
import commands

try:
    import paramiko
except ImportError:
    cmd = [
        'rpm',
        '-ivh',
        'python-paramiko-1.15.1-1.el7.noarch.rpm',
        'python-ecdsa-0.11-3.el7.centos.noarch.rpm',
        'python-crypto-2.6.1-1.el7.centos.x86_64.rpm',
        'python-six-1.9.0-2.el7.noarch.rpm'
    ]
    status, output = commands.getstatusoutput(" ".join(cmd))
    if status:
        raise ImportError("no model named paramiko")
    import paramiko


class DeployManager(object):
    def __init__(self, cfg_file="auto_deploy_ha.conf"):
        self.CONF = ConfigParser.SafeConfigParser()
        self.CONF.read(cfg_file)

    def set_hosts(self, node, sc):

        hosts = [
            "127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4 {}".format(
                self.CONF.get(node, 'name')),
            "::1         localhost localhost.localdomain localhost6 localhost6.localdomain6 {}".format(
                self.CONF.get(node, 'name')),
            "{}   api.inte.lenovo.com".format(self.CONF.get('vip', self.CONF.get('env', 'vip_manager'))),
            "{}   controller".format(self.CONF.get('vip', self.CONF.get('env', 'vip_manager'))),
        ]
        self.reset_file(sc, hosts, "/etc/hosts")

    def set_selinux(self, sc):
        out, err = sc.ssh_cmd("cat /etc/sysconfig/selinux")
        if err:
            raise RuntimeError("get selinux config failed:{}:{}".format(err, out))
        selinux = out.split('\n')
        lines = []
        for l in selinux:
            if not l:
                continue
            if l.startswith("SELINUX=") or l.startswith("SELINUX "):
                lines.append("SELINUX=disabled")
            else:
                lines.append(l)
        self.reset_file(sc, lines, "/etc/sysconfig/selinux")

    def set_network(self, sc, node):
        for eth in self.CONF.get('env', 'net').split(','):
            config = ['IPADDR={}'.format(self.CONF.get(node, eth))]
            for opt, value in self.CONF.items(eth):
                config.append("{}={}".format(opt.upper(), value))
            self.reset_file(sc, config, "/etc/sysconfig/network-scripts/ifcfg-{}".format(eth))

    def set_sshkey(self, ssh_key):
        for node in self.CONF.get('env', 'node').split(','):
            with SSHClient(
                    host=self.CONF.get(node, self.CONF.get('env', 'manager')),
                    username=self.CONF.get(node, 'user'),
                    password=self.CONF.get(node, 'password')) as sc:
                for this_node, key in ssh_key.items():
                    print("add public key of {} at {}".format(this_node, node))
                    print sc.ssh_cmd('mkdir -p /root/.ssh')
                    print sc.ssh_cmd('''echo {} | tee -a /root/.ssh/authorized_keys'''.format(key.replace("\n", "")))
                    print sc.ssh_cmd('chmod 600 /root/.ssh/authorized_keys')

    def reset_file(self, sc, lines, file):
        sc.ssh_cmd('echo > {}'.format(file))
        for l in lines:
            print sc.ssh_cmd('echo "{}" >> {}'.format(l, file))

    def create_ssh_key(self, sc):
        # create key
        print sc.ssh_cmd('rm -f /root/.ssh/id_rsa*')
        print sc.ssh_cmd('ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa')
        key, err = sc.ssh_cmd('cat /root/.ssh/id_rsa.pub')
        if err:
            raise RuntimeError("create ssh key failed:{}".format(err))
        print sc.ssh_cmd('rm -f /root/.ssh/id_rsa.pub')
        print sc.ssh_cmd('sed -i \'/StrictHostKeyChecking/d\' /etc/ssh/ssh_config')
        print sc.ssh_cmd('echo "StrictHostKeyChecking no" | tee -a /etc/ssh/ssh_config')
        return key

    def send_package(self):
        for node in self.CONF.get('env', 'node').split(','):
            print("to {}".format(node))
            print commands.getstatusoutput("scp /home/{} {}:{}".format(
                self.CONF.get('env', 'package'),
                self.CONF.get(node, self.CONF.get('env', 'manager')),
                "/tmp/"))
            print commands.getstatusoutput("ssh {} tar -xf /tmp/{} -C /tmp/ --overwrite".format(
                self.CONF.get(node, self.CONF.get('env', 'manager')), self.CONF.get('env', 'package')))

    def install_TCS(self):
        for node in self.CONF.get('env', 'node').split(','):
            print("install {}".format(node))

            status, output = commands.getstatusoutput("ssh {} /tmp/deployment/standalone-setup.sh install -s".format(
                self.CONF.get(node, self.CONF.get('env', 'manager'))))
            if status:
                raise RuntimeError("install TCS on {} failed:{}".format(node, output))

    def set_HA(self):
        for node in self.CONF.get('env', 'node').split(','):
            print(">>> prepare {}".format(node))
            with SSHClient(
                    host=self.CONF.get(node, self.CONF.get('env', 'manager')),
                    username=self.CONF.get(node, 'user'),
                    password=self.CONF.get(node, 'password')) as sc:
                # set ha install config
                install_config = [
                    'HA_flag=YES',
                    'ManageNetwork=\"{}\"'.format(self.CONF.get('vip', self.CONF.get('env', 'vip_manager'))),
                    'PublicNetwork=\"{}\"'.format(self.CONF.get('vip', self.CONF.get('env', 'vip_manager'))),
                    'this_node={}'.format(self.CONF.get(node, self.CONF.get('env', 'manager')))]
                other = 2
                for _node in self.CONF.get('env', 'node').split(','):
                    if _node == node:
                        continue
                    install_config.append(
                        'other_node{}={}'.format(other, self.CONF.get(_node, self.CONF.get('env', 'manager'))))
                    other += 1
                _ip = 1
                for eth, vip in self.CONF.items('vip'):
                    install_config.append('VIP{}=\"{}\"'.format(_ip, vip))
                    install_config.append('CIDR{}=\"{}\"'.format(_ip, 24))
                    _ip += 1
                file = "/tmp/deployment/ha_config/install_config"
                self.reset_file(sc, install_config, file)

    def install_HA(self):
        # deploy HA
        status, output = commands.getstatusoutput("cd /tmp/deployment/ha_config/ && ./all_in_one.sh")
        if status:
            raise RuntimeError("deploy HA failed:{}".format(output))
    
    def main(self,task_list=None):
        
        ssh_key = {}
        for node in self.CONF.get('env', 'node').split(','):
            print(">>> prepare {}".format(node))
            with SSHClient(
                    host=self.CONF.get(node, self.CONF.get('env', 'manager')),
                    username=self.CONF.get(node, 'user'),
                    password=self.CONF.get(node, 'password')) as sc:
                # set hostname
                print("set hostname:{}".format(self.CONF.get(node, 'name')))
                print sc.ssh_cmd("hostnamectl set-hostname {}".format(self.CONF.get(node, 'name')))

                # edit hosts
                print("edit hosts")
                print self.set_hosts(node, sc)

                # set selinux
                print("set selinux")
                print self.set_selinux(sc)

                # forbid firewall
                print("forbid firewall")
                print sc.ssh_cmd("systemctl stop firewalld")
                print sc.ssh_cmd("systemctl disable firewalld")
                print sc.ssh_cmd("systemctl stop iptables")
                print sc.ssh_cmd("systemctl disable iptables")
                print sc.ssh_cmd("systemctl stop ip6tables")
                print sc.ssh_cmd("systemctl disable ip6tables")

                # set network
                print("set network")
                self.set_network(sc, node)
                print sc.ssh_cmd("systemctl restart network")

                # create ssh key
                print("create ssh key")
                key = self.create_ssh_key(sc)
                ssh_key[node] = key

                # clear mariadb
                print("clear mariadb")
                print sc.ssh_cmd("systemctl stop mariadb")
                print sc.ssh_cmd("systemctl disable mariadb")
                print sc.ssh_cmd("yum remove $(rpm -qa | grep mariadb) -y")[1]
                print sc.ssh_cmd("rm /var/lib/mysql/* -rf")

        # add ssh key
        print("add ssh key")
        self.set_sshkey(ssh_key)

        # send package
        print("send package")
        self.send_package()

        # config HA
        print("conf HA")
        self.set_HA()

        # # install TCS
        # print("install TCS")
        # self.install_TCS()
        #
        # # deploy ha
        # print("deploy HA")
        # status, output = commands.getstatusoutput("cd /tmp/deployment/ha_config/ && ./all_in_one.sh")
        # if status:
        #     raise RuntimeError("deploy HA failed:{}".format(output))

        # upload license

        # create cluster

        # add host

        # deploy cluster


#
# =========================    tools   ===========================
#
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
        (_, stdout, stderr) = self.client.exec_command(cmd)
        out = stdout.read()
        err = stderr.read()
        return (out, err)

    def close(self):
        self.client.close()

    def __enter__(self):
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.host, port=22, username=self.username, password=self.password,
                                timeout=60)
        except paramiko.ssh_exception.AuthenticationException:
            raise LoginError()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    DeployManager().main()
