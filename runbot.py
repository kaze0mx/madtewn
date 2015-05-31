from bot import Bot
from channel import *
import sys,getopt




def usage():
    print "Usage: %s <list of channels> [-n <bot_personnality_name>] [--learn] [--mute] [--verbose] [--help]" % sys.argv[0]
    print """
Channels can be:
    -c,--console: Windows console I/O
    -s,--speak: Windows 7 speech recogntion/synthetisis
    -f,--file <filename>: Log file formatted as a sequence of <nick: sentence\\n>
    -i,--irc <channel1,channel2,...@server>: IRC I/O
    -g,--gtalk <login:password>: Gtalk I/O
Options are:
    -l,--learn: activate the bot's learning (for all learning modules)
    -m,--mute: The bot won't speak
    -d,--debug: output debug information
    -v,--verbose: error/debug information will be echoed everywhere possible

Note that the bot's help is available at http://localhost:5555. The bot's conf files can be found at ./db/bot_personnality_name/. For any question, remark or sex offer: kaze@neoliage.fr.
    """




try:
    opts, args = getopt.getopt(sys.argv[1:], "hn:i:f:g:csvlmd", ["help","name","irc","file","gtalk","console","speak","verbose","learn","mute","debug"])
except getopt.GetoptError, err:
    print str(err) 
    usage()
    sys.exit(2)

name="newbot"
channels=[]
learn=False
mute=False
verbose = False
debug=False

for o, a in opts:
    if a:
        a=a.strip()
    if o in ("-v","--verbose"):
        verbose = True
    elif o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-n", "--name"):
        name=a
    elif o in ("-i", "--irc"):
        chans,serv=a.split("@")
        channels.append(IrcChannel(server=serv,leschan=chans.split(",")))
    elif o in ("-g", "--gtalk"):
        channels.append(GtalkChannel(*a.split(":")))
    elif o in ("-c", "--console"):
        channels.append(ConsoleChannel())
    elif o in ("-f", "--file"):
        channels.append(LogChannel(a))    
    elif o in ("-s", "--speak"):
        channels.append(VoiceChannel())
    elif o in ("-l", "--learn"):
        learn=True
    elif o in ("-m", "--mute"):
        mute=True
    elif o in ("-v", "--verbose"):
        verbose=True
    elif o in ("-d", "--debug"):
        debug=True
    else:
        assert False, "unhandled option"

if not channels:
    usage()
    raise ValueError("No channel selected")
b=Bot(name)
b.conf["learn"]=learn
b.conf["mute"]=mute
if verbose:
    b.conf["debug_verbosity"]=7
    b.conf["error_verbosity"]=7
else:
    b.conf["debug_verbosity"]=1
    b.conf["error_verbosity"]=3
if not debug:
    b.conf["debug_verbosity"]=0
for c in channels:
    b.connect(c)
    c.start()
