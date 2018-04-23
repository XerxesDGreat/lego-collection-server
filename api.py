import tornado.ioloop
import tornado.web
import config
import sets

log = config.get_logger('api')


class AppRequestHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        d = {'code': status_code}
        if 'log_message' in kwargs:
            d['message'] = kwargs['log_message']
        self.write(d)

    def options(self):
        # no body
        self.set_status(204)
        self.finish()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')


class MainHandler(AppRequestHandler):
    def get(self):
        self.write({'message': 'LEGO Manager'})


class MySetsHandler(AppRequestHandler):
    def get(self):
        my_sets = sets.get_all_my_sets()
        self.write({"sets": {str(x.num): x.to_json() for x in my_sets}})


class SetDetailHandler(AppRequestHandler):
    def get(self, set_num):
        if not set_num:
            raise tornado.web.HTTPError(400, "missing set num")
        selected_set = sets.from_set_num(set_num)
        if not selected_set:
            raise tornado.web.HTTPError(404)
        self.write(sets.from_set_num(set_num).to_json())


def make_app():
    return tornado.web.Application([
        (r'/', MainHandler),
        (r'/sets', MySetsHandler),
        (r'/sets/(.*)', SetDetailHandler)
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
