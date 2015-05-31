import threading,socket,time,re,traceback,sys
import xmpp

class Channel(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.callbacks=[]
        self.nick=""
        self.goon=True


    def register(self,fn):
        if not fn in self.callbacks:
            self.callbacks.append(fn)

    def message(self,txt,author,spectators,thread,private):
        for fn in self.callbacks:
            try:
                fn(txt,author,spectators,self,thread,private)
            except: pass

    def out(self,txt,thread="all"):
        """
        Ecriture d'un message
        """
        pass

    def join_thread(self,thread):
        pass

    def leave_thread(self,thread):
        pass

    def connect(self):
        """
        Connexion au serveur
        """
        pass

    def process(self):
        """
        Lecture d'un message
        """
        pass

    def set_nick(self,nick):
        self.nick=nick

    def quit(self):
        self.goon=False

    def run(self):
        """
        Boucle principale
        """
        while self.goon:
            try:
                print "[CHANNEL] %s connecting ..." % self.__class__.__name__
                self.connect()
                print "[CHANNEL] %s connected" % self.__class__.__name__
                while self.goon:
                    self.process()
            except BaseException,e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print "[CHANNEL] Error: %s@%s, reconnecting" % (e,traceback.extract_tb(exc_traceback)[-1])
                tmp=self.goon
                self.quit()
                self.goon=tmp
                time.sleep(10)



#===============================================================================
#
#   Console Channel
#
#===============================================================================
import sys
class ConsoleChannel(Channel):
    
    def __init__(self):
        Channel.__init__(self)
        
    def out(self,txt,thread="all"):
        print ">",txt
        
    def process(self):
        msg=sys.stdin.readline()[:-1]
        msg=msg.decode("cp850").encode("utf8")
        if msg:
            self.message(msg,"Moi",["Moi",self.nick],"local",True)
        else:
            return

#===============================================================================
#
#   Voice Channel
#
#===============================================================================
class VoiceChannel(Channel):
    
    def __init__(self):
        Channel.__init__(self)
        
    def out(self,txt,thread="all"):
        from util import speech
        print ">",txt.decode("utf8").encode("cp850")
        speech.say(txt.decode("utf8"))
        
    def process(self):
        from util import speech
        msg=speech.input()
        if msg:
            msg=msg.encode("utf8")
            self.message(msg,"Moi",["Moi",self.nick],"local",True)
        else:
            return

#===============================================================================
#
#   Irc Channel
#
#===============================================================================

class IrcTimer(threading.Thread):
    def __init__(self,irchan):
        threading.Thread.__init__(self)
        self.irc=irchan
        self.goon=True
        
    def run(self):
        while self.goon:
            time.sleep(10)
            for c in self.irc.chans:
                if not c in self.irc.chans_on:
                    try:
                        self.irc.join_thread(c)
                    except: pass
                else:
                    try:
                        self.irc.sock.send("NAMES %s\n" % c)
                    except: 
                        self.irc.connected=False

        
        
class IrcChannel(Channel):
    
    
    def __init__(self,server="irc.epiknet.org",port=6667,nick="mad2n",leschan=["#fatt"]):
        Channel.__init__(self)
        self.chans=leschan
        self.nick=nick
        self.ircserver=server
        self.port=port
        self.connected=False

    def connect(self):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect((self.ircserver,self.port))
        self.sock.send("USER %s %s %s %s\n" % (self.nick,self.nick,self.nick,self.nick))
        self.sock.send("NICK " + self.nick + "\n")
        self.chans_on=set()
        self.nick_lists={}
        self.timer=IrcTimer(self)
        self.timer.start()        
        self.freq=0
        self.connected=True
        
    def process(self):
        if not self.connected:
            raise ValueError("Not connected")
        msg=self.sock.recv(1024)
        msg=msg.replace("\r","")
        for e in msg.split("\n"):
            t=e.split(" :")
            commande=t[0]
            if commande != "":
                texte=" :".join(t[1:])
                if commande.upper()=="PING":
                    self.sock.send("PONG "+texte+"\n")
                elif commande[0]==':':
                    t=commande.split(" ")
                    if len(t) < 2:
                        continue
                    nick=t[0].split("!")
                    nick=nick[0][1:]
                    if t[1].upper()=="PRIVMSG":
                        channel=t[2]
                        if not "#" in channel:
                            channel=nick
                        self.last_nick=nick
                        if not self.nick_lists.has_key(channel):
                            self.nick_lists[channel]=[]
                        texte=to_utf8(texte)
                        self.message(texte.strip(),nick,self.nick_lists[channel],channel,channel==nick)
                    elif t[1].upper()=="KICK":
                        if texte==self.nick:
                            self.chans_on.discard(t[2])
                    elif t[1]=="353":
                        channel=t[4]
                        texte=texte.split(" ")
                        if texte:
                            texte=texte[:-1]
                        self.nick_lists[channel]=map(lambda x: x.replace("@","").replace("%","").replace("+",""),texte)
                    elif t[1].upper()=="JOIN":
                        if nick==self.nick:
                            self.chans_on.add(texte)

    def join_thread(self,channel):
        """Rejoint un channel"""
        self.sock.send("JOIN "+channel+"\n")
        return

    def set_nick(self,nick):
        """Change le nom du bot"""
        self.nick=nick
        if self.connected:
            self.sock.send("NICK "+nick+"\n")
        return

    def leave_thread(self,channel):
        """Quitte le chan <channel>"""
        self.sock.send("PART %s\n" % channel)

    def out(self,what,chan="all",private=False):
        t=str(what).split("\n")
        if not private:
            target=chan
        else:
            target=self.last_nick
        for msg in t:
            if len(msg)>300:
                return
            if self.freq:
                time.sleep(self.freq*len(msg))
            self.sock.send("PRIVMSG %s :%s\n" % (target,msg))
        return 

    def quit(self):
        Channel.quit(self)
        self.sock.close()
        self.timer.goon=False
        self.timer._Thread__stop()
        self.connected=False


#===============================================================================
#
#   Log Channel
#
#===============================================================================
class LogChannel(Channel):
    
    def __init__(self,filename):
        Channel.__init__(self)
        self.filename=filename
        
    def out(self,txt,thread="all"):
        print ">",txt
        
    def process(self):
        #Gather all nicks
        f=open(self.filename,"r")
        r=re.compile(r'^<([^>]+)> ')
        nicks=set()
        for l in f.readlines():
            for m in r.findall(l):
                nicks.add(m)
        f.close()
        f=open(self.filename,"r")
        lines=f.readlines()
        i=1
        for l in lines:
            l=to_utf8(l)
            m=r.search(l)
            if not m:
                raise ValueError("Malformated log line %i: %s" % (i,l))
            nick=m.groups()[0]
            l=r.sub("",l).strip()
            self.message(l,nick,nicks,"#fat",False)
            i+=1
            if i%100==0:
                sys.stderr.write("Log: %d/%d\n"%(i,len(lines)))
        f.close()
        self.quit()


#===============================================================================
#
#   DumpLog Channel
#
#===============================================================================
class DumpLog(Channel):
    
    def __init__(self,filename):
        Channel.__init__(self)
        self.filename=filename
        
    def out(self,txt,thread="all"):
        print ">",txt
        
    def process(self):
        #Gather all nicks
        f=open(self.filename,"r")
        lines=f.readlines()
        i=1
        for l in lines:
            l=to_utf8(l)
            self.message(l,"Moi",["Moi"],"#fat",False)
            i+=1
            if i%100==0:
                sys.stderr.write("%d/%d\n"%(i,len(lines)))
        f.close()
        self.quit()



#===============================================================================
#
#   Gtalk Channel
#
#===============================================================================
class GtalkChannel(Channel):
    
    def __init__(self,login,password):
        Channel.__init__(self)
        self.login=login
        self.password=password
        self.server_host = "talk.google.com"
        self.server_port = 5223
        self.show= "available"
        self.status="Mad2n ftw"
        self.conn=None
        self.timer=None

    def connect(self):
        self.disconnected=False
        jid=xmpp.JID(self.login)
        user, server, password = jid.getNode(), jid.getDomain(), self.password
        self.conn=xmpp.Client(server,debug=[])
        conres=self.conn.connect( server=(self.server_host, self.server_port) )
        if not conres:
            print "Unable to connect to server %s!"%server
            sys.exit(1)
        if conres<>'tls':
            print "Warning: unable to estabilish secure connection - TLS failed!"
        
        authres=self.conn.auth(user, password, "laptop")
        if not authres:
            print "Unable to authorize on %s - Plsese check your name/password."%server
            sys.exit(1)
        if authres<>"sasl":
            print "Warning: unable to perform SASL auth os %s. Old authentication method used!"%server
        
        self.conn.RegisterHandler("message", self.controller)
        self.conn.RegisterHandler('presence',self.presenceHandler)
        self.conn.RegisterDisconnectHandler(self.on_disconnect)
        self.conn.sendInitPresence()
        self.setState(self.show, self.status)
        if self.timer:
            try:
                self.timer.cancel()
            except: pass
        self.timer=threading.Timer(600,self.ping)
        self.timer.start()


    def on_disconnect(self):
        self.disconnected=True

    def ping(self):
        """
        Evite les deconnection pour cause d'idle
        """
        try:
            self.conn.send(" ")
            self.timer=threading.Timer(600,self.ping)
            self.timer.start()
        except:
            pass

    def quit(self):
        if self.timer:
            try:
                self.timer.cancel()
            except: pass

    def process(self):
        try:
            self.conn.Process(1)
        except ValueError:
            pass
        if self.disconnected:
            raise IOError

    def setState(self, show, status_text):
        if show == "online" or show == "on" or show == "available":
            show = "available"
        elif show == "busy" or show == "dnd":
            show = "dnd"
        elif show == "away" or show == "idle" or show == "off" or show == "out" or show == "xa":
            show = "xa"
        else:
            show = "available"
        self.show = show
        if status_text:
            self.status = status_text
        if self.conn:
            pres=xmpp.Presence(typ='available',priority=5,  show=self.show, status=self.status)
            self.conn.send(pres)

    def getState(self):
        return self.show, self.status

    def out(self, txt, thread):
        txt=to_utf8(txt)
        self.conn.send(xmpp.Message(thread, txt,typ='chat'))

    def getRoster(self):
        return self.conn.getRoster()

    def controller(self, conn, message):
        text = message.getBody()
        user = message.getFrom()
        nick=str(user.node)
        if text:
            text = text.encode('utf-8', 'ignore')
            self.message(text,nick,[nick],user,True)

    def presenceHandler(self, conn, presence):
        if presence and presence.getType()=='subscribe':
            jid = presence.getFrom().getStripped()
            self.getRoster().Authorize(jid)

    def disconnectHandler(self,*args):
        self.disconnected=True


#===============================================================================
#
#   Misc
#
#===============================================================================

def to_utf8(texte):
    #Detection charset
    #enc=chardet.detect(texte)["encoding"]
    #if enc!="utf-8" and enc!="ascii":
    #    try:
    #        texte=texte.decode("latin1").encode("utf8")
    #    except:
    #        pass
    try:
        texte.decode("utf8")
    except:
        try:
            texte=texte.decode("latin1").encode("utf8")
        except:
            tmp=""+texte
            texte=""
            for c in tmp:
                if ord(c)<127:
                    texte+=c
    return texte

