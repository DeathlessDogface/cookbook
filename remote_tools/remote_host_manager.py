#! /usr/bin/python
# -*- coding:utf-8 -*-
import ConfigParser
import commands
import copy
import os
import sys
import threading
import warnings

import paramiko


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
        self.sftp = None

    def ssh_cmd(self, cmd):
        print "run cmd: {}   ".format(cmd),
        (_, stdout, stderr) = self.client.exec_command(cmd, bufsize=1024 * 1024)
        out = stdout.read()
        err = stderr.read()
        print "OVER"
        if out:
            print out
        if err:
            print("************ERROR**\n{}".format(err))
        return out, err

    def cephmgmt(self, cmd, *args):
        cmds = ['source', '/root/localrc', '&&', 'cephmgmtclient', cmd]
        if args:
            cmds.extend(args)
        self.ssh_cmd(" ".join(cmds))

    def close(self):
        self.client.close()

    def __enter__(self):
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.host, port=22, username=self.username, password=self.password,
                                timeout=1000)
            self.sftp = paramiko.SFTPClient.from_transport(self.client.get_transport())

        except paramiko.ssh_exception.AuthenticationException:
            raise LoginError()
        self.old_io = (sys.stdout, sys.stderr)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sftp:
            self.sftp.close()
        self.close()
        sys.stdout, sys.stderr = self.old_io


def thread_factory(fun):
    class MyThread(threading.Thread):
        def __init__(self, threadID, name, args=()):
            threading.Thread.__init__(self)
            self.threadID = threadID
            self.name = name
            self.run_args = args

        def run(self):
            fun(*self.run_args)

    return MyThread


#
# ================================================================
#
class BaseManager(object):
    def __init__(self, conf):
        self.CONF = conf

    def reset_file(self, sc, lines, file_path):
        print("=" * 10 + file_path)
        with sc.sftp.open(file_path, "w+") as fw:
            lines.append("")
            fw.write("\n".join(lines))
        print("\n".join(lines))
        print("=" * 10)

    def edit_remote_conf(self, sc, file_path, model=" ", **kwargs):
        if not kwargs:
            return
        lines = []
        with sc.sftp.open(file_path, 'r+') as fr:
            for line in fr.readlines():
                if line:
                    if any(map(lambda k: any([line.startswith(k),
                                              line.startswith("#{}".format(k)),
                                              line.startswith("# {}".format(k))]),
                               kwargs.keys())):
                        continue
                    else:
                        lines.append(line)
        for k, v in kwargs.items():
            lines.append("{}{}{}\n".format(k, model, v))
        with sc.sftp.open(file_path, "w+") as fw:
            fw.writelines(lines)


#
# ================================================================
#
class MaintenanceManager(BaseManager):
    def check_health(self):
        pass

    def check_config(self):
        pass

