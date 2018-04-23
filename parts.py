import db
import cache

db_conn = db.get_instance()

query_category_by_id = "SELECT * FROM part_categories WHERE id=:id"
query_part_by_id = "SELECT * FROM parts WHERE part_cat_id=:id"
query_by_inventory_id = "SELECT * FROM inventory_parts ip, parts p where ip.part_num = p.part_num and ip.inventory_id=:inventory_id"
query_by_category_id = "SELECT * FROM parts WHERE part_cat_id=:cat_id"


class Part(object):
    def __init__(self, data):
        self.part_num = data["part_num"]
        self.name = data["name"]
        self.category_id = data["part_cat_id"]
        self.category = None
        self.thumbnail = data["thumbnail"]

    def get_category(self):
        if not self.category:
            self.category = category_from_id(self.category_id)
        return self.category


class InventoryPart(object):
    def __init__(self, data, part):
        self.inventory_id = data["inventory_id"]
        self.part = part
        self.color_id = data["color_id"]
        self.quantity = data["quantity"]
        self.is_spare = data["is_spare"] == "t"


class Inventory(object):
    def __init__(self, inventory_parts):
        self.inventory_parts = inventory_parts
        self.part_categories = None

    def get_total_part_count(self):
        return reduce(lambda acc, item: acc + item.quantity, self.inventory_parts, 0)

    def get_part_list(self):
        return [p.part for p in self.inventory_parts]

    def get_part_categories_with_count(self):
        if self.part_categories is None:
            self.part_categories = {}
            for inv_item in self.inventory_parts:
                n = inv_item.part.get_category().name
                prev = self.part_categories.get(n, 0)
                self.part_categories[n] = prev + inv_item.quantity
        return self.part_categories


class PartCategory(object):
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.parts = None

    def get_parts(self):
        if not self.parts:
            self.parts = for_category_id(self.id)
        return self.parts


def category_from_id(id):
    def create():
        return PartCategory(db_conn.query_one(query_category_by_id, {"id": id}))
    return cache.remember("part_category", id, create)


def part_from_id(id):
    def create():
        return Part(db_conn.query_one(query_part_by_id, {"id": id}))
    return cache.remember("part", id, create)


def for_inventory_id(inventory_id):
    def create():
        results = db_conn.query(query_by_inventory_id, {"inventory_id": inventory_id})
        return Inventory([InventoryPart(r, Part(r)) for r in results])
    return cache.remember("inventory_part_list", inventory_id, create)


def for_category_id(category_id):
    def create():
        results = db_conn.query(query_by_category_id, {"cat_id": category_id})
        return [Part(r) for r in results]
    return cache.remember("category_part_list", category_id, create)


def get_all_for_sets(sets):
    parts = {
        "total_count": 0,
        "parts": {}
    }
    for s in sets:
        set_parts = s.get_inventory().inventory_parts
        for sp in set_parts:
            part_num = sp.part.part_num
            if part_num not in parts["parts"]:
                parts["parts"][part_num] = {"part": sp.part, "count": 0, "display": 0, "storage": 0, "colors": {}}
            parts["parts"][part_num]["count"] += sp.quantity

            display_key = "display" if s.is_on_display() else "storage"
            parts["parts"][part_num][display_key] += sp.quantity

            color_id = str(sp.color_id)
            if color_id not in parts["parts"][part_num]["colors"]:
                parts["parts"][part_num]["colors"][color_id] = {"display": 0, "storage": 0}
            parts["parts"][part_num]["colors"][color_id][display_key] += sp.quantity

            parts["total_count"] += sp.quantity
    return parts