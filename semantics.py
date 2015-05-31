# -*- coding: utf8 -*-
from bot import BotModule
import re,random,os
from data import DataMarshal




class SemanticsModule(BotModule):
    """
    Le module charger de traduire chaque emssage texte en différentes sémantiques 
    abstraites.
    """
    SEM_RAW=0    # Un chat mange la pomme de Baboon
    SEM_CLEAN=1  # Un chat mange la pomme de #personne#
    SEM_GRAM=2   # #detindef# chat #present# manger #detdef# pomme #de# #personne#
    SEM_FNC=3
    SEM_CONSTR=4   # 
    SEM_THEME=5    # 

    def __init__(self,bot):
        BotModule.__init__(self,bot)
        self.sems={self.SEM_CLEAN: CleanSemantics(self)}
        #if not os.path.exists("./db/leff.dat"):
        #    f=open("./db/lefff-3.0.3.txt","r")
        #    self.racines={}
        #    self.orthographes={}
        #    self.cls=[]
        #    self.dets=[]
        #    for l in f.readlines():
        #        l=l.decode("latin-1").encode("utf8").strip()
        #        t=len(l.split())
        #        if t==8:
        #            n,_,typ,attributs,pred,__,genre_conj,mode=l.split()
        #        elif t==7:
        #            n,_,typ,attributs,pred,__,mode=l.split()
        #            genre_conj=""
        #        pred=pred.split("_")[0]
        #        if n in ["cf","cln"] or typ in ["cf",]:
        #            continue
        #        if pred in ["cln","cla","cld","clr"]:
        #            pred=n
        #        typ=typ.upper()
        #        attributs=attributs.split(",")
        #        key="%s:%s"%(pred,typ)
        #        if not self.orthographes.has_key(n):
        #            self.orthographes[n]=[]
        #        if not self.racines.has_key(key):
        #            self.racines[key]=[]
        #        if not (n,genre_conj,mode) in self.racines[key]:
        #            self.racines[key].append("%s:%s:%s"%(n,genre_conj,mode))
        #        if not key in self.orthographes[n]:
        #            self.orthographes[n].append(key)
        #        if typ=="CLN":
        #            self.cls.append((n,genre_conj,typ))
        #        elif typ=="DET":
        #            self.dets.append((n,genre_conj))
        #    f.close()
        #    dat={
        #            "dets":self.dets,"cls":self.cls,"racines":self.racines,"orthographes":self.orthographes
        #            }
        #    data=DataMarshal("db/leff.dat",dat)
        #    data.save()
        #else:
        #    dic=DataMarshal("db/leff.dat")
        #    self.orthographes=dic["orthographes"]
        #    self.racines=dic["racines"]
        #    self.dets=dic["dets"]
        #    self.cls=dic["cls"]

    def translate(self,raw_txt,author,spectators,thread,private):
        sem_id_src=self.SEM_RAW
        res={self.SEM_RAW:raw_txt}
        translated=True
        while translated:
            translated=False
            for sem_id,sem in self.sems.items():
                if sem.get_semantics_input()==sem_id_src:
                    res[sem_id]=sem.translate(res[sem_id_src],author,spectators,self.bot.name,thread,private)
                    if not res[sem_id]:
                        del res[sem_id]
                        break
                    sem_id_src=sem_id
                    translated=True
                    break
        return res

    def translate_back(self,sem_id,txt,author,spectators,thread,private):
        res={sem_id:txt}
        while sem_id!=self.SEM_RAW:
            txt=self.sems[sem_id].translate_back(txt,author,spectators,self.bot.name,thread,private)
            sem_id=self.sems[sem_id].get_semantics_input()
            res[sem_id]=txt
        return res

    def preprocess_rule_match(self,sem_id,match):
        if sem_id==self.SEM_RAW:
            return match
        else:
            return self.sems[sem_id].preprocess_rule_match(match)

    def preprocess_rule_action(self,sem_id,action):
        if sem_id==self.SEM_RAW:
            return action
        else:
            return self.sems[sem_id].preprocess_rule_action(action)

    def help_content(self):
        s="<h4>Sémantiques supportées:</h4>"
        s+="""
        <table><tr><th>Id</th><th>Nom</th><th>Description</th><th>Exemple</th></tr>
        <tr><td>RAW</td><td>Sémantique brute</td><td>Le message original, tel que reçu par le bot</td><td><i>Un chat mange la pomme de Baboon !</i></td></tr>
        <tr><td>CLEAN</td><td>Sémantique nettoyée</td><td>Le message original, sans la ponctuation, avec identification des smileys et nicks</td><td><i>un chat mange la pomme de #personne#</i></td></tr>
        <tr><td>GRAM</td><td>Abstrait grammaire et conjgaison</td><td>Le message original, sans toutes les variations liées à la grammaire ou à la conjugaison</td><td><i>#detindef# chat #present# manger #detdef# pomme #de# #personne#</i></td></tr>
        </table>
        Plus de sémantiques à venir!
        """
        return s


   
        