#
# ================================================================
#
class EnvironmentManager(BaseManager):
    def clear_TCS(self, sc):
        print("\n>>> clear TCS ...")
        print("... clear HA")
        sc.ssh_cmd("sh /usr/bin/ha_clear.sh")
        sc.ssh_cmd("rm /etc/my.cnf.d/galera.cnf -rf")
        print("... clear ceph")
        sc.ssh_cmd("sh /etc/ceph/scripts/clear.sh")
        sc.ssh_cmd("sh /etc/ceph/scripts/disk_fs_mgmt.sh -O deletepartition")
        sc.ssh_cmd("sh /etc/ceph/scripts/clear.sh")
        sc.ssh_cmd("sh /etc/ceph/scripts/disk_fs_mgmt.sh -O deletepartition")
        print("... remove mariadb")
        sc.ssh_cmd("systemctl stop mariadb")
        sc.ssh_cmd("systemctl disable mariadb")
        sc.ssh_cmd("yum remove $(rpm -qa | grep mariadb) -y")
        sc.ssh_cmd("rm /var/lib/mysql/* -rf")
        sc.ssh_cmd("rm /usr/lib/ocf/* -rf")

    def set_hostname(self, sc, node):
        print("\n>>>  set hostname:{}".format(self.CONF.get(node, 'name')))
        sc.ssh_cmd("hostnamectl set-hostname {}".format(self.CONF.get(node, 'name')))

    def init_disk(self, sc):
        print("\n>>> init disk on {}".format(sc.host))
        _disks = []
        info, err = sc.ssh_cmd("lsblk -rp --output NAME,TYPE,MOUNTPOINT")
        info = info.split("\n")
        title = info.pop(0)
        while info:
            cache_disk = {'disk': None, 'part': [], 'raid': [], 'is_os': False}
            while info:
                _line = info.pop(0)
                if not _line:
                    continue
                line = _line.split()
                if cache_disk['disk'] and line[1] == 'disk':
                    info.insert(0, _line)
                    break

                if len(line) > 2 and "/boot" in line[2]:
                    cache_disk['is_os'] = True
                if line[1] == "disk":
                    cache_disk['disk'] = line[0]
                elif line[1] == 'part':
                    if len(line) > 2:
                        cache_disk['part'].append((line[0], line[2]))
                elif "raid" in line[1]:
                    cache_disk['raid'].append(line[0])
            print("... cache_disk")
            if cache_disk['is_os']:
                continue
            _disks.append(copy.deepcopy(cache_disk))

        for disk in _disks:
            if disk['part']:
                for disk_part, dir_path in disk['part']:
                    sc.ssh_cmd("umount %s -f" % dir_path)
            if disk['raid']:
                sc.ssh_cmd(
                    "mdadm {raid} --fail {parts}  --remove {parts}".format(
                        raid=disk['disk'], parts=' '.join(disk['part'])))
                sc.ssh_cmd(
                    "mdadm --grow --raid-devices=1 --force {}".format(disk['disk']))
            if disk['disk']:
                sc.ssh_cmd("dd if=/dev/zero  of={} bs=1M count=1".format(disk['disk']))

    def set_timezone(self, sc, node):
        print("\n>>> set time zone for {}".format(node))
        sc.ssh_cmd("timedatectl set-timezone Asia/Shanghai")

    def forbid_selinux(self, sc):
        print("\n>>> forbid selinux")
        out, err = sc.ssh_cmd("cat /etc/sysconfig/selinux")
        selinux = out.split('\n')
        lines = []
        for l in selinux:
            if not l or l.startswith('#'):
                continue
            if l.startswith("SELINUX=") or l.startswith("SELINUX "):
                lines.append("SELINUX=disabled")
            else:
                lines.append(l)
        self.reset_file(sc, lines, "/etc/sysconfig/selinux")
        sc.ssh_cmd("setenforce 0")

    def forbid_firewall(self, sc):
        print("\n>>> forbid firewall")
        sc.ssh_cmd("systemctl stop firewalld")
        sc.ssh_cmd("systemctl disable firewalld")
        sc.ssh_cmd("systemctl stop iptables")
        sc.ssh_cmd("systemctl disable iptables")
        sc.ssh_cmd("systemctl stop ip6tables")
        sc.ssh_cmd("systemctl disable ip6tables")

    def forbid_networkManager(self, sc, fb=True):
        if fb:
            print("\n>>> forbid NetworkManager")
            sc.ssh_cmd("systemctl stop NetworkManager")
            sc.ssh_cmd("systemctl disable NetworkManager")
        else:
            print("\n>>> restart NetworkManager")
            sc.ssh_cmd("systemctl enable NetworkManager")
            sc.ssh_cmd("systemctl restart NetworkManager")

    def set_network(self, sc, node, eths=None):
        print("\n>>> set network")
        if not eths:
            eths = self.CONF.get('env', 'net').split(',')
        for eth in eths:
            if not self.CONF.has_option(node, eth):
                continue
            addr = self.CONF.get(node, eth)
            if ":" in addr:
                config = ['DEVICE={}'.format(eth),
                          'NAME={}'.format(eth),
                          'IPV6ADDR={}'.format(addr)]
                for opt, value in self.CONF.items('ifcfg-v6'):
                    config.append("{}={}".format(opt.upper(), value))
                self.reset_file(sc, config, "/etc/sysconfig/network-scripts/ifcfg-{}".format(eth))
            else:
                config = ['IPADDR={}'.format(addr),
                          'NAME={}'.format(eth), ]
                for opt, value in self.CONF.items(eth):
                    config.append("{}={}".format(opt.upper(), value))
                self.reset_file(sc, config, "/etc/sysconfig/network-scripts/ifcfg-{}".format(eth))
            sc.ssh_cmd("ifdown {} && ifup {}".format(eth, eth))
        self.reset_file(sc, ['nameserver 10.96.1.18', 'nameserver 10.96.1.19', 'nameserver 8.8.8.8'],
                        '/etc/resolv.conf')

    def create_ssh_key(self, sc):
        print("\n>>> create ssh key")
        sc.ssh_cmd('rm -f /root/.ssh/id_rsa*')
        sc.ssh_cmd('ssh-keygen -q -t rsa -N "" -f /root/.ssh/id_rsa')
        key, err = sc.ssh_cmd('cat /root/.ssh/id_rsa.pub')
        if err:
            raise RuntimeError("create ssh key failed:{}".format(err))
        sc.ssh_cmd('rm -f /root/.ssh/id_rsa.pub')
        sc.ssh_cmd('sed -i \'/StrictHostKeyChecking/d\' /etc/ssh/ssh_config')
        sc.ssh_cmd('echo "StrictHostKeyChecking no" | tee -a /etc/ssh/ssh_config')
        return key

    def set_sshkey(self, sc, ssh_key, node):
        print("\n>>> set ssh key")
        for _node, key in ssh_key.items():
            print("add ssh key of {} in {}".format(_node, node))
            sc.ssh_cmd('mkdir -p /root/.ssh')
            sc.ssh_cmd('''echo {} | tee -a /root/.ssh/authorized_keys'''.format(key.replace("\n", "")))
            sc.ssh_cmd('chmod 600 /root/.ssh/authorized_keys')

    def check_network(self, sc, main_node):
        print("\n>>> check network")
        public_domain = "www.baidu.com"
        print("{}<-->{}".format(main_node, public_domain))
        sc.ssh_cmd("ping {} -c 3".format(public_domain))
        for node in self.CONF.get('env', 'node').split(','):
            for eth in self.CONF.get('env', 'net').split(','):
                if not self.CONF.has_option(node, eth):
                    continue
                addr = self.CONF.get(node, eth)
                print("{}<-->{}:{}".format(main_node, node, eth))
                if "." in addr:
                    sc.ssh_cmd("ping {} -c 3".format(addr))
                else:
                    sc.ssh_cmd("ping -6 {} -c 3".format(addr))

    def install_sendmail(self, sc):
        print("\n>>> insatll sendmail")
        sc.ssh_cmd("yum install sendmail -y")

    def forbid_ssh_dns(self, sc):
        print("\n>>> forbid ssh DNS")
        self.edit_remote_conf(sc, "/etc/ssh/sshd_config", UseDNS="no")
        sc.ssh_cmd("systemctl restart sshd")


