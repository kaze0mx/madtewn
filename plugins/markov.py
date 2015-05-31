# -*- coding: utf8 -*-
import sys,random
sys.path.append("../")
from bot import BotModule
import data
import struct


RATIO_CHOSEN_words_in_lines=3
NUM_MIN_CONTEXT_FOR_CHOSEN_WORD=3
WRITE_INTERVAL=100


class MarkovModule(BotModule):
    """
    Module pour la création de  chaînes de markov de mots. Fonctionne sur toutes les sémantiques.
    """
    def __init__(self,bot):
        BotModule.__init__(self,bot)
        self.words_in_lines={}
        self.lines={}
        self.contexts={}
        self.previous_chosen_words_in_lines={}
        self.nb_writes=0
        self.allowed_semantics=self.bot.conf["markov_allowed_semantics"]
        for sem in self.allowed_semantics:
            self.lines[sem]=data.DataMarshal("%s/markov_lines_%s.py" % (self.bot.data_dir,sem),save_interval=10000000)
            self.words_in_lines[sem]=data.DataMarshal("%s/markov_words_%s.py" % (self.bot.data_dir,sem),save_interval=10000000)
            self.contexts[sem]=data.DataMarshal("%s/markov_contexts_%s.py" % (self.bot.data_dir,sem),save_interval=10000000)
            self.previous_chosen_words_in_lines[sem]={}
        self.bot.hook_pre_message(self.learn)



    def learn(self,transduced,author,spectators,thread,private):
        """learn on all allowed semantics by populating the markov chains
        """
        if not self.bot.conf["learn"]:
            return
        for sem,msg in transduced.items():
            if not sem in self.allowed_semantics:
                continue
            lines=self.lines[sem]
            words_in_lines=self.words_in_lines[sem]
            contexts=self.contexts[sem]
            previous_chosen_words_in_lines=self.previous_chosen_words_in_lines[sem]
            mots=map(str.strip,msg.split())
            line=" ".join(mots)

            #lines
            hash_line=DJBHash(line)
            if not lines.has_key(hash_line):
                lines[hash_line]=struct.pack("H",1)+line
            else:
                l=lines[hash_line]
                num_ctxt=struct.unpack("H",l[:2])[0]
                if num_ctxt<65000:
                    num_ctxt+=1
                lines[hash_line]=struct.pack("H",num_ctxt)+l[2:]

            #words_in_lines
            i=0
            for w in mots:
                hash_w=DJBHash(w)
                if not words_in_lines.has_key(hash_w):
                    words_in_lines[hash_w]=struct.pack("IB",hash_line,i)
                else:
                    hl=words_in_lines[hash_w]
                    if not hash_in_packed_hashs(hash_line,hl,1):
                        hl+=struct.pack("IB",hash_line,i)
                        words_in_lines[hash_w]=hl
                i+=1

            #contexts
            chosen_word=self.chose_word(mots,words_in_lines)
            if not chosen_word:
                continue
            if previous_chosen_words_in_lines.has_key(thread):
                hash_previous_chosen_words_in_lines=DJBHash(previous_chosen_words_in_lines[thread])
                hash_chosen_word=DJBHash(chosen_word)
                if not contexts.has_key(hash_previous_chosen_words_in_lines):
                    contexts[hash_previous_chosen_words_in_lines]=struct.pack("I",hash_chosen_word)
                else:
                    ctxt=contexts[hash_previous_chosen_words_in_lines]
                    if not hash_in_packed_hashs(hash_chosen_word,ctxt):
                        ctxt+=struct.pack("I",hash_chosen_word)
                        contexts[hash_previous_chosen_words_in_lines]=ctxt
            self.previous_chosen_words_in_lines[sem][thread]=chosen_word
            self.nb_writes+=1
            if self.nb_writes>WRITE_INTERVAL:
                self.nb_writes=0
                words_in_lines.save()
                lines.save()
                contexts.save()
        return 


    def word_from_hash(self,h,sem):
        l0=self.words_in_lines[sem][h]
        l,pos=struct.unpack("IB",l0[0:5])
        l=self.lines[sem][l][2:].split()
        if pos>=len(l):
            #Si collision
            return random.choice(l)
        return l[pos]


    def chose_word(self,words_in_lines,sem_words_in_lines):
        l=[]
        for w in words_in_lines:
            hash_w=DJBHash(w)
            if not sem_words_in_lines.has_key(hash_w):
                continue
            lines=sem_words_in_lines[hash_w]
            #Must be known in 3 different contexts at least
            if len(lines)<NUM_MIN_CONTEXT_FOR_CHOSEN_WORD*5:
                continue
            l.append((len(lines),w))
        l.sort(lambda x,y:cmp(x[0],y[0]))
        if l:
            return random.choice(l[:int(len(l)/RATIO_CHOSEN_words_in_lines)+1])[1]
        else:
            return None        

    
    def get_log_hash_word(self,hash_w,sem):
        """
        Retourne une phrase des logs contenant le mot de hash <hash_w>
        """
        if not sem in self.allowed_semantics:
            raise ValueError("No learning for this semantics, thus no log")
        words_in_lines=self.words_in_lines[sem]
        lines=self.lines[sem]
        l=words_in_lines[hash_w]
        i=random.randint(0,len(l)/5-1)*5
        hash_line=struct.unpack("I",l[i:i+4])[0]
        return lines[hash_line][2:]


    def get_markov_word(self,chosen_word,sem,sens=1):
        """
        Retourne une phrase construite via markov autour d'un mot de hash <hash_w>
        """
        words_in_lines=self.words_in_lines[sem]
        lines=self.lines[sem]

        # Build sentence backward/forward from <word>
        sentence = [chosen_word]
        done = False
        while not done:
            pre_words = {None : 0}
            if sens==-1:
                word=sentence[0]
            else:
                word=sentence[-1]
            hash_word=DJBHash(word)
            ls=words_in_lines[hash_word]
            for x in xrange(0, len(ls),5):
                l, pos = struct.unpack("IB", ls[x:x+5])
                tmp=lines[l]
                line = tmp[2:]
                num_context = struct.unpack("H",tmp[0:2])[0]
                cwords = line.split()
                if pos>=len(cwords):
                    #Collision
                    continue
                #if the word is not the first/last of the memorized line, look the previous one
                if sens==1 and len(sentence) > 1:
                    if sentence[len(sentence)-2] != cwords[pos-1]:
                        continue
                if (sens==-1 and pos) or (sens==1 and pos < len(cwords)-1):
                    #look if we can find a pair with the choosen word, and the previous one
                    if sens==-1 and len(sentence) > 1 and len(cwords) > pos+1:
                        if sentence[0-sens] != cwords[pos-sens]:
                            continue
                    look_for = (l, pos) #cwords[pos+sens]
                    #saves how many times we can find each word
                    if not(pre_words.has_key(look_for)):
                        pre_words[look_for] = num_context
                    else :
                        pre_words[look_for] += num_context
                else:
                    pre_words[None] += num_context
            if pre_words[None]==1:
                pre_words[None]=0
            #Sort the words
            liste = pre_words.items()
            if not liste:
                return
            liste.sort(lambda x,y: cmp(y[1],x[1]))
            numbers = [liste[0][1]]
            #build proba range
            for x in xrange(1, len(liste) ):
                numbers.append(liste[x][1] + numbers[x-1])
            #take one them from the list ( randomly )
            max_iter=0
            retire=True
            while retire and max_iter<len(numbers)+5:
                tir = random.randint(0, numbers[len(numbers) -1])
                for x in xrange(0, len(numbers)):
                    if tir <= numbers[x]:
                        chosen = liste[x][0]
                        break
                retire=False#chosen is not None and chosen[2] in sentence
                max_iter+=1
            if chosen is None:
                done = True
            else:
                hash_l, pos = chosen
                cwords = lines[hash_l][2:].split()
                cont = True
                last_proba = None
                while cont:
                    cont = False
                    pos+=sens
                    if pos >= len(cwords) or pos < 0:
                        break
                    word = cwords[pos]
                    hash_word=DJBHash(word)
                    ls=words_in_lines[hash_word]
                    proba = 0
                    for x in xrange(0, len(ls),5):
                        word_line, _ = struct.unpack("IB", ls[x:x+5])
                        the_line = lines[word_line]
                        proba += struct.unpack("<H", the_line[:2])[0]
                    if sens==-1:
                        if last_proba is None or proba > last_proba*2:
                            sentence.insert(0, word) 
                            cont = True
                    else:
                        if last_proba is None or proba*2 < last_proba:
                            sentence.append(word) 
                            cont = True
                    last_proba = proba
        return sentence
    
    def save(self):
        for sem in self.allowed_semantics:
            self.lines[sem].save()
            self.words_in_lines[sem].save()
            self.contexts[sem].save()


