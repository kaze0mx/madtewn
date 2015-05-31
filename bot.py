# -*- coding: utf8 -*-
"""
MADTEWN2
"""

import os,sys,inspect,copy,traceback
import data

try:
    import pyfiglet,pyfiglet.fonts    #stupid pkg !
except: pass

OUT_NONE=0
OUT_LOCAL=1
OUT_CHANNEL=2
OUT_FILE=4



default_conf= {
"mute":False,
"learn":True,
"always_answer":False,
"debug_verbosity":OUT_LOCAL,
"error_verbosity":OUT_LOCAL,
"report_port":5555,
"markov_nuplets":3,
"markov_allowed_semantics": set([1]),
"admins":["kaze"],
}




class BotModule:
    """
    La classe de base pour tous les modules du framework.
    """
    def __init__(self,bot):
        self.bot=bot

    def help_content(self):
        pass

    def unload(self):
        pass

    def save(self):
        pass

    def get_functions(self):
        res=[]
        for n in dir(self):
            elem=getattr(self,n)
            if n.startswith("function_") and callable(elem):
                args, varargs, varkw, defaults = inspect.getargspec(elem)
                prototype="%s%s" % (n[9:],inspect.formatargspec(args[1:],varargs,varkw,defaults,lambda x:"<%s>" % x))
                res.append((n[9:],elem,prototype,elem.__doc__,self))    
        return res


class Bot(BotModule):
    """
    Le module principal du bot, qui va charger tous les autres modules.
    """

    def __init__(self,name):
        BotModule.__init__(self,self)
        self.name=name
        self.data_dir="./db/%s" % self.name
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        self.channels=[]
        self.original_sys_modules=copy.copy(sys.modules)
        self.conf=data.DataConf("%s/conf.py" % self.data_dir,default_conf)
        self.load()
        self.debug("Bot loaded")


    def connect(self,chan):
        """
        Connecte le bot courant a un channel instancié.
        """
        self.channels.append(chan)
        chan.register(self.on_message)
        chan.set_nick(self.name)

    def hook_pre_message(self,fn):
        """
        Tous les modules peuvent appeler cette methode pour ajouter un hook a la reception de message.
        La fonction fn passée en parametre sera appellée a chaque reception de message (peu importe le channel) et avant la construction de la réponse au message. Ce hook est principalement destiné aux fonctions de stat et d'apprentissage.
        La fonction peut retourner un dictionnaires ({"nom_variable":valeur,}) dont les elements seront accessibles depuis les actions des regles
        """
        if not fn in self.callbacks:
            self.callbacks.append(fn)

    def on_message(self,msg,author,spectators,channel,thread,private):
        """
        Fonction principale du bot, calcule la reponse pour une message recu.
        """
        if not spectators:
            spectators=["Bob"]
        try:
            msg=msg.strip()
            if not msg:
                return
            if msg=="!quit" and author in self.conf["admins"]:
                self.function_quit()
                return
            elif msg=="!tg":
                self.function_tg()
                return
            elif msg=="!reload":
                self.function_reload()
                channel.out("%s reloaded" % self.name,thread)
                return
            elif msg.startswith("!join"):
                channel.join_thread(msg.split()[-1])
                return
            elif msg=="!leave":
                channel.leave_thread(thread)
                return
            #Translation using semantics ...
            private=private or self.name in msg or self.conf["always_interaction"]
            for deli in ",:>- ":
                if msg.startswith("%s%s" % (self.name,deli)):
                    msg=msg[len(self.name)+1:].lstrip()
            transduced=self.semantics.translate(msg,author,spectators,thread,private)
            self.debug("<<<< %s"%transduced)
            #Callbacks
            callback_dic={}
            for c in self.callbacks:
                dic=c(transduced,author,spectators,thread,private)
                if dic is not None:
                    callback_dic.update(dic)
            #Module interaction
            if not self.conf["mute"]:
                r=self.interaction.response(transduced,author,spectators,thread,private,callback_dic)
                if not r:
                    return
                sem,reponse=r
                transduced=self.semantics.translate_back(sem,reponse,author,spectators,thread,private)
                self.debug(">>>> %s"%transduced)
                msg=transduced[self.semantics.SEM_RAW]
                if msg and msg.strip():
                    for l in msg.split("\n"):
                        channel.out(l,thread)
        except BaseException,e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            last=traceback.extract_tb(exc_traceback)[-1]
            s="%s:%s" % (os.path.basename(last[0]),last[1])
            self.error(e,s,"\n".join(map(str,traceback.extract_tb(exc_traceback))))
            if self.conf["error_verbosity"] & OUT_CHANNEL:
                channel.out("[ERROR %s] %s" % (s,e),thread)




    def load(self):
        """
        Charge le bot et tous les modules associés
        """
        self.modules={"bot":(self,None)}
        self.callbacks=[]
        self.functions={}
        self.semantics=self.load_module("semantics.py")
        self.plugins=self.load_module("plugin.py")
        self.interaction=self.load_module("interaction.py")
        self.report=self.load_module("report.py")
        self.evaluator=self.load_module("eval.py")
        for inst,mod in self.modules.values():
            for f in inst.get_functions():
                self.functions[f[0]]=f[1]
        

    def load_module(self,fullpath):
        """
        Charge dynamiquement un module du bot.
        """
        path=os.path.relpath(fullpath)
        filename=os.path.basename(fullpath)
        modulename=".".join(path.replace(os.sep,".").split(".")[:-1])
        module=__import__(modulename)
        components = modulename.split('.')
        for comp in components[1:]:
            module = getattr(module, comp)
        for n in dir(module):
            elem=getattr(module,n)
            try:
                if issubclass(elem,BotModule) and elem!=BotModule:
                    inst=elem(self)
                    self.modules[modulename]=(inst,module)
                    return inst
            except TypeError:
                pass
        return None


    def get_prototype_function(self,name):
        """
        Retourne le prototype d'une fonction appelable du bot (ou d'un de ses modules externes).
        Retourne: (nom (string),objet fonction,liste des types des parametres,doc de la fonction,prototype formatté (string))        
        """
        if not self.functions.has_key(name):
            raise ValueError("No such function: %s" %name)
        fn=self.functions[name]
        args, varargs, varkw, defaults = inspect.getargspec(fn)
        if varargs is None:
            varargs=[]
        if varkw is None:
            varkw=[]
        if defaults is None:
            defaults=[]
        doc=fn.__doc__ or ""
        doc=filter(lambda x: x,map(str.strip,doc.split("\n")))
        types=None
        if doc and doc[0].startswith("("):
            types=doc[0][1:-1].split(",")
            doc=doc[1:]
        doc=" ".join(doc)
        proto="%s(" % name
        args=zip(args[1:]+varargs+varkw,([None]*(len(args)+len(varargs)))+list(defaults))
        for i in range(len(args)):
            if i>0:
                proto+=","
            a,d=args[i]
            t=""
            if types and len(types)>i:
                t=types[i]
            if d:
                d="="+d
            else:
                d=""
            proto+="%s<%s%s>" %(t,a,d)
        proto+=")"
        return (name,fn,types,doc,proto)                