#
# ================================================================
#
class DeployTCSManager(BaseManager):
    def send_package(self, sc, node):
        print("\n>>> send package to {}".format(node))
        dir, name = os.path.split(self.CONF.get('ceph', 'package'))
        sc.ssh_cmd("mkdir -p /tmp/upgrade_ceph/")
        print sc.sftp.put(self.CONF.get('ceph', 'package'), "/tmp/upgrade_ceph/{}".format(name))
        sc.ssh_cmd("tar -xf /tmp/upgrade_ceph/{} -C /tmp/ --overwrite".format(name))

    def clear_package(self, sc, node):
        print("\n>>> clear packages")
        sc.ssh_cmd("rm /tmp/upgrade_ceph/* -rf")
        sc.ssh_cmd("rm /tmp/deployment -rf")

    def set_hosts(self, sc, node, ha_flag, net_version):
        print("\n>>> edit /etc/hosts")
        if ha_flag:
            api_inte = self.CONF.get('vip', self.CONF.get(node, 'ha'))
        else:
            api_inte = self.CONF.get(node, self.CONF.get(node, 'manager'))
        hosts = [
            "127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4 {}".format(
                self.CONF.get(node, 'name')),
            "::1         localhost localhost.localdomain localhost6 localhost6.localdomain6 {}".format(
                self.CONF.get(node, 'name')),
            "{}   api.inte.lenovo.com".format(api_inte),
        ]
        if ha_flag:
            hosts.append("{}   controller".format(api_inte))
            for _host in self.CONF.get('ceph', 'controller').split(','):
                hosts.append("{}   {}".format(self.CONF.get(_host, self.CONF.get(_host, 'manager')),
                                              self.CONF.get(_host, 'name')))

        self.reset_file(sc, hosts, "/etc/hosts")

    def install_TCS(self, net_version):
        print("\n>>> install TCS")
        threads = []
        for node in self.CONF.get('ceph', 'controller').split(','):
            threads.append(self._install_tcs(node, node, (self, node, net_version)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("over install <<<")

    @thread_factory
    def _install_tcs(self, node, net_version):
        print("> install TCS on {}".format(node))
        if '6' in net_version:
            net_flag = "-ipv6"
        else:
            net_flag = ""
        with SSHClient(
                host=self.CONF.get(node, "deployip"),
                username=self.CONF.get(node, 'user'),
                password=self.CONF.get(node, 'password')) as sc:
            print(" !!! it is a long time !!! (about 20min)")
            sc.ssh_cmd("/tmp/deployment/standalone-setup.sh install -s {} > /tmp/install_tcs.log".format(net_flag))
        print("finished on {} <".format(node))

    def set_HA(self, sc, node):
        # set ha install config
        print("\n>>> set HA config")
        install_config = [
            'HA_flag=YES',
            'ManageNetwork=\"{}\"'.format(self.CONF.get('vip', self.CONF.get(node, 'manager'))),
            # 'PublicNetwork=\"{}\"'.format(self.CONF.get('vip', self.CONF.get(node, 'public'))),
            'this_node={}'.format(self.CONF.get(node, self.CONF.get(node, 'manager')))]
        other = 2
        for _node in self.CONF.get('ceph', 'controller').split(','):
            if _node == node:
                continue
            install_config.append(
                'other_node{}={}'.format(other, self.CONF.get(_node, self.CONF.get(_node, 'manager'))))
            other += 1
        _ip = 1
        for eth, vip in self.CONF.items('vip'):
            if not self.CONF.has_option(node, eth):
                continue
            install_config.append('VIP{}=\"{}\"'.format(_ip, vip))
            if ":" in vip:
                install_config.append('CIDR{}=\"{}\"'.format(_ip, 64))
            else:
                install_config.append('CIDR{}=\"{}\"'.format(_ip, 24))
            _ip += 1
        file = "/tmp/deployment/ha_config/install_config"
        self.reset_file(sc, install_config, file)

    def deploy_HA(self, sc):
        print("\n>>> deploy HA")
        warnings.warn(" !!! it if a long time !!! (about 60min)")
        raise RuntimeError('what are you doing is dangerous!')
        sc.ssh_cmd("cd /tmp/deployment/ha_config/ && ./all_in_one.sh > /tmp/deploy_ha.log")

    def upload_license(self, sc):
        print("\n>>> upload license")
        dir, name = os.path.split(self.CONF.get('ceph', 'license'))
        sc.ssh_cmd("rm /tmp/{} -rf".format(name))
        print sc.sftp.put(self.CONF.get('ceph', 'license'), "/tmp/{}".format(name))
        sc.cephmgmt("update-license",
                    "-l", "/tmp/{}".format(name))

    def create_cluster(self, sc):
        print("\n>>> create cluster")
        sc.cephmgmt("create-cluster",
                    '--name', self.CONF.get('ceph', 'cluster'),
                    "--addr","beijing")

    def add_host(self, sc):
        print("\n>>> add host")
        for node in self.CONF.get('ceph', 'agent').split(','):
            sc.cephmgmt("create-server",
                        "--id", self.CONF.get('ceph', 'cluster_id'),
                        "--name", self.CONF.get(node, 'name'),
                        "--managerip", self.CONF.get(node, self.CONF.get(node, 'manager')),
                        "--publicip", self.CONF.get(node, self.CONF.get(node, 'public')),
                        "--clusterip", self.CONF.get(node, self.CONF.get(node, 'storage')),
                        "--server_user", self.CONF.get(node, 'user'),
                        "--server_pass", self.CONF.get(node, 'password'),
                        "--rack_id", self.CONF.get('ceph', 'rack_id'),
                        "--ipmi_ip", self.CONF.get(node, 'ipmi'))

    def deploy_cluster(self, sc):
        print("\n>>> deploy cluster")
        sc.cephmgmt("deploy-cluster", self.CONF.get('ceph', 'cluster_id'))

    def upgrade_tcs(self, sc, name):
        print("\n>>> upgrade TCS")
        sc.cephmgmt("upgrade-tcs-soft",
                    "-c", self.CONF.get('ceph', 'cluster_id'),
                    "-n", name)

    def upgrade_ceph(self, sc):
        print("\n>>> upgrade ceph soft")
        sc.cephmgmt("upgrade-cluster",
                    self.CONF.get('ceph', 'cluster_id'))


#
# =================================================================
#
class DeployManager(object):
    def __init__(self, work_space, cfg_file):
        self.CONF = ConfigParser.SafeConfigParser()
        self.CONF.read(cfg_file)
        self.ssh_key = {}
        if not os.path.isdir(work_space):
            commands.getstatusoutput("mkdir -p {}".format(work_space))
        self.env_manager = EnvironmentManager(self.CONF)
        self.tcs_manager = DeployTCSManager(self.CONF)

    def set_environment(self):
        for node in self.CONF.get('env', 'node').split(','):
            print("\n>>> connect to {}...".format(node))
            with SSHClient(
                    host=self.CONF.get(node, "deployip"),
                    username=self.CONF.get(node, 'user'),
                    password=self.CONF.get(node, 'password')) as sc:
                print("\n>>> set environment on {}".format(node))
                # self.env_manager.clear_TCS(sc)
                self.env_manager.set_hostname(sc, node)
                # self.env_manager.init_disk(sc)
                self.env_manager.forbid_ssh_dns(sc)
                self.env_manager.set_network(sc, node)
                self.env_manager.set_timezone(sc, node)
                self.env_manager.forbid_selinux(sc)
                self.env_manager.forbid_firewall(sc)
                self.env_manager.forbid_networkManager(sc) # warning ! maybe connect public net failed
                # self.env_manager.install_sendmail(sc)
                self.ssh_key[node] = self.env_manager.create_ssh_key(sc)

        for node in self.CONF.get('env', 'node').split(','):
            with SSHClient(
                    host=self.CONF.get(node, "deployip"),
                    username=self.CONF.get(node, 'user'),
                    password=self.CONF.get(node, 'password')) as sc:
                print(">>> config environment on {}".format(node))
                self.env_manager.set_sshkey(sc, self.ssh_key, node)

        main_node = self.CONF.get('env', 'node').split(',')[0]
        with SSHClient(
                host=self.CONF.get(main_node, "deployip"),
                username=self.CONF.get(main_node, 'user'),
                password=self.CONF.get(main_node, 'password')) as sc:
            self.env_manager.check_network(sc, main_node)
            return

    def deploy_TCS(self, flag, net_version):
        controllers = self.CONF.get('ceph', 'controller').split(',')
        main_controller = controllers[0]
        for controller in controllers:
            with SSHClient(
                    host=self.CONF.get(controller, "deployip"),
                    username=self.CONF.get(controller, 'user'),
                    password=self.CONF.get(controller, 'password')) as sc:
                # self.tcs_manager.clear_package(sc, controller)
                # self.tcs_manager.send_package(sc, controller)
                # self.tcs_manager.set_HA(sc,controller)
                # self.tcs_manager.set_hosts(sc, controller, flag, net_version)
                break
        # return
        # self.install_TCS(net_version)
        print("operation on controller:{}".format(main_controller))
        with SSHClient(
                host=self.CONF.get(main_controller, "deployip"),
                username=self.CONF.get(main_controller, 'user'),
                password=self.CONF.get(main_controller, 'password')) as sc:
            # self.tcs_manager.deploy_HA(sc) # warning ! it is a long time
            # self.tcs_manager.upload_license(sc)
            # self.tcs_manager.create_cluster(sc)
            self.tcs_manager.add_host(sc)
            # self.tcs_manager.deploy_cluster(sc)
            # self.tcs_manager.upgrade_tcs(sc,"deployment-standalone-daily_20180704_1036.tar.gz")
            # self.tcs_manager.upgrade_ceph(sc)
            # return

    def main(self, **kwargs):
        self.set_environment()
        # self.deploy_TCS(flag=True, net_version='ipv6')
        # self.deploy_TCS(flag=True, net_version='ipv4')


#
# ====================================================================================
#
if __name__ == "__main__":
    args = sys.argv[1:]
    _args = [x for x in args if not x.startswith("-")]
    kwargs = dict([(x, args[args.index(x) + 1]) for x in args if x.startswith('-')])

    work_space = kwargs.get("--work_space", "/home/jsj/")
    if "-f" in kwargs:
        cfg_file = kwargs["-f"]
    elif _args:
        cfg_file = _args[0]
    else:
        raise RuntimeError("Appoint a config file!")
    DeployManager(work_space, cfg_file).main(args=_args)
