#!/usr/bin/python
# -*- coding:utf-8 -*-

import ConfigParser
import re

__all__ = ["CONF"]
CONF_PATH = "/etc/storagemgmt_cron/storagemgmt_cron.conf"

_instance = {}


def Singleton(cls):
    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton


class Option(object):
    def __init__(self, section, conf):
        if not isinstance(conf, ConfigParser.SafeConfigParser):
            return
        if not conf.has_section(section):
            return
        for k in conf.options(section):
            self.__setattr__(k.replace(" ","_"), self.data_type(conf.get(section, k)))

    def __getattr__(self, item):
        raise ConfigError("the option:{} if not defined!".format(item))

    @classmethod
    def data_type(cls, data):
        data_type_map = {
            int: re.compile(r"^\s*\-?[0-9]+\s*$"),
            float: re.compile(r"^\s*\-?[0-9]+\.[0-9]*\s*$"),
            cls.boolean: re.compile(r"\s*[Tt]rue|[Ff]alse|TRUE|FALSE|[Yy]es|[Nn]o|YES|NO|[Yy]|[Nn]\s*$")
        }
        for data_type, data_re in data_type_map.items():
            result = data_re.findall(data)
            if result and len(result) == 1:
                return data_type(result[0].strip())
        return data

    @staticmethod
    def boolean(data):
        if data.lower() in ['true', 'yes', 'y']:
            return True
        elif data.lower() in ['false', 'no', 'n']:
            return False
        else:
            return data


@Singleton
class _CONF(object):
    def __init__(self):
        self._parser = ConfigParser.SafeConfigParser()
        self._parser.read(CONF_PATH)
        for section in self._parser.sections():
            self.__setattr__(section.replace(" ","_"), Option(section, self._parser))
        if self._parser.defaults():
            for k, v in self._parser.defaults().items():
                self.__setattr__(k.replace(" ","_"), Option.data_type(v))

    def __getattr__(self, item):
        if item in self._parser.sections():
            return Option(item, self._parser)
        else:
            raise ConfigError("the section/option:{} if not defined!".format(item))




class ConfigError(Exception):
    pass


import pdb

pdb.set_trace()
CONF = _CONF()
print 'test'