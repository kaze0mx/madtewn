# -*- coding: utf8 -*-
from bot import BotModule
import os,re,random,threading,time
import data
from data import Code
import cgi

NB_GROUPS=3


default_rules= { 
        0 : (0, 100, '^!$1={[a-zA-Z][a-zA-Z0-9_]*}[ ]*=$2={.*}$', Code('assign(arg1,eval(arg2))')),
        1 : (0, 100, '^!p $1={.*}$', Code('eval(arg1)')),
        2 : (0, 100, '^!help', Code("'RTFM: http://localhost:5555'")),
        3 : (0, 100, '^!$1={[a-zA-Z][a-zA-Z0-9_]*}[ ]*$2={.*}$', Code('call_format(arg1,arg2)')),
}

class InteractiveModule(BotModule):
    """
    C'est le module de règles, dont le rôle est de faire réponde quelque chose au bot.
    La fonction la plus importe est:
    <pre>!learn <i>sem</i>,<i>prio</i>,<i>regexp</i>,<i>code action</i></pre>
    Paramètres: <ul><li><i>sem</i> in (RAW,CLEAN)</li><li> 0&lt;=<i>prio</i>&lt;=100</li><li> <i>match</i> est une expression  régulière, qui peut contenir des sous-groupes de la forme '$1={&lt;regexp sous-groupe&gt;}'</li><li> <i>action</i> est du code python
        évalué à l'exécution de la règle.</li></ul>
        Cette action défini une règle, sur la sémantique <i>sem</i>. Elle sera exécutée uniquement si l'expression régulière <i>regexp</i> match sur le message, dans la bonne sémantique. Elle aura alors une chance de s'exécuter, en fonction de sa <i>prio</i>. Si <i>prio</i> vaut 100, alors la règle sera toujours choisie, sauf si d'autres règles de <i>prio</i> 100 existent auquel cas le choix est aléatoire. Si <i>prio</i> vaut 0, cette règle ne sera choisie que si aucune autre règle de <i>prio</i> supérieur n'a été choisie. Pour les autres valeurs de <i>prio</i> (de 1 à 99) la règle est choisie en fonction de sa <i>prio</i>, le plus grand, plus grand est la chance. <br/>
        Si la règle a été choisie, son action est alors exécutée (cf. module <a href="#EvalModule">EvalModule</a>). Une règle a accès: 
        <ul><li>aux variables du dictionnaires</li>
        <li> à l'ensemble des fonctions du bot</li>
        <li> aux variables arg1...argn qui sont des chaînes correspondant au match des sous-groupes $1...$n</li>
        <li> aux variables nick (nick de celui qui a parlé) et spectators (liste de eprsonnes sur le chan)</li></ul>
    """

    def __init__(self,bot):
        BotModule.__init__(self,bot)
        self.rules=data.DataConf("%s/rules.py" % self.bot.data_dir,default_rules)
        self.compiled_rules={}
        for id,rule in self.rules.items():
            self.compiled_rules[id]=self.precompile_rule(rule)
        self.interet=1.0
        self.inconscient=Inconscient(self,5)
        self.inconscient.start()




    def precompile_rule(self,rule):
        sem,prio,match,action=rule
        assert type(match)==str and isinstance(action,Code) and type(prio)==int and prio>=0 and prio<=100
        for i in range(1,NB_GROUPS+1):
            r=re.compile("\\$%i=\\{(?P<toto>[^\\}]*)\\}" % i)
            match=r.sub("(?P<g%i>\g<toto>)" % i,match)
            match=match.replace("$%i"%i,'(?P<g%i>\w*)' % i)
        regexp=re.compile(match, re.IGNORECASE)
        return regexp


    

    def response(self,transduced,author,spectators,thread,private,extra_dic={}):
        regles_qui_matchent=[]
        regles_de_100=[]
        regles_de_0=[]
        if private:
            self.interet=1
        #On garde les regles qui matchent
        for rule_id,rule in self.rules.items(): 
            sem,prio,match,action=rule
            if type(sem)==tuple:
                sem_in,sem_out=sem
            else:
                sem_in=sem
                sem_out=sem
            regexp=self.compiled_rules[rule_id]
            if not transduced.has_key(sem_in):
                break
            match=regexp.search(transduced[sem_in])
            if match:
                if prio==100:
                    regles_de_100.append((sem_out,prio,action,match))
                elif prio==0:
                    regles_de_0.append((sem_out,prio,action,match))
                else:
                    regles_qui_matchent.append((sem_out,prio,action,match))
        if regles_de_100:
            #Si des regles ont une prio de 100, alors on en choisit la première 
            #peu importe la pertinence
            regle=regles_de_100[0]
        elif regles_qui_matchent:
            #Sinon, choix d'une regle parmi les autres regles
            somme_prios=sum(map(lambda x:x[1],regles_qui_matchent))
            tirage=random.random()*somme_prios
            for sem,prio,action,match in regles_qui_matchent:
                if prio>=tirage:
                    regle=(sem,prio,action,match)
                    break
                tirage-=prio
        elif regles_de_0:
            regle=random.choice(regles_de_0)
        else:
            regle=None
        reponse=""
        if regle:
            sem,prio,action,match=regle
            je_parlerai=private or regles_de_100 or (random.randint(0,99) <= prio and random.random()<=self.interet)
            if je_parlerai:
                #Mappe les match_groups pour qu'ils soient accessibles depuis la reponse de la regle
                dico_sup={"nick":author,"spectators":spectators}
                dico_sup.update(extra_dic)
                for i in range(1,NB_GROUPS+1):
                    try:
                        dico_sup["arg%i" % i]=match.group("g%i" % i)      
                    except: pass
                #Evalue la reponse
                reponse=self.bot.evaluator.function_eval(action,dico_sup=dico_sup)
                if reponse:
                    reponse=str(reponse)
        else:
            je_parlerai=False
        if reponse!="":
            self.interet+=0.1
        else:
            self.interet-=0.01
        if self.interet>1:
            self.interet=1
        if self.interet <0.1:
            self.interet=0.1
        if je_parlerai:
            return (sem,reponse)
        return None


    def sur_etat(self):      
        """Function called every x seconds"""
        self.interet-=.03
        if self.interet<=0.1:
            self.interet=0.1;
        return       

    def unload(self):
        self.inconscient.goon=False
        self.inconscient._Thread__stop()


    def function_learn(self,sem,prio,match,action):
        """
        (py,int,str,code)
        Ajoute une nouvelle règle à la liste de règles. 
        Paramètres: <i>sem</i> in (RAW,CLEAN), 0&lt;=<i>prio</i>&lt;=100, <i>match</i> 
        est une expression  régulière, qui peut contenir des sous-groupes de la 
        forme '$1={&lt;regexp sous-groupe&gt;}', <i>action</i> est du code python
        évalué à l'exécution de la règle.
        Une règle a accès: 
        <ul><li>aux variables du dictionnaires</li>
        <li> à l'ensemble des fonctions du bot</li>
        <li> aux variables arg1...argn qui sont des chaînes correspondant au match des sous-groupes $1...$n</li>
        <li> aux variables nick (nick de celui qui a parlé) et spectators (liste de eprsonnes sur le chan)</li></ul>
        Retourne l'id de la règle.
        """
        for i in range(len(self.rules.keys())+2):
            if not i in self.rules.keys():
                break
        match=self.bot.semantics.preprocess_rule_match(sem,match)
        action=self.bot.semantics.preprocess_rule_action(sem,action)
        self.rules[i]=(sem,prio,match,action)
        self.compiled_rules[i]=self.precompile_rule(self.rules[i])
        return i


    def function_unlearn(self,rule_id):
        """
        (int)
        Supprime la règle <rule_id>
        """
        if not rule_id in self.rules.keys():
            raise ValueError("No rule of id %s"% rule_id)
        del self.rules[rule_id]
        del self.compiled_rules[rule_id]

    def function_rule_get(self,rule_id):
        """
        (int)
        Retourne la règle <rule_id>
        """
        return self.rules[rule_id]


    def function_rule_changeprio(self,rule_id,new_prio):
        """
        (int,int)
        Modifie la priorité de la règle <rule_id>"""
        sem,prio,match,action=self.rules[rule_id]
        self.rules[rule_id]=(sem,new_prio,match,action)

    def function_rule_changematch(self,rule_id,new_match):
        """
        (int,str)
        Modifiy la regexp de la règle <rule_id>"""
        sem,prio,match,action=self.rules[rule_id]
        new_match=match=self.bot.semantics.preprocess_rule_match(sem,new_match)
        self.rules[rule_id]=(sem,prio,new_match,action)
        self.compiled_rules[rule_id]=self.precompile_(self.rules[rule_id])

    def function_rule_changeaction(self,rule_id,new_action):
        """
        (int,code)
        Modifie l'action de la règle <rule_id>"""
        sem,prio,match,action=self.rules[rule_id]
        new_action=self.bot.semantics.preprocess_rule_action(sem,new_action)
        self.rules[rule_id]=(sem,prio,match,new_action)

    def help_content(self):
        s="<h4>Règles mémorisées:</h4>"
        s+="<table border='1'><tr><th>Id</th><th>Sem</th><th>Priority</th><th>Match</th><th>Action</th></tr>"
        sem_pp={0:"RAW",1:"CLEAN",2:"GRAM"}
        for k,v in self.rules.items():
            sem,prio,match,action=v
            s+="<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (k,sem_pp[sem],prio,cgi.escape(repr(match)),cgi.escape(action.source))
        s+="</table>"
        return s


   
class Inconscient(threading.Thread):
    def __init__(self,ia,temps):
        threading.Thread.__init__(self)
        self.temps=temps
        self.ia=ia
        self.goon=True
        
    def run(self):
        while self.goon:            
            time.sleep(self.temps)
            try:
                self.ia.sur_etat()
            except:
                pass        
