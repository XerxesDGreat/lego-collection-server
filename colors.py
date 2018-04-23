import db
import config
import cache

log = config.get_logger('colors')
db_conn = db.get_instance()


class Color(object):
    def __init__(self, data):
        try:
            self.id = data['id']
            self.rgb = data['rgb']
            self.is_trans = data['is_trans']
            self.name = data['name']
        except KeyError as e:
            log.error('missing key in data %s' % data, e)

query_by_id = 'SELECT * FROM colors WHERE id=:id'
def from_id(id):
    def create():
        return Color(db_conn.query_one(query_by_id, {'id': id}))
    return cache.remember('color', id, create)
