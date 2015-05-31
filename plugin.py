# -*- coding: utf8 -*-
from bot import BotModule
import os

class PluginsModule(BotModule):
    """
    Le module qui va charger dynamiquement l'ensemble des plugins.
    TODO: comment créer un plugin
    """

    def __init__(self,bot):
        BotModule.__init__(self,bot)
        directory="./plugins"
        if not directory.endswith(os.sep):
            directory=directory+os.sep
        for f in os.listdir(directory):
            if f.endswith(".py") and f!="__init__.py":
                self.bot.load_module(directory+f)
                





