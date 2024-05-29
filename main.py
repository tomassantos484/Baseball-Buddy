#Importing Libraries
import discord
import os
import giphy_client
import requests
import random
import json
import MLBTeams
import google.generativeai as genai
from pybaseball import *
from pybaseball import cache
from discord.ext import commands
from dotenv import load_dotenv
from giphy_client.rest import ApiException

#Cache for pybaseball
cache.enable()

# Discord, GIPHY, TENOR API Key Set Up
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GIPHY_KEY = os.getenv("GIPHY_KEY")
TENOR_KEY = os.getenv("TENOR_KEY")

#Google Gemini API Key Set Up
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Generate a fun fact about the MLB.")

#Mike Trout Constants
MikeTrout = "Mike Trout"
MikeFirst = "Mike"
TroutLast = "Trout"
MikeTeam = "Los Angeles Angels"

#Discord Bot Set Up
client = commands.Bot(command_prefix = '!', intents=discord.Intents.all())

@client.event
async def on_ready():
    print("Mike Trout is ready to bat!")
    await client.change_presence(activity=discord.Game(name="Baseball"))
    try:
        synced = await client.tree.sync()
    except Exception as e:
        print(e)

@client.tree.command(name="hello", description="Mike Trout says hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}! I am Mike Trout, the best baseball player in the world!", ephemeral=False)

@client.tree.command(name="goodbye", description="Mike Trout says goodbye!")
async def goodbye(interaction: discord.Interaction):
    await interaction.response.send_message(f"Goodbye, {interaction.user.mention}! I hope to see you again soon!", ephemeral=False)
    
@client.tree.command(name="ping", description="Mike Trout sends his ping!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(client.latency * 1000)}ms", ephemeral=False)

@client.tree.command(name="randomgifgiphy", description="Mike Trout sends a random gif from GIPHY!")
async def randomgifgiphy(interaction: discord.Interaction, q: str= MikeTrout):
    api_instance = giphy_client.DefaultApi()

    try:
        api_response = api_instance.gifs_search_get(GIPHY_KEY, q, rating="g")
        random_gif_list = list(api_response.data)
        gif_selection = random.choice(random_gif_list)

        attribution_image = discord.File("giphy_attribution_logo.gif", filename="image.gif")

        emb = discord.Embed(
            title=q, 
            color= discord.Color.red()
            )
        emb.set_image(url=f'https://media.giphy.com/media/{gif_selection.id}/giphy.gif')
        emb.set_footer(text = "Powered by GIPHY", icon_url = "attachment://image.gif")

        await interaction.response.send_message(embed=emb, file= attribution_image, ephemeral=False)

    except ApiException as e:
        print("Exception when calling DefaultApi->gifs_random_get: %s\n" % e)

@client.tree.command(name="randomgiftenor", description="Mike Trout sends a random gif from Tenor!")
async def randomgiftenor(interaction: discord.Interaction, q: str = MikeTrout):
    try:
        params = {
            "q": q,
            "key": TENOR_KEY,
            "limit": 50
        }

        result = requests.get("https://tenor.googleapis.com/v2/search?", params=params)
        data = result.json()

        number = random.randint(0,49)
        url = data["results"][number]["media_formats"]["gif"]["url"]

        embed = discord.Embed(
            title = q,
            color = discord.Color.blue()
        )

        embed.set_image(url=url)
        embed.set_footer(text="Via Tenor")
        await interaction.response.send_message(embed=embed)

    except Exception:
        print("Error!")