###################################################################################
#
# LOGGING
#
###################################################################################

    def debug(self,msg):
        """
        Ecriture d'un message de debug
        """
        if self.conf["debug_verbosity"] & OUT_LOCAL:
            print "[DEBUG] %s" % msg
        if self.conf["debug_verbosity"] & OUT_FILE:
            f=open("debug.log","a")
            f.write("[DEBUG] %s\n" % msg)
            f.close()
        if self.conf["debug_verbosity"] & OUT_CHANNEL:
            for c in self.channels:
                c.out("[DEBUG] %s" % msg,"all")

    def error(self,exc,where="",full=""):
        """
        Ecriture d'un message d'erreur
        """
        if self.conf["error_verbosity"] & OUT_LOCAL:
            print "[ERROR %s] %s" % (where,str(exc))
        if self.conf["error_verbosity"] & OUT_FILE:
            f=open("error.log","a")
            f.write("[ERROR %s] %s\n" % (where,str(exc)))
            f.write(full+"\n")
            f.close()


###################################################################################
#
# Fonctions appelables depuis les channels
#
###################################################################################

    def function_bavard(self):
        """
        Toogle le mode bavard
        """
        self.conf["always_interaction"]=not self.conf["always_interaction"]
        return "bavard=%s" % self.conf["always_interaction"]

    def function_errors(self):
        """
        Toggle l'affichage des erreurs sur le channel
        """
        self.conf["error_verbosity"]^=OUT_CHANNEL
        return "errors_display=%s" % str((self.conf["error_verbosity"]&OUT_CHANNEL)!=0)


    def function_quit(self):
        """Quit"""
        for c in self.channels:
            c.quit()
            c._Thread__stop()
        for m in self.modules.values():
            m[0].save()
        for m in self.modules.values():
            m[0].unload()
        sys.exit()

    def function_tg(self):
        """Fait se taire/parler le bot"""
        if self.conf["mute"]:
            new_nick=self.name
        else:
            new_nick=self.name+"_tg"
        for c in self.channels:
            c.set_nick(new_nick)
        self.conf["mute"]=not self.conf["mute"]

    def function_reload(self):
        """Reload tous les modules du bot. Prend en compte les modifications des sources et fichiers de configurations"""
        for k,v in self.modules.items():
            if v[0]==self:
                continue
            v[0].save()
        for k,v in self.modules.items():
            if v[0]==self:
                continue
            v[0].unload()
            reload(v[1])
        sys.modules=copy.copy(self.original_sys_modules)
        self.load()






