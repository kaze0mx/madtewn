import cPickle as pickle,marshal

class Code:
    """Serializable lambda function"""
    
    def __init__(self,string,dicofun=None):
        self.source=string
        self.dicofun=dicofun

    def __repr__(self):
        return "Code(%s)" % repr(self.source)

    def __call__(self,*args,**kwargs):
        return eval(self.source,self.dicofun(),{})(*args,**kwargs)


class Data:
    def __init__(self,filename,default={},save_interval=1):
        self.filename=filename
        self.dic={}
        for k,v in default.items():
            self.dic[k]=v
        try:
            values=self.load()            
            for k,v in values.items():
                self.dic[k]=v
        except IOError:
            self.save()
        self.nb_writes=0
        self.save_interval=save_interval

    def __getitem__(self,k):
        if not self.dic.has_key(k):
            self.dic[k]=None
        return self.dic[k]

    def __setitem__(self,k,i):
        self.dic[k]=i
        self.nb_writes+=1
        if self.nb_writes>=self.save_interval:
            self.nb_writes=0
            self.save()

    def __delitem__(self,k):
        del self.dic[k]
        self.nb_writes+=1
        if self.nb_writes>=self.save_interval:
            self.nb_writes=0
            self.save()

    def __len__(self):
        return len(self.dic)

    def has_key(self,k):
        return self.dic.has_key(k)

    def __iter__(self):
        return self.dic.__iter__()

    def values(self):
        return self.dic.values()

    def keys(self):
        return self.dic.keys()

    def items(self):
        return self.dic.items()

    def __repr__(self):
        return repr(self.dic)


class DataPickle(Data):

    def load(self):
        f=open(self.filename,"r")
        res=pickle.load(f)
        f.close()
        return res

    def save(self):
        f=open(self.filename,"w")
        pickle.dump(self.dic,f)
        f.close()


class DataMarshal(Data):

    def load(self):
        f=open(self.filename,"rb")
        res=marshal.load(f)
        f.close()
        return res

    def save(self):
        f=open(self.filename,"wb")
        marshal.dump(self.dic,f)
        f.close()


class DataConf(Data):

    def load(self):
        f = open(self.filename, "r")
        stuff = {}
        line = 0
        while 1:
            line = line + 1
            s = f.readline()
            if s.strip()=="":
                break
            if s[0]=="#":
                continue
            s = map(str.strip,s.split("="))
            if s[0].isdigit():
                s[0]=int(s[0])
            try:
                stuff[s[0]] = eval("=".join(s[1:]),{"True":True,"False":False,"Code":Code},{})
            except:
                raise ValueError("Malformed line in %s line %d" % (self.filename, line))
                continue
        return stuff
        

    def save(self):
        f = open(self.filename, "w")
        fields=self.dic
        for key in fields.keys():
            s = repr(fields[key])
            f.write(str(key)+" = ")
            f.write(s+"\n")
        f.close()