#**************************************************************************
#
# Fonctions
#
#**************************************************************************

    def function_dump(self):
        lines=self.lines[2]
        f=open("log","w")
        for v in lines.values():
            ctxt=struct.unpack("H",v[:2])[0]
            l=v[2:]
            f.write("%d:%s\n"%(ctxt,l))
        f.close()



    def function_clean(self,sem):
        """
        (int)
        Clean les logs
        """
        from channel import to_utf8
        lines=self.lines[sem]
        words_in_lines=self.words_in_lines[sem]
        contexts=self.contexts[sem]
        for hw in words_in_lines.keys():
            w=self.word_from_hash(hw,sem)
            wutf8=to_utf8(w)
            if w!=wutf8:
                print repr(w),"vs",repr(wutf8.decode("utf8").encode("cp850","ignore"))
            

    def function_markov_repeat(self,string,sem):
        """
        (str,int)
        Retourne une chaine de markov construite autour d'un mot intéressant 
        de "string", ou d'un mot au hasard si aucun mot intéressant.
        """
        words_in_lines=self.words_in_lines[sem]
        mots=map(str.strip,string.split())
        chosen_word=self.chose_word(mots,words_in_lines)
        if not chosen_word:
            chosen_word=self.word_from_hash(random.choice(words_in_lines.keys()),sem)
        cont=True
        while cont:
            pre_sentence=self.get_markov_word(chosen_word,sem,-1)
            post_sentence=self.get_markov_word(chosen_word,sem,1)
            sentence=" ".join(pre_sentence[:-1]+post_sentence)
            chosen_word=self.word_from_hash(random.choice(words_in_lines.keys()),sem)
            cont=len(sentence)==0
        return sentence

    def function_markov_answer(self,string,sem):
        """
        (str,int)
        Retourne une chaine de markov construite autour d'un mot répondu une
        fois a un mot intéressant  de "string", ou d'un mot au hasard si 
        aucun mot intéressant.
        """
        mots=map(str.strip,string.split())
        words_in_lines=self.words_in_lines[sem]
        contexts=self.contexts[sem]
        chosen_word=self.chose_word(mots,words_in_lines)
        if not chosen_word:
            hash_w=random.choice(words_in_lines.keys())
        else:
            hash_w=DJBHash(chosen_word)
            if contexts.has_key(hash_w):
                l=contexts[hash_w]
                i=random.randint(0,len(l)/4-1)*4
                hash_w=struct.unpack("I",l[i:i+4])[0]
            else:
                hash_w=random.choice(words_in_lines.keys())
        chosen_word=self.word_from_hash(hash_w,sem)
        return self.function_markov_repeat(chosen_word,sem)




    def function_log_repeat(self,string,sem=0):
        """
        (str,int)
        Retourne une phrase des logs contenant un mot intéressant de "string".
        Si aucune n'est trouvée, retourne une phrase aléatoire.
        """
        words_in_lines=self.words_in_lines[sem]
        mots=map(str.strip,string.split())
        chosen_word=self.chose_word(mots,words_in_lines)
        if not chosen_word:
            hash_w=random.choice(words_in_lines.keys())
        else:
            hash_w=DJBHash(chosen_word)
        return self.get_log_hash_word(hash_w,sem)

    def function_log_answer(self,string,sem=0):
        """
        (str,int)
        Retourne une phrase des logs contenant un de des mots répondus à "string".
        Si aucune n'est trouvée, retourne une phrase aléatoire.
        """
        mots=map(str.strip,string.split())
        words_in_lines=self.words_in_lines[sem]
        contexts=self.contexts[sem]
        chosen_word=self.chose_word(mots,words_in_lines)
        if not chosen_word:
            hash_w=random.choice(words_in_lines.keys())
        else:
            hash_w=DJBHash(chosen_word)
            if contexts.has_key(hash_w):
                l=contexts[hash_w]
                i=random.randint(0,len(l)/4-1)*4
                hash_w=struct.unpack("I",l[i:i+4])[0]
            else:
                hash_w=random.choice(words_in_lines.keys())
        return self.get_log_hash_word(hash_w,sem)
        


   








