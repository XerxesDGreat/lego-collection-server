import tornado.ioloop
import tornado.web
import config
import sets
import json
import parts

log = config.get_logger('api')

NotFound = tornado.web.HTTPError(404)


class AppRequestHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        d = {
            'code': status_code
        }
        # if 'exc_info' in kwargs:
        #     d['error'] = {
        #         'type': type(kwargs['exc_info'][0]),
        #         'message': kwargs['exc_info'][1].message
        #     }
        #     log.exception(kwargs['exc_info'])
        if 'log_message' in kwargs:
            d['message'] = kwargs['log_message']
        self.write(d)

    def options(self, *args, **kwargs):
        # no body
        self.set_status(204)
        self.finish()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT')

    def prepare(self):
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            self.json_args = json.loads(self.request.body)
        else:
            self.json_args = None


class MainHandler(AppRequestHandler):
    def get(self):
        self.write({'message': 'LEGO Manager'})


class MySetsHandler(AppRequestHandler):
    def get(self):
        my_sets = sets.get_all_my_sets()
        self.write({"data": [x.to_json() for x in my_sets]})


class SetDetailHandler(AppRequestHandler):
    def get(self, set_num):
        if not set_num:
            raise tornado.web.HTTPError(400, "missing set num")
        selected_set = sets.from_set_num(set_num)
        if not selected_set:
            raise NotFound
        self.write(sets.from_set_num(set_num).to_json())

    def put(self, set_num):
        selected_set = sets.from_set_num(set_num)
        if not selected_set:
            raise NotFound
        selected_set.update_from_json(self.json_args)
        selected_set.save()
        self.write(selected_set.to_json())


class MyPartsHandler(AppRequestHandler):
    def get(self):
        my_parts = parts.get_all_for_sets(sets.get_all_my_sets())
        response = {
            "totalCount": my_parts['total_count'],
            "parts": {}
        }

        for part_num, part_info in my_parts['parts'].iteritems():
            response_part = part_info['part'].to_json()
            for key in ['count', 'colors', 'storage', 'display']:
                response_part[key] = part_info[key]
            response['parts'][part_num] = response_part

        self.write({'data': response})


def make_app():
    return tornado.web.Application([
        (r'/', MainHandler),
        (r'/sets/?', MySetsHandler),
        (r'/sets/(.*)', SetDetailHandler),
        (r'/parts/?', MyPartsHandler)
    ])


if __name__ == '__main__':
    print("""
    
888
888                         
888                         
888 .d88b.  .d88b.  .d88b.  
888d8P  Y8bd88P"88bd88""88b 
88888888888888  888888  888 
888Y8b.    Y88b 888Y88..88P 
888 "Y8888  "Y88888 "Y88P"  
                888         
           Y8b d88P         
            "Y88P"
""")
    print("Running the LEGO manager api")
    app = make_app()
    print("listening on port %s. To change this port, edit the `http_port` variable in `config.py`" % config.http_port)
    app.listen(config.http_port)
    tornado.ioloop.IOLoop.current().start()
