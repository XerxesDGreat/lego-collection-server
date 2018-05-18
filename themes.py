import db
import config
import cache

log = config.get_logger('themes')
log.info('gonna get instance')
db_conn = db.get_instance()
log.info('got instance')

class Theme(object):
    delim = " > "

    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.parent_id = data["parent_id"]
        self.parent = None

    def get_parent(self):
        if not self.parent_id:
            return None
        if self.parent is None:
            self.parent = from_id(self.parent_id)
        return self.parent

    def get_name(self):
        parent = self.get_parent()
        prefix = "" if parent is None else parent.get_name() + self.delim
        return prefix + self.name

    def is_related_to(self, theme):
        search_term = theme.id if isinstance(theme, Theme) else theme
        if search_term == self.id:
            return True
        if self.get_parent() is not None:
            return self.get_parent().is_related_to(search_term)


query_by_id = "SELECT * FROM themes WHERE id=:id"
def from_id(id):
    def create():
        return Theme(db_conn.query_one(query_by_id, {"id": id}))
    return cache.remember("theme", id, create) 

SEASONAL = from_id(206)
