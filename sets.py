import db
import themes
import cache
import config
import parts

db_conn = db.get_instance()


query_by_id = "SELECT s.*, ms.display, ms.quantity FROM sets s, my_sets ms WHERE set_num=:set_num AND s.set_num = ms.set_number"
query_all_my_sets = "SELECT s.*, ms.quantity, ms.display FROM sets s, my_sets ms WHERE s.set_num = ms.set_number"
query_update_my_set = "UPDATE my_sets SET display = :display, quantity = :quantity WHERE set_number=:set_num"
query_all_my_sets_containing_part = """SELECT s.*, s.display, ip.color_id, s.quantity
FROM (
    select s.*, ms.display, ms.quantity from sets s, my_sets ms
    where s.set_num = ms.set_number
) s, inventories i, inventory_parts ip
WHERE ip.part_num = :part_num AND ip.color_id = :color_id
AND i.id = ip.inventory_id
AND i.set_num = s.set_num;
"""

log = config.get_logger('sets')


class Set(object):
    query_for_latest_inventory = "SELECT `id` FROM inventories WHERE set_num=:set_num ORDER BY version DESC LIMIT 1"

    def __init__(self, data):
        self.name = data["name"]
        self.num = data["set_num"]
        self.year = data["year"]
        self.theme_id = data["theme_id"]
        self.num_parts = data["num_parts"]
        self.on_display = data["display"] == "t"
        self.quantity_owned = data["quantity"]
        self.inventory = None

    keys_to_replace = {
        'theme_id': 'themeId',
        'num_parts': 'numParts',
        'on_display': 'onDisplay',
        'quantity_owned': 'quantityOwned'
    }

    keys_to_ignore = [
        'inventory'
    ]

    def to_json(self):
        json_obj = {}
        for k in self.__dict__:
            if k in self.keys_to_ignore:
                continue
            if k in self.keys_to_replace:
                json_obj[self.keys_to_replace[k]] = self.__dict__[k]
            else:
                json_obj[k] = self.__dict__[k]
        return json_obj

    def update_from_json(self, data):
        self.on_display = data.get('on_display', self.on_display)
        self.quantity_owned = data.get('quantity_owned', self.quantity_owned)
    
    def get_theme(self):
        return themes.from_id(self.theme_id)

    def is_on_display(self):
        return self.on_display or self.get_theme().is_related_to(themes.SEASONAL)

    def get_inventory(self):
        if self.inventory:
            return self.inventory
        latest_inventory_id = db_conn.query_one(self.query_for_latest_inventory, {"set_num": self.num})[0]
        config.get_logger("sets").info("latest inventory id: %s" % latest_inventory_id)
        self.inventory = parts.for_inventory_id(latest_inventory_id)
        return self.inventory

    def save(self):
        query_args = {
            "set_num": self.num,
            "display": "t" if self.on_display else "f",
            "quantity": self.quantity_owned
        }
        log.info(query_args)
        db_conn.query_no_return(query_update_my_set, query_args)
        db_conn.commit()


def from_set_num(set_num):
    def create():
        return Set(db_conn.query_one(query_by_id, {"set_num": set_num}))
    return cache.remember("set", set_num, create) 


def get_all_my_sets():
    def fetch():
        return [Set(row) for row in db_conn.query(query_all_my_sets)]
    return cache.remember('my_sets', 'all', fetch)


def get_all_my_sets_containing_part(part_num, color):
    def fetch():
        return [Set(row) for row in db_conn.query(query_all_my_sets_containing_part, {"part_num": part_num, "color_id": color})]
    return cache.remember('my_sets_containing_part', '%s:%s' % (part_num, color), fetch)