class Semantics:

    def __init__(self,semmodule):
        self.sem=semmodule

    def get_semantics_id(self):
        pass

    def get_semantics_input(self):
        pass

    def translate(self,txt,author,spectators,botname,thread,private):
        raise ValueError("Semantics not supported")

    def translate_back(self,txt,author,spectators,botname,thread,private):
        raise ValueError("Semantics not supported")

    def preprocess_rule_match(self,match_string):
        raise ValueError("Semantics not supported")

    def preprocess_rule_action(self,action_string):
        raise ValueError("Semantics not supported")



#**************************************************************************
#
# Clean semantics
#
#**************************************************************************

accents={
        u"é":u"e",
        u"è":u"e",
        u"ê":u"e",
        u"ë":u"e",
        u"ç":u"c",
        u"ä":u"a",
        u"à":u"a",
        u"â":u"a",
        u"ù":u"u",
        u"û":u"u",
        u"ü":u"u",
        u"ï":u"i",
        u"î":u"i",
        u"ô":u"o",
}
ligatures="qu|quelqu|[ltdmjcsn]"
smileys=":d :p :P :) :] :D :s :> :( :[ :< :* :s ;) ;( ;s ;> :') :)) TT -_- ^^ 8D 8) 8p 8P oO :DD <3".split()

re_ponctuation=re.compile(u"[%s]" % re.escape(u"&\"'(-_)=~{[|\\^@]}+¨$%*!:;,./<>"))
re_question=re.compile(r"\?")
re_smileys=re.compile("|".join(map(re.escape,smileys)))
re_c=re.compile(r"\bc ")
re_nombre=re.compile(r" \d+ ")
re_url=re.compile(r'(https?|ftp|file|irc)://[\w\d:#@%/;$()~_?+-=.&]*')
re_ligature=re.compile('\\b(%s)\\\''%ligatures)
re_ale=re.compile(r'\bau\b')
re_ales=re.compile(r'\baux\b')
re_dele=re.compile(r'\bdu\b')
re_cet=re.compile(r'\bcet\b')

re_ligature_back=re.compile('\\b(%s)(e) ([aeiou])'%ligatures)
re_others_back=re.compile(r'#\w+#')
re_personne_back=re.compile(r'#personne#')
re_nombre_back=re.compile(r'#nombre#')
re_smiley_back=re.compile(r'#smiley#')
re_smiley_back2=re.compile(r'\bp\b|\bx\b')
re_dele_back=re.compile(r'\bde le\b')
re_ale_back=re.compile(r'\bà le\b')
re_ales_back=re.compile(r'\ba les\b')
re_cet_back=re.compile(r'\bce ([haeiou])\b')

