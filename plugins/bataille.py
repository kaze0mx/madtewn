# -*- coding: utf8 -*-
import sys,random,re,cgi
from collections import namedtuple
sys.path.append("../")
from bot import BotModule
import data

TAILLE = 10
BATEAUX={
        "P":5,
        "C":4,
        "T":3,
        "M":3,
        "L":2,
}
NOMS_BATEAUX={
        "P":"Porte-avion",
        "C":"Croiseur",
        "T":"Contre-torpilleur",
        "M":"Sous-marin",
        "L":"Torpilleur",
}


LETTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:TAILLE+1]

ALEAU = ["Touche ... nan completement rate en fait", "Nope", "Que dalle", "T'as besoin d'aide ?", "PAS DU TOUT", "hahaha", "Bien tente", "J'espere que tu pisses mieux", "Non", "Trop pas", "A l'eau","hihi","mouhahahaha","pffrrrt","plouf", "je vais t'appeler 'le sniper'","Je crois que t'as eu un poisson","Nan mais jette directement tes missiles ca ira plus vite","Et si t'essayais avec plus gros","Et pan la mouette","T'as bien tue le vent","Tu entends ce bruit ? Nan ? bah c'est normal","Je vais t'acheter 'Comment viser pour les nuls'"]
TOUCHE = ["Mon %s !!", "Encule touche pas a mon %s","Batard laisse mon %s tranquille", "Laisse mon %s en paix 'culeeee", "Touche mon %s encore une fois et je tue ta famille", "Refais pas ca, mon %s est fragile","C'etait pas mon %s nonon c'etait .. heu .. un bateau en plastique","Tu l'aimes pas mon %s hein ?"]
COULE = ["C'etait un fier %s ...","C'etait mon %s, tu me dois 100K euros","J'en ai un autre de %s de toute facon","Coule mon %s :(","ENCULLLE MON %s","T'as casse mon %s :(((","Nique moi encore un %s et j'appelle mon pote Kim Jong","Il m'avait pas coute trop cher mon %s de toute facon", "C'est bien t'as nique un vieux %s tout pourri bravo"]
DEJAJOUE = ["T'as deja joue ca connard", "Alzeihmer te guette","HAHAHAHA deja joue","Tu te repettes mec"]
GAGNE = ["Et en plus t'as gagne connard","GG gros encule","Ouaiiis, t'as gagne au jeu de merde","Putain t'en a mis du temps pour battre un bot","Ouaiiis on a un gros winner","and the winner is .. gros trou de balle","Je te parle plus FDP j'aime pas perde"]

MOITOUCHE = ["Et je t'ai touche ton %s haha", "Et pan dans ton %s", "Direct dans ton %s", "BIM sur ton %s"]
MOICOULE = ["Et je t'ai coule ton %s haha", "%s kaputt ja ja", "'Arrrrgh' fais ton %s", "T'y tenais pas a ton %s j'espere"]
MOIGAGNE = ["I WIIIIIIN", "I am the best","J'ai gagneeeeee","Moi >> toi"]

def rpos():
    return (random.randint(1,TAILLE-1),random.randint(1,TAILLE-1))

def cpos(pos):
    l,c=pos
    r=[]
    if l>0:
        r.append((l-1,c))
    if l<TAILLE-1:
        r.append((l+1,c))
    if c>0:
        r.append((l,c-1))
    if c<TAILLE-1:
        r.append((l,c+1))
    return random.choice(r)

def rline(size):
    l1=random.randint(0,TAILLE-1)
    l2=l1
    c1=random.randint(0,TAILLE-1-size)
    c2=c1+size-1
    if random.randint(0,1):
        c1,c2,l1,l2=l1,l2,c1,c2
    r= ((l1,c1),(l2,c2))
    return r

def lpos(string):
    r=(LETTERS.find(string[0].upper()),int(string[1:])-1)
    if r[0]>= TAILLE or r[1]>=TAILLE:
        raise ValueError("Invalid position: %s" % string)
    return r

def ppos(pos):
    return "%s%d" % (LETTERS[pos[0]],pos[1]+1)

def lline(string):
    m=0
    for c in range(1,len(string)):
        if string[c].isalpha():
            m=c
            break
    return (lpos(string[:m]),lpos(string[m:]))

def pline(line):
    return "%s%s" % (ppos(line[0]),ppos(line[1]))

def iterline(line):
    for l in range(line[0][0],line[1][0]+1):
        for c in range(line[0][1],line[1][1]+1):
            yield (l,c)

def lenline(line):
    i=0
    for k in iterline(line):
        i+=1
    return i


