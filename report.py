# -*- coding: utf8 -*-
import bot
from bot import BotModule
import os,threading,cgi,zipfile,glob
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

base_help="""

"""

class ReportModule(BotModule):
    """
    Le module chargé de vous fournir la jolie page d'aide que voilà.
    """

    def __init__(self,bot):
        BotModule.__init__(self,bot)
        self.server=WebServer(self,bot.conf["report_port"])
        self.server.start()

    def unload(self):
        self.server.cont=False
        self.server.server.socket.close()
        self.server._Thread__stop()

    def report_main(self):
        f=open("db/help_header.html","r")
        s=f.read()
        f.close()
        for k,v in self.bot.modules.items():
            r=self.module2html(v[0]) 
            if r and not k.startswith("plugins."):
                s+=r
        for k,v in self.bot.modules.items():
            r=self.module2html(v[0]) 
            if r and k.startswith("plugins."):
                s+=r
        f=open("db/help_footer.html","r")
        s+=f.read()
        f.close()
        return s

    def module2html(self,module):
        s="<a name='%s'><h3>%s</h3></a>" % (module.__class__.__name__,module.__class__.__name__)
        r=module.__doc__
        if r:
            s+="<h4>Description</h4>"+r
        r=module.help_content()
        if r:
            s+=r
        if module.get_functions():
            s+="<h4>Fonctions exportées</h4>" 
            s+="<table width='100%', border='1'><tr><th>Prototype</th><th>Description</th></tr>"
            for f in module.get_functions():
                    name,fn,types,doc,proto=self.bot.get_prototype_function(f[0])
                    s+="<tr><td><b>%s</b></td><td>%s</td></tr>"%(cgi.escape(proto),doc)
            s+="</table>"
        return s


class WebServer(threading.Thread):
    def __init__(self,mod,port):
        threading.Thread.__init__(self)
        self.server = HTTPServer(('', port), RequestHandler)
        self.server.mod=mod
        self.cont=True

    def run(self):
        while self.cont:
            try:
                self.server.serve_forever()
            except:
                pass
        
class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        mod=self.server.mod
        if self.path=="/":
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(mod.report_main())
            return
        elif self.path=="/sources.zip":
            self.send_response(200)
            self.send_header('Content-type','application/octet-stream')
            self.send_header('Content-disposition','attachment; filename=sources.zip')
            self.end_headers()
            f = zipfile.ZipFile("sources.zip", "w")
            for name in glob.glob("*.py"):
                f.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
            for name in glob.glob("plugins/*.py"):
                f.write(name, "plugins/"+os.path.basename(name), zipfile.ZIP_DEFLATED)
            f.write("./db/style.css", "db/style.css", zipfile.ZIP_DEFLATED)
            f.write("./db/help_header.html", "db/help_header.html", zipfile.ZIP_DEFLATED)
            f.write("./db/help_footer.html", "db/help_footer.html", zipfile.ZIP_DEFLATED)
            f.write("./db/mad2n/rules.py", "./db/mad2n/rules.py", zipfile.ZIP_DEFLATED)
            f.write("./db/mad2n/dico.py", "./db/mad2n/dico.py", zipfile.ZIP_DEFLATED)
            f.close()
            f=open("sources.zip","rb")
            self.wfile.write(f.read())
            f.close()
            return
        elif self.path=="/style.css":
            self.send_response(200)
            self.send_header('Content-type','text/css')
            self.end_headers()
            f=open("./db/style.css","r")
            self.wfile.write(f.read())
            f.close()
            return
        else:
            self.send_error(404,'File Not Found')
            
 
    def do_POST(self):
       pass

    def log_message(self,*args):
       pass
    
