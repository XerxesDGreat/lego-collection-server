import sqlite3
from lxml import html

with open("fixtures/rebrickable-table.html") as f:
    tree = html.fromstring(f.read())

rows = tree.xpath("//tr")[1:]
db_conn = sqlite3.connect("collection.db")
cur = db_conn.cursor()
query = "UPDATE parts SET thumbnail=:thumbnail WHERE part_num=:part_num"

for row in rows:
    children = row.getchildren()
    thumbnail = children[0].getchildren()[0].attrib.get("src")
    part_num = children[1].text
    cur.execute(query, {"thumbnail": thumbnail, "part_num": part_num})

db_conn.commit()