class Jeu:

    INIT=0

    def __init__(self):
        self.magrille= []
        self.tagrille= []
        self.mescoups= []
        self.tescoups= []
        self.mesbateaux={}
        self.tesbateaux={}
        self.etat=Jeu.INIT
        for i in range(TAILLE):
            self.magrille.append([])
            self.tagrille.append([])
            self.mescoups.append([])
            self.tescoups.append([])
            for j in range(TAILLE):
                self.magrille[-1].append(" ")
                self.tagrille[-1].append(" ")
                self.mescoups[-1].append(" ")
                self.tescoups[-1].append(" ")
        self.ia=True
        self.ia_touche=None

    def pose_bateau(self,line,bateau,moi=False):
        bateaux=self.get_bateaux(moi)
        grille=self.get_grille(moi)
        if bateau not in BATEAUX.keys():
            raise ValueError("Mauvais bateau")
        if bateau in bateaux.keys():
            raise ValueError("Bateau deja pose")
        if lenline(line)!=BATEAUX[bateau]:
            raise ValueError("Mauvaise taille de bateau: %s et %s (%s)" % (bateau,lenline(line),pline(line)))
        for p in iterline(line):
            l,c=p
            if grille[l][c]!=" ":
                raise ValueError("Terrain occupe: %s" % ppos((l,c)))
        for p in iterline(line):
            l,c=p
            grille[l][c]=bateau
        bateaux[bateau]=line
        return True

    def pose_bateau_libre(self,bateau,moi=False):
        grille=self.get_grille(moi)
        taille=BATEAUX[bateau]
        pose=False
        while not pose:
            pose=True
            line=rline(taille)
            for p in iterline(line):
                l,c=p
                if grille[l][c]!=" ":
                    pose=False
                    break
        self.pose_bateau(line,bateau,moi)

    def joue(self,pos,moi=False):
        grille=self.get_grille(not moi)
        coups=self.get_coups(moi)
        l,c=pos
        res=grille[l][c]
        if res==" ":
            coups[l][c]="o"
            grille[l][c]="o"
        else:
            coups[l][c]="X"
            grille[l][c]="X"
        return res

    def win(self,moi=False):
        grille=self.get_grille(not moi)
        for l in grille:
            for c in l:
                if c!="X" and c!=" " and c!="o":
                    return False
        return True

    def has_bateau(self,bateau,moi=False):
        grille=self.get_grille(moi)
        for l in grille:
            for c in l:
                if c==bateau:
                    return True
        return False

    def get(self,pos,moi=False):
        grille=self.get_grille(moi)
        l,c=pos
        return grille[l][c]


    def get_coups(self,moi=False):
        if moi:
            return self.mescoups
        else:
            return self.tescoups

    def get_grille(self,moi=False):
        if moi:
            return self.magrille
        else:
            return self.tagrille

    def get_bateaux(self,moi=False):
        if moi:
            return self.mesbateaux
        else:
            return self.tesbateaux


class BatailleModule(BotModule):

    def __init__(self,bot):
        BotModule.__init__(self,bot)
        self.jeux={}
        self.stats=data.DataPickle("%s/bataille_stats.dat" % self.bot.data_dir)


    def function_bataille_new(self,nick,debut=""):
        """
        (str,str)
        Commence une nouvelle partie pour "nick"<br/>
        Si "debut" n'est pas renseignee, alors les bateaux sont places automatiquement<br/>
        Sinon "debut" doit avoir le format: "P:pos C:pos T:pos M:pos L:pos", ou:
        <ul>
        <li> pos est une ligne dans la grille, e.g.: A2A6 ou B2D2</li>
        <li> P (5 cases) est le porte-avion</li>
        <li> C (4 cases) est le croiseur</li>
        <li> T (3 cases) est le contre-torpilleur</li>
        <li> M (3 cases) est le sous-marin</li>
        <li> L (2 cases) est le torpilleur</li>
        </ul>
        """
        jeu=Jeu()
        self.jeux[nick] = jeu
        #tes bateaux
        if debut:
            for p in debut.split(" "):
                bateau,pos=p.split(":")
                jeu.pose_bateau(rline(pos),bateau,False)
        else:
            for b in BATEAUX.keys():
                jeu.pose_bateau_libre(b,False)
        #tes bateaux
        for b in BATEAUX.keys():
            jeu.pose_bateau_libre(b,True)
        return "Nouveau jeu pour %s: %s" % (nick," ".join(map(lambda x: "%s:%s"%(x[0],pline(x[1])),self.jeux[nick].tesbateaux.items())))

    def function_bataille_grille(self,nick):
        """
        Affiche la grille courante
        """
        jeu=self.jeux.get(nick,None)
        if jeu is None:
            return "Pas de jeu en cours !"
        tagrille=jeu.get_grille(False)
        tescoups=jeu.get_coups(False)
        r=" ".join(map(str,range(1,11)))+" "
        r="    %s          %s\n" % (r,r)

        for li in range(len(tagrille)):
            r+="%s ||%s||   --   ||%s|| %s\n" % (LETTERS[li],"|".join(tagrille[li]),"|".join(tescoups[li]),LETTERS[li])
        return r

    def function_bataille_joue(self,nick,pos):
        """
        Joue un coup
        """
        rep=[]
        jeu=self.jeux.get(nick,None)
        if jeu is None:
            return "Pas de jeu en cours !"
        pos=lpos(pos)
        res=jeu.joue(pos,False)
        if res == " " or res == "o":
            rep.append(random.choice(ALEAU))
        else:
            if res=="X":
                rep.append(random.choice(DEJAJOUE))
            else:
                if jeu.has_bateau(res,True):
                    rep.append(random.choice(TOUCHE) % (NOMS_BATEAUX[res],))
                else:
                    rep.append(random.choice(COULE) % (NOMS_BATEAUX[res],))
        if jeu.win(False):
            rep.append(random.choice(GAGNE))
            self.jeux[nick]=None
        elif jeu.ia:
            #IA
            ok=False
            while not ok:
                pos=None
                if jeu.ia_touche is not None and random.randint(0,5):
                    pos=cpos(jeu.ia_touche)
                if pos is None:
                    pos=rpos()
                ok=jeu.get(pos,False) not in "oX"
            res=jeu.joue(pos,True)
            if res not in " oX":
                if jeu.has_bateau(res,False):
                    jeu.ia_touche=pos
                    rep.append("Je joue %s: %s" % (ppos(pos),random.choice(MOITOUCHE) % (NOMS_BATEAUX[res],)))
                else:
                    rep.append("Je joue %s: %s" % (ppos(pos),random.choice(MOICOULE) % (NOMS_BATEAUX[res],)))
                    jeu.ia_touche=None
            else:
                rep.append("Je joue %s" % (ppos(pos),))
            if jeu.win(True):
                rep.append(random.choice(MOIGAGNE))
                self.jeux[nick]=None
        return "\n".join(rep)


