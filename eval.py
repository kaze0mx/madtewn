# -*- coding: utf8 -*-
from bot import BotModule
import data
import os,cgi
import random
from data import Code
import inspect


ALLOWED_BUILTINS={
"__builtins__":None,
"True":True,
"False":False,
"map":map,
"filter":filter,
"set":set,
"zip":zip,
"str":str,
"int":int,
"dict":dict,
"set":set,
"list":list,
"tuple":tuple,
"len":len,
"range":range,
"hex":hex,
"bin":bin,
"chr":chr,
"ord":ord,
"unicode":unicode,
"rnd":random.choice,
"repr":repr,
"random":random,
"RAW":0,
"CLEAN":1,
"GRAM":2,
"FNC":3,
}




class EvalModule(BotModule):
    """
    Ce module est chargé de l'exécution de code python à l'intérieur des règles. La 
    fonction principale a cet égard est la function eval(&lt;python code&gt;). Ce module 
    tient également à jour un dictionnaire de valeurs, sauvegardé automatiquement, et
    accessible au sein des actions des règles.
    """

    def __init__(self,bot):
        BotModule.__init__(self,bot)
        self.dico=data.DataConf("%s/dico.py" % self.bot.data_dir)
        for v in self.dico.values():
            if isinstance(v,Code):
                v.dicofun=self.get_dico
                


    def get_dico(self):
        d={}
        d.update(ALLOWED_BUILTINS)
        d.update(self.dico)
        d.update(self.bot.functions)
        return d

    def function_eval(self,expr,dico={},dico_sup={}):
        """
        (code,dic,dic)
        Evalue une expression python, retourne le resultat. Vous pouvez utiliser le raccourci "!p" également.
        """
        if not dico:
            dico=self.get_dico()
        dico.update(dico_sup)
        if type(expr)==str and expr.startswith("lambda "):
            return Code(expr,self.get_dico)
        elif isinstance(expr,Code):
            expr=expr.source
        if "__" in expr:
            raise ValueError("Unsafe code")
        try:
            for sexpr in ssplit(expr,";"):
                res=eval(sexpr,dico,{})
                dico.update(self.dico)
            return res
        except Exception,e:
            return ValueError("Error while evaluating %s: %s" % (repr(expr),str(e)))


    def function_assign(self,key,value):
        """
        (str,py)
        Assigne une valeur à une variable du dictionnaire de valeurs. Un raccourci, sous forme de règle, existe: !key=value.
        Retourne la nouvelle valeur.
        """
        self.dico[key]=value
        return value

    def function_get(self,key,default_value=0):
        """
        (str,py)
        Retourne la valeur d'une variable du dictionnaire de valeurs, retoure default_value si elle n'existe pas. Un raccourci, sous forme de règle, existe: !p value.
        Retourne la nouvelle valeur.
        """
        if not self.dico.has_key(key):
            self.dico[key]=default_value
        return self.dico[key]

    def function_call_format(self,fun_name,arguments_string):
        """
        (str,str)
        Appèle la fonction <fun_name> avec les arguments <arguments_string>. <argument_string> est
        une chaîne python representant une liste d'arguments python, séparés par une virgule, pour la fonction 
        <fun_name>. Une validation et un formattage des arguments a lieu.
        Example:
        calls("ma_func","'toto',5+6,lambda x:45") -> mafunc("toto",11,<code object>)
        """
        return self.function_eval("%s(*parse_args(%s,%s))" % (fun_name,repr(fun_name),repr(arguments_string)))
        

    def function_parse_args(self,fun_name,string):
        """
        (str,str)
        Parse une chapine représentant une liste d'arguments python pour la fonction 
        <fun_name> et retourne une liste python de valeurs formattées.
        Exemple:
        parse_args("ma_func","'toto',5+6,lambda x:45") -> ["toto",11,<code object>]
        """
        name,fn,types,doc,proto=self.bot.get_prototype_function(fun_name)
        args=ssplit(string,",")
        dic=self.get_dico()
        largs, varargs, varkw, defaults = inspect.getargspec(fn)
        if varargs is None:
            varargs=[]
        if varkw is None:
            varkw=[]
        if defaults is None:
            defaults=[]
        minargs=len(largs)-1-len(defaults)
        maxargs=len(largs)-1+len(varargs)+len(varkw)
        if len(args)<minargs or len(args)>maxargs:
            raise ValueError("%s requires between %d and %d arguments, %d given" % (name,minargs,maxargs,len(args)))
        if types:
            #Formatting args
            for i in range(len(args)):
                if types[i]=="str":
                    try:
                        tt=self.function_eval(args[i],dic)
                        if not type(tt)==str:
                            args[i]=str(tt)
                        else:
                            args[i]=tt
                    except:
                        #Helper function for strings: we may omit "" or ''
                        args[i]=str(args[i])
                elif types[i]=="code":
                    #Do not evaluate code objects, they are lazy evaluated!
                    args[i]=Code(args[i],self.get_dico) 
                else:
                    args[i]=self.function_eval(args[i],dic)
            #Verify typing
            for i in range(len(args)):
                if (types[i]=="code" and not isinstance(args[i],Code)) or (types[i]!="code" and types[i]!="py" and type(args[i]).__name__!=types[i]):
                    raise ValueError("%s %dth argument must be of type %s, got %s instead" % (name,i+1,types[i],type(args[i]).__name__))
        else:
            for i in range(len(args)):
                args[i]=self.function_eval(args[i],dic)
        return args
                
    def help_content(self):
        s="<h4>Variables du dictionnaire, accessible depuis les actioons des règles:</h4>"
        s+="<table border='1'><tr><th>Nom</th><th>Valeur</th></tr>"
        for k,v in self.get_dico().items():
            if not str(v).startswith("<bound method"):
                s+="<tr><td><b>%s</b></td><td>%s</td></tr>" % (k,cgi.escape(str(v)))
        s+="</table>"
        return s

            

                    


        
        
        


#===============================================================================
#
#   Fonctions utilitaires 
#
#===============================================================================



def ssplit(txt,separators):
    """
    Split a python string, considering only level0 separators
    """
    stack=[]
    res=[]
    cur=[]
    escaped=False
    for c in txt:
        if c in separators and not stack:
            res.append("".join(cur))
            cur=[]
        else:
            cur.append(c)
        if c in "\"'" and not escaped:
            if not stack or stack[-1] not in "\"'":
                stack.append(c)
            elif stack[-1]==c:
                stack.pop()
        elif c in "[({" and (not stack or stack[-1] not in "\"'"):
            stack.append(c)
        elif c in "])}" and (not stack or stack[-1] not in "\"'"):
            if not stack:
                raise ValueError
            if c==")" and stack[-1]!="(" or c=="]" and stack[-1]!="[" or  c=="{" and stack[-1]!="}":
                raise ValueError
            stack.pop()
        escaped=stack and c=="\\" and stack[-1] in "\"'"
    if stack:
        raise ValueError
    if cur:
        res.append("".join(cur))
    return res














