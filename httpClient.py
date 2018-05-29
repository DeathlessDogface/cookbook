import urllib
import urllib2


class UrlChain:
    def __init__(self, path=''):
        self._path = path

    def __getattr__(self, item):
        return UrlChain('%s/%s' % (self._path, item))

    def __str__(self):
        return self._path

    def __call__(self, index):
        return UrlChain('%s/%s' % (self._path, index))


class HttpClient(object):
    def __init__(self):
        pass

    def get(self, url, **kwargs):
        if kwargs:
            parames = []
            for k, v in kwargs.items():
                parames.append("{}={}".format(k, v))
            _url = "%s?%s" % (url, "&".join(parames))
        else:
            _url = str(url)
        request = urllib2.Request(_url)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request)
        return response.read()

    def post(self, url, **kwargs):
        data = urllib.urlencode(kwargs)
        request = urllib2.Request(str(url), data)
        response = urllib2.urlopen(request)
        return response.read()

    def delete(self, url):
        request = urllib2.Request(str(url))
        request.get_method = lambda: 'DELETE'
        response = urllib2.urlopen(request)
        return response.read()

    def put(self, url, **kwargs):
        data = urllib.urlencode(kwargs)
        request = urllib2.Request(str(url), data)
        request.get_method = lambda: 'PUT'
        response = urllib2.urlopen(request)
        return response.read()


class LogClient(object):
    def __init__(self, ip, port=None):
        self.client = HttpClient()
        if isinstance(port, int):
            self.baseurl = UrlChain("http://{}:{}".format(ip, port))
        else:
            self.baseurl = UrlChain("http://{}".format(ip))

    def test(self):
        return self.client.get(self.baseurl.f, ie='utf-8', kw='python', fr='search', red_tag='g2349925280')

    def search(self):
        return self.client.get(self.baseurl.log.search, query={"search": "api", "filter": {"loglevel": "INFO"}})


if __name__ == "__main__":
    # http://tieba.baidu.com/f?ie=utf-8&kw=python&fr=search&red_tag=g2349925280
    # LC = LogClient('10.100.46.93', 9002)
    LC = LogClient("tieba.baidu.com")
    print LC.test()