class CleanSemantics(Semantics): 

    def get_semantics_id(self):
        return SemanticsModule.SEM_CLEAN

    def get_semantics_input(self):
        return SemanticsModule.SEM_RAW

    def preprocess_rule_match(self,match_string):
        return match_string

    def preprocess_rule_action(self,action_string):
        return action_string

    def translate(self,txt,author,spectators,botname,thread,private):
        if txt.startswith("!"):
            return None
        #return txt #TODO
        txt=re_question.sub(" ? ",txt)
        txt=re.sub("\\b%s\\b"%botname,"",txt)
        txt=re_url.sub(' #url# ',txt)
        txt=re_c.sub('ce est ',txt)
        txt=re_ale.sub('à le',txt)
        txt=re_ales.sub('à les',txt)
        txt=re_dele.sub('de le',txt)
        txt=re_cet.sub('ce',txt)
        txt=re_nombre.sub(' #nombre# ',txt)
        txt=re_smileys.sub(' #smiley# ',txt)
        txt=txt.lower()
        txt=re_ligature.sub(r'\1e ',txt)
        txt=re.sub("\\b%s\\b"%"|".join(map(lambda x: re.escape(x.lower()),spectators))," #personne# ",txt)
        txt=txt.decode("utf8")
        txt=re_ponctuation.sub(' ',txt)
        txt=list(txt)
        for i in range(len(txt)):
            if accents.has_key(txt[i]):
                txt[i]=accents[txt[i]]
        txt="".join(txt).encode("utf8")
        txt=" ".join(map(str.strip,txt.split()))
        return txt

    def translate_back(self,txt,author,spectators,botname,thread,private):
        txt=re_ligature_back.sub(r"\1'\3",txt)
        txt=txt.replace(botname,"")
        if random.randint(0,5)==0:
            spects=spectators
        else:
            spects=[author]
        txt=re_personne_back.sub(random.choice(spects),txt)
        txt=re_nombre_back.sub(str(random.randint(0,100)),txt)
        txt=re_smiley_back2.sub("#smiley#",txt)     #fix an old bug where smileys were wrongly parsed (: removed)
        txt=re_smiley_back.sub(random.choice(smileys),txt)
        txt=re_others_back.sub("",txt)
        txt=re_dele_back.sub("du",txt)
        txt=re_ale_back.sub("au",txt)
        txt=re_ales_back.sub("aux",txt)
        txt=re_cet_back.sub("cet \1",txt)

        if txt[-3:] in [" je"," de"]:
            txt=txt[:-3]
        return txt
        

#**************************************************************************
#
# Gram semantics
#
#**************************************************************************



erreur_courantes={
"mais":"COO",
"ne":"CLNEG",
"pas":"ADVNEG",
}

nats_to_ignore=["CLNEG"]


