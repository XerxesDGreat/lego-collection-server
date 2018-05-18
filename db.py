import sqlite3
import csv
import os
import time
import config


class DB(object):
    base_tables = {
        "file_times": {
            "columns": [
                ("file_name", "VARCHAR(40)", "PRIMARY KEY"),
                ("updated", "INT")
            ]
        },
        "colors": {
            "file_path": "fixtures/colors.csv",
            "columns": [
                ("rgb", "VARCHAR(6)"),
                ("id", "INT", "PRIMARY KEY"),
                ("is_trans", "VARCHAR(1)"),
                ("name", "VARCHAR(20)")
            ]
        },
        "inventories": {
            "file_path": "fixtures/inventories.csv",
            "columns": [
                ("id", "INT", "PRIMARY KEY"),
                ("version", "INT"),
                ("set_num", "VARCHAR(15)")
            ]
        },
        "inventory_parts": {
            "file_path": "fixtures/inventory_parts.csv",
            "columns": [
                ("inventory_id", "INT"),
                ("part_num", "VARCHAR(25)"),
                ("color_id", "INT"),
                ("quantity", "INT"),
                ("is_spare", "VARCHAR(1)")
            ]
        },
        "part_categories": {
            "file_path": "fixtures/part_categories.csv",
            "columns": [
                ("id", "INT"),
                ("name", "VARCHAR(50)")
            ]
        },
        "parts": {
            "file_path": "fixtures/parts.csv",
            "columns": [
                ("part_num", "VARCHAR(25)"),
                ("name", "VARCHAR(200)"),
                ("part_cat_id", "INT")
            ]
        },
        "sets": {
            "file_path": "fixtures/sets.csv",
            "columns": [
                ("set_num", "VARCHAR(15)"),
                ("name", "VARCHAR(200)"),
                ("year", "INT"),
                ("theme_id", "INT"),
                ("num_parts", "INT")
            ]
        },
        "themes": {
            "file_path": "fixtures/themes.csv",
            "columns": [
                ("id", "INT"),
                ("name", "VARCHAR(50)"),
                ("parent_id", "INT")
            ]
        },
        "my_sets": {
            "file_path": "fixtures/xerxes-2017-01-24.csv",
            "columns": [
                ("set_number", "VARCHAR(15)"),
                ("quantity", "INT"),
                ("display", "VARCHAR(1)")
            ]
        }
    }
    query_select_file_import_time = "SELECT updated FROM file_times WHERE file_name=:file_name"
    query_table_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
    query_table_insert = "INSERT INTO %s (%s) VALUES (%s)"
    query_file_imported_insert_phase = "INSERT OR IGNORE INTO file_times VALUES(:file_name, 0)"
    query_file_imported_update_phase = "UPDATE file_times SET updated=:updated_time WHERE file_name=:file_name"
    query_truncate = "DELETE FROM %s"

    def __init__(self, logger=None):
        self.dbconn = sqlite3.connect('collection.db')
        self.dbconn.text_factory = str
        self.dbconn.row_factory = sqlite3.Row
        self.c = self.dbconn.cursor()
        self.log = logger if logger else config.get_logger('db')

    def _query(self, query, args=None):
        self.log.debug("query: %s, args %s", query, args)
        if args:
            self.c.execute(query, args)
        else:
            self.c.execute(query)

    def _query_many(self, query, args):
        self.log.debug("query: %s, args %s", query, args)
        self.c.executemany(query, args)

    def query_one(self, query, args):
        self._query(query, args)
        return self.c.fetchone()

    def query(self, query, args=None):
        self._query(query, args)
        return self.c.fetchall()

    def query_cursor(self, query, args=None):
        self._query(query, args)
        return self.c

    def query_no_return(self, query, args=None):
        self._query(query, args)

    def query_many_no_return(self, query, data):
        self._query_many(query, data)
    
    def commit(self):
        self.dbconn.commit()

    def run_fixtures(self):
        self.log.info("running fixtures")
        for table_name, meta in self.base_tables.items():
            self.log.info("verifying table %s", table_name)
            if not self.table_exists(table_name):
                self.log.info("creating table %s", table_name)
                col_str = ", ".join([" ".join(col) for col in meta["columns"]])
                sql = "CREATE TABLE %s (%s);" % (table_name, col_str)
                self.query_no_return(sql)
            if "file_path" in meta:
                self.import_data_from_file(table_name, meta["file_path"])

    def table_exists(self, table_name):
        results = self.query_one(self.query_table_exists, {"table_name": table_name})
        self.log.debug("table exists results: %s", results)
        return results is not None and len(results) > 0

    def truncate(self, table_name):
        self.query_no_return(self.query_truncate % table_name)

    def run_and_commit(self, operations):
        operations()
        self.dbconn.commit()

    def get_file_last_modified(self, file_path):
        return int(os.path.getmtime(file_path))
    
    def get_file_last_imported(self, file_name):
        last_imported = self.query_one(self.query_select_file_import_time, {"file_name": file_name})
        if last_imported is None:
            return 0
        return last_imported[0]
    
    def is_file_up_to_date(self, file_name, file_path):
        file_modified_time = self.get_file_last_modified(file_path)
        last_imported_time = self.get_file_last_imported(file_name)
        self.log.debug("imported: %s, modified: %s" % (last_imported_time, file_modified_time))
        return last_imported_time and file_modified_time <= last_imported_time
    
    def read_csv(self, file_path):
        rows = []
        keys = None
        with open(file_path) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if keys is None:
                    keys = row.keys()
                rows.append(row)
        return keys, rows
    
    def import_data_from_file(self, table_name, file_path):
        if not os.path.isfile(file_path):
            raise IOError()
        if self.is_file_up_to_date(table_name, file_path):
            self.log.info("table '%s' is up to date", table_name)
            return

        self.log.info("importing file '%s' into table '%s'", file_path, table_name)
        
        (keys, rows) = self.read_csv(file_path)

        def row_generator():
            for r in rows:
                print (r)
                yield tuple(r.values())
    
        def table_update_operations():
            self.truncate(table_name)
            sql = self.query_table_insert % (table_name, ",".join(keys), ",".join(["?" for k in keys]))
            self.query_many_no_return(sql, row_generator())
            self.query_no_return(self.query_file_imported_insert_phase, {"file_name": table_name})
            self.query_no_return(self.query_file_imported_update_phase, {"file_name": table_name, "updated_time": int(time.time())})
    
        self.run_and_commit(table_update_operations)


db_conn = None


def get_instance(logger=None):
    global db_conn
    if not db_conn:
        db_conn = DB(logger)
        db_conn.run_fixtures()
    return db_conn