def hash_in_packed_hashs(h,packed_hashs,extra_bytes=0):
    h=struct.pack("I",h)
    for i in range(0,len(packed_hashs),4+extra_bytes):
        if h==packed_hashs[i:i+4]:
            return True
    return False



#**************************************************************************
#*                                                                        *
#*          General Purpose Hash Function Algorithms Library              *
#*                                                                        *
#* Author: Arash Partow - 2002                                            *
#* URL: http://www.partow.net                                             *
#* URL: http://www.partow.net/programming/hashfunctions/index.html        *
#*                                                                        *
#* Copyright notice:                                                      *
#* Free use of the General Purpose Hash Function Algorithms Library is    *
#* permitted under the guidelines and in accordance with the most current *
#* version of the Common Public License.                                  *
#* http://www.opensource.org/licenses/cpl1.0.php                          *
#*                                                                        *
#**************************************************************************
#

def RSHash(key):
    a    = 378551
    b    =  63689
    hash =      0
    for i in range(len(key)):
      hash = hash * a + ord(key[i])
      a = a * b
    return hash


def JSHash(key):
    hash = 1315423911
    for i in range(len(key)):
      hash ^= ((hash << 5) + ord(key[i]) + (hash >> 2))
    return hash


def PJWHash(key):
   BitsInUnsignedInt = 4 * 8
   ThreeQuarters     = long((BitsInUnsignedInt  * 3) / 4)
   OneEighth         = long(BitsInUnsignedInt / 8)
   HighBits          = (0xFFFFFFFF) << (BitsInUnsignedInt - OneEighth)
   hash              = 0
   test              = 0

   for i in range(len(key)):
     hash = (hash << OneEighth) + ord(key[i])
     test = hash & HighBits
     if test != 0:
       hash = (( hash ^ (test >> ThreeQuarters)) & (~HighBits));
   return (hash & 0x7FFFFFFF)


