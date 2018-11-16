from pecan import expose
from pecan import rest


class V1RootController(rest.RestController):
    @expose(template='json')
    def get(self):
        return {'test': 'this is v1 root get'}

    @expose(template='json')
    def put(self, **kwargs):
        return {'test': 'this is v1 root put'}

    @expose(template='json')
    def post(self, **kwargs):
        return {'test': 'this is v1 root post'}

    @expose(template='json')
    def delete(self, **kwargs):
        return {'test': 'this is v1 root delete'}
