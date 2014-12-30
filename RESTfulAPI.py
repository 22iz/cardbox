#!/usr/bin/ python
#encoding=utf-8


from datetime import date
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.httpserver
import json
import MySQLdb
import hashlib
import urllib

import os.path
import random
import string

import sys
reload(sys)
sys.setdefaultencoding('utf-8') 

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)

# import tornado.autoreload
settings = {'debug' : True}
# define("debug",default=True,help="Debug Mode",type=bool)


class VersionHandler(tornado.web.RequestHandler):
    def get(self):
        response = { 'version': 'alpha 0.0.1',
                     'last_build':  date.today().isoformat(),
                     'API': listAPI() }
        
        self.write(response)

class CardByIdHandler(tornado.web.RequestHandler):
    def get(self, id):
        conn = MySQLdb.connect("localhost", "root", "Fl2014", charset="utf8")
        conn.select_db("cardbox_alpha")
        cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM cardboxers WHERE id = "+str(id))
        result = cur.fetchall()
        for rs in result:
            response = { 'carboxer_id': rs['cardboxer_id'],
                         'name': rs['name'],
                         'title': rs['title'],
                         'email': rs['email'],
                         'content': rs['content'],
                         'image': rs['image']
                         # 'release_date': date.today().isoformat(),
                         # 'API': listAPI() 
                        }
        cur.close()
        conn.close()
        self.write(response)

def listAPI():
    msg = 'API: '
    api_version = 'http://120.24.224.48:8000/version'
    api_cardbyid = 'http://120.24.224.48:8000/cardbyid/id'
    api_register = 'http://120.24.224.48:8000/register'
    api_recommend = 'http://120.24.224.48:8000/recommend/number_of_record'
    return msg + api_version + ", " + api_cardbyid + ", " + api_register + ", " + api_recommend

class Application(tornado.web.Application):
    def __init__(self):
        fname = "[0-9A-Za-z]+"
        cardboxer_id = "\d+"
        extension = "[A-Za-z]+"
        img_url = r"/img/("+fname+"_"+cardboxer_id+"[\.]"+extension+")"
        handlers = [
            (r"/cardbyid/([0-9]+)", CardByIdHandler),
            (r"/version", VersionHandler),
            (r"/", IndexHandler),
            (img_url, tornado.web.StaticFileHandler, {"path": "./img"}),
            (r"/register", RegisterHandler),
            (r"/login", LoginHandler),
            (r"/recommend/([0-9]+)", RecommendHandler)
        ]
        tornado.web.Application.__init__(self, handlers, **settings) # use it when development
        # tornado.web.Application.__init__(self, handlers) # use it when production

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("register.html")

class RegisterHandler(tornado.web.RequestHandler):
    def post(self):
        cardboxer_id = random.randint(0, 1000000000)
        name = self.get_argument('name')
        password = self.get_argument('password')
        email = self.get_argument('email')
        title = self.get_argument('title')
        content = self.get_argument('content')
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        
        # 检测有否图片上传
        try:
            self.request.files['file'][0]
        except AttributeError:
            final_filename = "no_file"
            self.write("no_file\n")
        except KeyError:
            final_filename = "no_file"
            self.write("no_file\n")
        else:
            file1 = self.request.files['file'][0]
            original_fname = file1['filename']
            extension = os.path.splitext(original_fname)[1]
            final_filename= fname+"_"+str(cardboxer_id)+extension
            output_file = open("img/" + final_filename, 'w')
            output_file.write(file1['body'])
            self.write("成功上传图片：\"" + final_filename + "\"<br/><br/>")

        conn = MySQLdb.connect("localhost", "root", "Fl2014", charset="utf8")
        conn.select_db("cardbox_alpha")
        cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        # cur.execute("insert into cardboxers(name, title, password, email, content, image, cardboxer_id) values (%s, %s, %s, %s, %s, %s, %s)", (name, title, hashlib.md5(password).hexdigest(), email, content, 'http://120.24.224.48:8000/img/'+final_filename, cardboxer_id))
        cur.execute("insert into cardboxers(name, title, password, email, content, image, cardboxer_id) values (%s, %s, %s, %s, %s, %s, %s)", (name, title, password, email, content, 'http://120.24.224.48:8000/img/'+final_filename, cardboxer_id))
        conn.commit()
        cur.close()
        conn.close()
        self.finish('恭喜成功注册！')

class LoginHandler(tornado.web.RequestHandler):
    """docstring for LoginHandler"""
    def post(self):
        email = self.get_argument('email')
        password = self.get_argument('password')
        conn = MySQLdb.connect("localhost", "root", "Fl2014", charset="utf8")
        conn.select_db("cardbox_alpha")
        cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM cardboxers WHERE email='"+email+"' AND password='"+password+"'")
        result = cur.fetchone()
        if result:
            print "success"
            self.write('Successful 登录')
        else:
            print "fail"
            self.write('Fail 请重新输入')

        

# 请求推荐卡片
class RecommendHandler(tornado.web.RequestHandler):
    def get(self, number):
        conn = MySQLdb.connect("localhost", "root", "Fl2014", charset="utf8")
        conn.select_db("cardbox_alpha")
        cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM cardboxers LIMIT " + str(number))
        result = cur.fetchall()
        count = 1
        response = {}
        for rs in result:
            card_count = 'card' + str(count)
            temp = { 'carboxer_id': rs['cardboxer_id'],
                         'name': rs['name'],
                         'title': rs['title'],
                         'email': rs['email'],
                         'content': rs['content'],
                         'image': rs['image']
                        }
            response[card_count] = temp
            count += 1
        self.write(response)
        cur.close()
        conn.close()
        
def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