@client.tree.command(name="playerlookup", description="Mike Trout sends info about a player of your choice!")
async def playerlookup(interaction: discord.Interaction, first_name: str = MikeFirst, last_name: str = TroutLast):
    player = playerid_lookup(last_name, first_name)
    if player.empty:
        await interaction.response.send_message("Player not found!")
        return

    mlb_key = player['key_mlbam'].iloc[0]
    retro_key = player['key_retro'].iloc[0]
    bbref_key = player['key_bbref'].iloc[0]
    fangraphs_key = player['key_fangraphs'].iloc[0]
    first_season = int(player['mlb_played_first'].iloc[0])
    last_season = int(player['mlb_played_last'].iloc[0])

    mlb_url = f"https://www.mlb.com/player/{first_name.lower()}-{last_name.lower()}-{mlb_key}"
    retrosheet_url = f"https://www.retrosheet.org/boxesetc/{last_name[0].upper()}/P{retro_key}.htm"
    bbref_url = f"https://www.baseball-reference.com/players/{last_name[0].lower()}/{bbref_key}.shtml"
    fangraphs_url = f"https://www.fangraphs.com/players/{first_name}-{last_name}/{fangraphs_key}"

    embed = discord.Embed(title=f"{first_name} {last_name}", description=f"Player ID: {mlb_key}", color=discord.Color.blue())
    embed.add_field(name="First MLB Season", value=first_season, inline=False)
    embed.add_field(name="Last MLB Season", value=last_season, inline=False)
    embed.add_field(name="MLB.com:", value=mlb_url, inline=False)
    embed.add_field(name="Retrosheet:", value=retrosheet_url, inline=False)
    embed.add_field(name="Baseball Reference:", value=bbref_url, inline=False)
    embed.add_field(name="Fangraphs:", value=fangraphs_url, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=False)

@client.tree.command(name="randomstatement", description="Mike Trout sends a random statement!")
async def randomstatement(interaction: discord.Interaction, player: str = MikeTrout, team: str = MikeTeam):
    # Immediately defer the interaction to indicate processing is happening
    # and to get more time for sending the response.
    await interaction.response.defer(ephemeral=False)

    # Fetching player names
    # Open the text file containing player names
    with open('player_names.txt', 'r') as file:
    # Read all lines from the file
        player_names = file.readlines()
    # Remove leading and trailing whitespaces from each player name
        player_names = [name.strip() for name in player_names]

        
    #Use Cases
    def get_statement(player, team):
        base_case = "Generate a random funny, semi-satirical, and meme-like baseball-related random statement based on"
        if player == "empty" and team == "empty":
            player = MikeTrout
            team = MikeTeam

        if player == "random" and team == "random":
            prompt = f"{base_case} a random player and a random team."
        
        elif player == "random" and team != "random":
            prompt = f"{base_case} a random player and the {team}."
        
        elif player != "random" and team == "random":
            team = random.choice(list(MLBTeams.Teams.values()))
            prompt = f"{base_case} {player} and a random team. The team is the {team}."
        
        elif player == "empty":
            prompt = f"{base_case} the {team}."
        
        elif team == "empty":
            prompt = f"{base_case} {player}."
        else:
            prompt = f"{base_case} {player} and the {team}."

        return model.generate_content(prompt)

    # Call the function and store the response
    response = get_statement(player, team)
    await interaction.followup.send(response.text, ephemeral=False)

@client.tree.command(name="troutify", description="Mike Trout sends a random statement about himself!")
async def troutify(interaction: discord.Interaction):

    # Immediately defer the interaction to indicate processing is happening
    # and to get more time for sending the response.
    await interaction.response.defer(ephemeral=False)
    
    response = model.generate_content("Generate a random funny, semi-satirical, and meme-like baseball-related random statement based on Mike Trout.")
    await interaction.followup.send(response.text, ephemeral=False)

   
@client.tree.command(name="funfact", description="Mike Trout sends a fun fact about the MLB!")
async def funfact(interaction: discord.Interaction):
    response = model.generate_content("You are an expert baseball historian who knows the game of baseball in and out. Generate a fun fact about MLB. As you are called upon to generate fun facts, be sure to occasionally include fun facts about rules, games, series, postseason, world series, stats, bizarre occurrences, etc.")
    await interaction.response.send_message(response.text, ephemeral=False)


#New Command Ideas:
#Game Schedule and Scores
#Player and Team News
#Fantasy Baseball Integration
#Game Highlights and Media
#Trivia + Interactivity
#Etc.

client.run(DISCORD_TOKEN)