def ELFHash(key):
    hash = 0
    x    = 0
    for i in range(len(key)):
      hash = (hash << 4) + ord(key[i])
      x = hash & 0xF0000000
      if x != 0:
        hash ^= (x >> 24)
      hash &= ~x
    return hash


def BKDRHash(key):
    seed = 131 # 31 131 1313 13131 131313 etc..
    hash = 0
    for i in range(len(key)):
      hash = (hash * seed) + ord(key[i])
    return hash


def SDBMHash(key):
    hash = 0
    for i in range(len(key)):
      hash = ord(key[i]) + (hash << 6) + (hash << 16) - hash;
    return hash


def DJBHash(key):
    hash = 5381
    for i in range(len(key)):
       hash = ((hash << 5) + hash) + ord(key[i])
    return hash & 0xFFFFFFFF


def DEKHash(key):
    hash = len(key);
    for i in range(len(key)):
      hash = ((hash << 5) ^ (hash >> 27)) ^ ord(key[i])
    return hash


def BPHash(key):
    hash = 0
    for i in range(len(key)):
       hash = hash << 7 ^ ord(key[i])
    return hash


def FNVHash(key):
    fnv_prime = 0x811C9DC5
    hash = 0
    for i in range(len(key)):
      hash *= fnv_prime
      hash ^= ord(key[i])
    return hash


def APHash(key):
    hash = 0xAAAAAAAA
    for i in range(len(key)):
      if ((i & 1) == 0):
        hash ^= ((hash <<  7) ^ ord(key[i]) * (hash >> 3))
      else:
        hash ^= (~((hash << 11) + ord(key[i]) ^ (hash >> 5)))
    return hash


        





    

    
        


    