class GramSemantics(Semantics): 

    def __init__(self,semmodule):
       Semantics.__init__(self,semmodule)

    def get_semantics_id(self):
        return SemanticsModule.SEM_GRAM

    def get_semantics_input(self):
        return SemanticsModule.SEM_CLEAN

    def preprocess_rule_match(self,match_string):
        return match_string

    def preprocess_rule_action(self,action_string):
        return action_string

    def __lookup(self,mot):
        res=[]
        if self.sem.orthographes.has_key(mot):
            for c in self.sem.orthographes[mot]:
                res.append(tuple(c.split(":")))
        return res

    def __get_masculin(self,mot,default=None,typ="NC"):
        key="%s:%s"%(mot,typ)
        if not self.sem.racines.has_key(key):
            return mot
        for ortho in self.sem.racines[key]:
            n,genre_conj,mode=ortho.split(":")
            if genre_conj=="m" or genre_conj=="ms" or genre_conj=="s":
                return n
        return default

    def __get_feminin(self,mot,default=None,typ="NC"):
        key="%s:%s"%(mot,typ)
        if not self.sem.racines.has_key(key):
            return mot
        for ortho in self.sem.racines[key]:
            n,genre_conj,mode=ortho.split(":")
            if genre_conj=="f" or genre_conj=="fs" or genre_conj=="s":
                return n
        return default

    def __get_pluriel(self,mot,default=None,typ="NC",feminin=None):
        key="%s:%s"%(mot,typ)
        if not self.sem.racines.has_key(key):
            return mot
        if feminin is None:
            ok=["p","mp","fp"]
        elif feminin:
            ok=["p","fp"]
        else:
            ok=["p","mp"]
        for ortho in self.sem.racines[key]:
            n,genre_conj,mode=ortho.split(":")
            if genre_conj in ok:
                return n
        return default

    def __get_conjugaison(self,verbe,forme):
        key="%s:%s"%(verbe,"V")
        if not self.sem.racines.has_key(key):
            return verbe
        temps,nombre,plur=forme
        for ortho in self.sem.racines[key]:
            n,genre_conj,mode=ortho.split(":")
            if plur!=genre_conj[-1] or temps not in genre_conj or nombre not in genre_conj:
                continue
            return n
        return verbe


    def __get_random_racine(self,typ):
        if typ=="CLN":
            return random.choice(self.sem.cls)[0]
        elif typ=="DET":
            return random.choice(self.sem.dets)[0]
        else:
            l=filter(lambda x:x.endswith(":%s"%typ),self.sem.racines.keys())
            if not l:
                return ""
            return random.choice(l).split(":")[0]



    def __format_sujet(self,num):
        if num<3:
            num+=1
            lettre="s"
        else:
            num-=2
            lettre="p"
        return "%s%s"%(num,lettre)

    def __format_sujet_inv(self,s):
        if not s:
            return 2
        r=int(s[0])-1
        if s[1]=="p":
            r+=3
        return r

    def __format_genre(self,masc,fem,pl):
        if masc:
            r="m"
        else:
            r="f"
        if pl:
            r+="p"
        else:
            r+="s"
        return r


    def __choose_best_gram(self,sentence_splited,pos,choices,original_word):
        pos_verbs=[]
        pos_nouns=[]
        pos_advs=[]
        pos_adjs=[]
        pos_dets=[]
        pos_prons=[]
        contient_verbe=False
        i=0
        for m in sentence_splited:
            for w,t in m:
                if t=="NC":
                    pos_nouns.append(i)
                elif t=="V":
                    pos_verbs.append(i)
                elif t=="ADJ":
                    pos_adjs.append(i)
                elif t=="ADV":
                    pos_advs.append(i)
                elif t=="PREP":
                    pos_advs.append(i)
                elif t=="DET":
                    pos_dets.append(i)
                elif t.startswith("CL"):
                    pos_prons.append(i)
            i+=1
        natures=map(lambda x:x[1],choices)
        nat=""
        #regles de grammaire basiques
        w=sentence_splited[pos]
        #enleve les erreurs
        if "V" in natures and "ADJ" in natures:
            natures.remove("ADJ")
        if "ADJ" in natures and len(natures)>1 and not (pos-1 in pos_nouns or pos+1 in pos_nouns):
            natures.remove("ADJ")
        if "NC" in natures and len(natures)>1 and not (pos-1 in pos_adjs or pos-1 in pos_dets):
            natures.remove("NC")
        #trouve la bonne nature
        if erreur_courantes.has_key(choices[0][0]) and erreur_courantes[choices[0][0]] in natures :
            nat=erreur_courantes[choices[0][0]]
        elif original_word=="a" and "PREP" in natures and len(pos_verbs)>1 and pos-1 not in pos_prons :
            nat="PREP"
        elif "PRI" in natures and pos==0:
            nat="PRI"
        elif "NC" in natures and pos-1 in pos_dets:
            nat="NC"
        elif "CLN" in natures and pos==0:
            nat="CLN"
        elif "CLN" in natures and pos+1 in pos_verbs:
            nat=random.choice(filter(lambda x:x.startswith("CL"),natures))
        elif "V" in natures and (len(pos_verbs)==1 or pos-1 in pos_prons or pos+1 in pos_prons):
            nat="V"
        elif "PRI" in natures and (pos+1 in pos_verbs):
            nat="PRI"
        elif "DET" in natures and (pos+1 in pos_nouns or len(choices[0][0])<=3):
            nat="DET"
        elif "NC" in natures and pos+1 in pos_adjs:
            nat="NC"
        elif "ADJ" in natures and (pos-1 in pos_nouns or pos+1 in pos_nouns):
            nat="ADJ"
        elif "PREP" in natures and (pos-1 in pos_verbs or pos+1 in pos_dets):
            nat="PREP"
        choices=filter(lambda x:x[1] in natures,choices)
        if nat:
            contient_verbe=contient_verbe or nat=="V"
            try:
                c=filter(lambda x: x[1]==nat,choices)[0][0]
            except:
                print "********************",nat,choices
            return (c,nat)
        return random.choice(choices)

    def translate(self,txt,author,spectators,botname,thread,private):
        txt=txt.split()
        res=[]
        tmp_res=[]
        for mot in txt:
            matchs=[]
            if mot[0]=="#" and mot[-1]=="#":
                #mots speciaux de la semantique precedentes
                if mot=="#nombre#":
                    matchs=[("nombre","DET")]
            else:
                #mots ordinaires
                matchs=self.__lookup(mot)
            if not matchs:
                r=[(mot,"")]
            else:
                r=matchs
            tmp_res.append(r)
        #PRON DATIF
        i=1
        contient_a=None
        while i<len(tmp_res):
            for j in range(len(tmp_res[i])):
                w,t=tmp_res[i][j]
                if w=="a":
                    contient_a=i
                elif t=="CLD" and contient_a is not None and contient_a==i-1:
                    tmp_res[i][j]=(w,"CLD")
                    del tmp_res[contient_a]
                    contient_a=None
                    break
            i+=1
        #ambiguites
        i=0
        for poss in tmp_res:
            if len(poss)==1:
                m,nat=poss[0]
            else:
                m,nat=self.__choose_best_gram(tmp_res,i,poss,txt[i])
            tmp_res[i]=[(m,nat)]
            i+=1
        #temps composés
        i=1
        contient_auxiliaire=None
        while i<len(tmp_res):
            for w,t in tmp_res[i]:
                if t=="V" and (w=="avoir" or w=="etre"):
                    contient_auxiliaire=i
                elif t=="V" and (contient_auxiliaire==i-1 or contient_auxiliaire==i-2 or contient_auxiliaire==i-3):
                    del tmp_res[contient_auxiliaire]
                    contient_auxiliaire=None
                    break
            i+=1
        #construction    
        for elem in tmp_res:
            m,nat=elem[0]
            if nat:
                res.append("#%s:%s#"%(m,nat))
            else:
                res.append(m)
        return " ".join(res)



    def translate_back(self,txt,author,spectators,botname,thread,private):
        def accorde(res,a_accorder,choix_feminin,choix_pluriel):
            choix_masculin=not choix_feminin and not choix_pluriel
            if choix_feminin is None:
                choix_feminin=False
            for pos in a_accorder:
                ow,ot=res[pos]
                if ot=="ADJ" or ot=="NC":
                    if choix_masculin and not choix_pluriel:
                        ow=self.__get_masculin(ow,ow,ot)
                    elif choix_feminin and not choix_pluriel:
                        ow=self.__get_feminin(ow,ow,ot)
                    elif choix_pluriel:
                        ow=self.__get_pluriel(ow,ow,ot,choix_feminin)
                    res[pos]=ow
                elif ot=="DET":
                    if ow=="nombre":
                        res[pos]="#nombre#"
                        choix_pluriel=True
                    else:
                        genre=self.__format_genre(choix_masculin,choix_feminin,choix_pluriel)
                        poss=[]
                        for det in self.sem.dets:
                            n,g=det
                            genre_ok=not choix_pluriel and g=="s" or choix_pluriel and g=="p" or g==genre
                            if genre_ok and n==ow:
                                poss=[n]
                                break
                            elif genre_ok:
                                poss.append(n)
                        if not poss:
                            poss=[""]
                        res[pos]=random.choice(poss)
                else:
                    assert(False)
        txt=txt.split()
        choix_sujet=2
        choix_feminin=None
        choix_masculin=None
        choix_temps=None
        choix_pluriel=None
        res=[]
        a_accorder=[]
        #Accord noms et adjs et conjugue les verbes
        for i in range(len(txt)):
            if txt[i][0]=="#" and txt[i][-1]=="#" and ":" in txt[i]:
                w,t=txt[i][1:-1].split(":")
                #remplit les trous au hasard
                if not w:
                    w=self.__get_random_racine(t)
                #On accorde les precedents
                if t=="DET" or t not in ["ADJ","NC"]:
                    accorde(res,a_accorder,choix_feminin,choix_pluriel)
                    a_accorder=[]
                if t=="T":
                    #choix du temps
                    choix_temps=w
                elif t=="CLN":
                    key="%s:CLN"%w
                    rac=self.sem.racines[key]
                    suj=2
                    for o in rac:
                        n,genre_conj,mode=o.split(":")
                        if n==w:
                            suj=genre_conj
                            break   
                    choix_sujet=self.__format_sujet_inv(suj)
                    res.append(w)
                elif t=="V":
                    if choix_temps is None:
                        choix_temps=random.choice(["P"])
                    if i and (txt[i-1] in ["pour","de"] or txt[i-1].endswith(":V#")):
                        choix_temps="W"
                    key_temps="%s%s"%(choix_temps,self.__format_sujet(choix_sujet))
                    if choix_temps.startswith("Km"):
                        res.append(self.__get_conjugaison("avoir","P%s"%key_temps[1:]))
                        res.append(self.__get_conjugaison(w,"K"))
                    elif choix_temps=="W":
                        res.append(w)
                    else:
                        res.append(self.__get_conjugaison(w,key_temps))
                elif t=="DET":
                    #On accordera plus tard
                    a_accorder.append(len(res))
                    res.append((w,t))
                elif t=="ADJ":
                    #On accordera plus tard
                    a_accorder.append(len(res))
                    res.append((w,t))
                elif t=="NC":
                    #Noms
                    masculin=self.__get_masculin(w)
                    feminin=self.__get_feminin(w)
                    pluriel=self.__get_pluriel(w)
                    #Choisit un nombre et genre au hasard
                    choix_feminin=(not masculin or random.randint(0,2)==0) and feminin
                    choix_pluriel=random.randint(0,4)==0 and pluriel
                    choix_sujet=2
                    if choix_pluriel:
                        choix_sujet=5
                    a_accorder.append(len(res))
                    res.append((w,t))
                else:
                    #cas par defaut
                    res.append(w)
            else:
                res.append(txt[i])
        if a_accorder:
            accorde(res,a_accorder,choix_feminin,choix_pluriel)
        return " ".join(res)





