# ============================================
# KJVBot by Jack (gitub.com/jackthebaptist)
# This bot will get any verse from the KJV 
# Licensed under the GPL 3.0
# ============================================

# --- Imports ---
import api.bible
import sys
from profanity import profanity
import discord
import asyncio
from discord.utils import get
from discord.ext.commands import Bot
from discord.ext import commands
import platform

# --- Colours ---
def codechar(code):
    return CPT + str(code) + 'm'

class colour_code(object):
    def __init__(self):
        for name in dir(self):
            if not name.startswith('_'):
                value = getattr(self, name)
                setattr(self, name, codechar(value))

class foreground(colour_code): #foreground colours (text)
    BLACK           = 30
    RED             = 31
    GREEN           = 32
    YELLOW          = 33
    BLUE            = 34
    MAGENTA         = 35
    CYAN            = 36
    WHITE           = 37
    RESET           = 39

class background(colour_code): #background colours (selections)
    BLACK           = 40
    RED             = 41
    GREEN           = 42
    YELLOW          = 43
    BLUE            = 44
    MAGENTA         = 45
    CYAN            = 46
    WHITE           = 47
    RESET           = 49

# --- Global Variables ---
client = Bot(description="This bot will recite any verse from the KJV", command_prefix="/", pm_help = True)
ab = api.bible

# --- console code ---
@client.event
async def on_ready(): #Start up message for console, will not be seen on Discord
	print('======================================================')
	print('Logged in as \033[32m'+client.user.name+'\033[39m (ID:\033[32m'+client.user.id+'\033[39m) | Connected to \033[33m'+str(len(client.servers))+'\033[39m servers | Connected to \033[33m'+str(len(set(client.get_all_members())))+'\033[39m users')
	print('--------')
	print('Current Discord.py Version: {} | Current Python Version: {}'.format(discord.__version__, platform.python_version()))
	print('--------')
	print('Use this link to invite your bot to other servers:')
	print('\033[32mhttps://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8\033[39m'.format(client.user.id))
	print('--------')
	print('You are running KJVBot 1.8')
	print('Created by \033[36mJack\033[39m')
	print('\033[32mhttps://github.com/glyphs\033[39m')
	print('======================================================\n')
	return await client.change_presence(game=discord.Game(name='usage: /kjv john 3:16'))

@client.event
async def on_message(message):	
	if message.content.startswith("/kjv"):
		verse = message.content[4:]
		try:
			a,b,c = verse.split(" ")		
			result = ab.get_passage(a+" "+b+" "+c)
			try:
				output = result['text'].replace('*', '\n\n').replace('#', '\n')
				desc = output.encode('utf8').decode(sys.stdout.encoding)
				embed = discord.Embed(title=":closed_book: ** "+result['reference']+" **", description=desc, color=0x1fcd53)
				await client.send_message(message.channel,embed=embed)
				print("\033[32m[+]\033[39m request for ("+a+" "+b+" "+c+") by: "+message.author.mention)
			except TypeError:
				await client.send_message(message.channel,"Dude, learn how to type.")
		except ValueError:
			a,b = verse.split(" ")
			result = ab.get_passage(a+" "+b)
			try:
				output = result['text'].replace('*', '\n\n').replace('#', '\n')
				desc = output.encode('utf8').decode(sys.stdout.encoding)
				embed = discord.Embed(title=":closed_book: ** "+result['reference']+" **", description=desc, color=0x1fcd53)
				await client.send_message(message.channel,embed=embed)
				print("\033[32m[+]\033[39m request for ("+a+" "+b+") by: "+message.author.mention)
			except TypeError:
				await client.send_message(message.channel,"Dude, learn how to type.")
		
	elif message.content.startswith("/votd"):
		result = ab.getVotd()
		vrs = result['text']
		embed = discord.Embed(title="====== Verse of the Day ======", description="", color=0x1fcd53)
		embed.add_field(name=":closed_book: ** "+result['reference']+" **", value=vrs)
		await client.send_message(message.channel,embed=embed)
		print("\033[32m[+]\033[39m request for VOTD by: "+message.author.mention)	
		

client.run('ADD BOT ID HERE')
