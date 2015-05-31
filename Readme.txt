INSTALL
=======

No hard dependancy. Instal xmpppy if you want to use the Gtalk channel~.

Run
===

~~~~~~~~
$ python runbot.py --help
Usage: runbot.py <list of channels> [-n <bot_personnality_name>] [--learn] [--mute] [--verbose] [--help]

Channels can be:
    -c,--console: Windows console I/O
    -s,--speak: Windows 7 speech recogntion/synthetisis
    -f,--file <filename>: Log file formatted as a sequence of <nick: sentence\n>
    -i,--irc <channel1,channel2,...@server>: IRC I/O
    -g,--gtalk <login:password>: Gtalk I/O
Options are:
    -l,--learn: activate the bot's learning (for all learning modules)
    -m,--mute: The bot won't speak
    -d,--debug: output debug information
    -v,--verbose: error/debug information will be echoed everywhere possible

Note that the bot's help is available at http://localhost:5555. The bot's conf files can be found at ./db/bot_personnality_name/. For any question, remark or sex offer: kaze@neoliage.fr.
~~~~~~~~

Example:

~~~~~~~~
python runbot.py -n monbotamoi -c
~~~~~~~~

Then you have to add some rules for the bot to interract. You can look at the mad2n personnality, included there, for examples.
Please note that for the markov module really to kick in, the bot need to already have learned for some time. 
