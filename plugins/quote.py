# -*- coding: utf8 -*-
import sys,random,re,cgi
sys.path.append("../")
from bot import BotModule
import data



class QuoteModule(BotModule):
    """
    Module pour l'enregistrement des quotes.
    """
    def __init__(self,bot):
        BotModule.__init__(self,bot)
        self.quotes=data.DataConf("%s/quotes.py" % self.bot.data_dir)
        self.r=re.compile(r"(<\w+>)")


    def function_quote_add(self,quote):
        """
        (str)
        Ajoute une quote à la base de quotes.
        """
        for i in range(len(self.quotes.keys())+2):
            if not i in self.quotes.keys():
                break
        quote=self.r.sub("\n\\1",quote)
        if quote[0]=="\n":
            quote=quote[1:]
        self.quotes[i]=quote

    def function_quote_rnd(self):
        """
        Retourne une quote au hasard.
        """
        return random.choice(self.quotes.values())


    def help_content(self):
        s="<h4>Quôtes enregistrées:</h4>"
        s+="<table border='1'><tr><th>Id</th><th>Quote</th></tr>"
        for k,v in self.quotes.items():
            s+="<tr><td><b>%s</b></td><td>%s</td></tr>" % (k,cgi.escape(str(v)).replace("\n","<br/>"))
        s+="</table>"
        return s