#**************************************************************************
#
# Fnc semantics
#
#**************************************************************************

gram_to_keep=frozenset(["NC","V","PREP","CLN","CLD","PRO","CLM"])

class FonctionSemantics(Semantics): 

    def get_semantics_id(self):
        return SemanticsModule.SEM_FNC

    def get_semantics_input(self):
        return SemanticsModule.SEM_GRAM

    def preprocess_rule_match(self,match_string):
        return match_string

    def preprocess_rule_action(self,action_string):
        return action_string

    def translate(self,txt,author,spectators,botname,thread,private):
        if txt.startswith("!"):
            return None
        txt=txt.split()
        #keep only lat prep
        verbe_vu=False
        sujet_vu=False
        res=[]
        for i in range(len(txt)-1,-1,-1):
            t=txt[i]
            if t[0]=="#" and t[-1]=="#" and ":" in t:
                m,nat=t[1:-1].split(":")
            else:
                continue
            if not sujet_vu:
                if (not verbe_vu) or nat!="V":
                    if i>=len(txt)-1 or not txt[i+1].endswith(":%s#"%nat):
                        res.insert(0,t)
            verbe_vu=verbe_vu or nat=="V"
            sujet_vu=sujet_vu or (verbe_vu and nat in ["NC","CLN"])
        txt=res
        #keep only: GN, V, preps
        res=[]
        for t in txt:
            if t[0]=="#" and t[-1]=="#" and ":" in t:
                m,nat=t[1:-1].split(":")
            else:
                m=t
                nat=""
            if nat=="" or nat in gram_to_keep:
                res.append(t)
        return " ".join(res)

    def translate_back(self,txt,author,spectators,botname,thread,private):
        txt=txt.split()
        res=[]
        sujet=False
        verbe=False
        cod=False
        for t in txt:
            if t[0]=="#" and t[-1]=="#" and ":" in t:
                m,nat=t[1:-1].split(":")
            else:
                m=t
                nat=""
            if nat=="NC":
                res.append("#:DET#")
                res.append(t)
                if random.randint(0,1)==0:
                    res.append("#:ADJ#")
            elif nat=="V":
                res.append(t)
                if random.randint(0,6)==0:
                    res.append("#:ADV#")
            else:
                res.append(t)
        return " ".join(res)
