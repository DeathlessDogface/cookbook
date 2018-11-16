import pecan

from v1.root import V1RootController


class RootController(object):
    v1 = V1RootController()

    @pecan.expose()
    def hello(self):
        return "hello world"
