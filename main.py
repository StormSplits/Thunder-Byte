import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
from textblob import TextBlob
import asyncio
import os
import logging
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
import re
import webserver

# Load environment variables from the config.env file
load_dotenv('./config.env')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Set up Google Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# User memory
user_memory = {}

# Bot introduction messages
bot_intros = [
    "🌩️ **Hello, I'm Thunder Byte!** 🌩️\nI'm your new stormy sidekick, crafted with lightning speed and thunderous power of **Storm Splits**!",
    "⚡ **Greetings! Thunder Byte at your service!** ⚡\nForged in the digital storm clouds by the brilliant mind of **Storm Splits**!",
    "🌪️ **Bzzt! Thunder Byte here!** 🌪️\nYour electrifying companion, sparked to life by the **Storm Splits**!"
]

# Bot features list
bot_features = [
    "⚡ Answer science questions with electrifying accuracy!",
    "🔢 Solve math problems faster than lightning!",
    "🏛️ Enlighten you with mythological tales from across the ages!",
    "😂 Crack jokes that'll make you roar with laughter!",
    "📚 Spin yarns and tell tales that'll blow you away!",
    "🧠 Offer sage advice backed by ancient wisdom and pop culture!"
]

# Getting started guide
getting_started = """
🌩️ **How to Get Started:**
1. Type `/` to see all available commands
2. Choose a command and fill in any required information
3. Hit enter and watch the storm of knowledge unfold!
4. For more fun, try mentioning me in a message!

Remember, I'm always here to help, rain or shine! ⚡🚀
"""


# Helper function to generate bot introduction
def generate_bot_intro():
    intro = random.choice(bot_intros)
    features = "\n".join(random.sample(bot_features,
                                       4))  # Randomly select 4 features
    return f"{intro}\n\n⚡ **What I Can Do:**\n{features}\n\n{getting_started}"


# Helper function to generate response using Gemini API
def replace_bot_name_with_user(response_text, user_name):
    bot_name = bot.user.name
    return response_text.replace(bot_name, user_name)


async def generate_response(prompt, user_name):
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        final_response = replace_bot_name_with_user(response.text, user_name)
        return final_response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I'm having trouble coming up with a response right now. Try again later!"


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


# Command error handler
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction,
                               error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True)
    else:
        logger.error(f"Command error: {error}")
        await interaction.response.send_message(
            "An error occurred while processing your command. Please try again later.",
            ephemeral=True)


# About command
@bot.tree.command(name="about", description="Learn about Thunder Byte")
async def about(interaction: discord.Interaction):
    response = generate_bot_intro()
    if len(response) > 2000:
        await interaction.response.defer()
        await interaction.followup.send(response[:2000])
        await interaction.followup.send(response[2000:])
    else:
        await interaction.response.send_message(response)


# Science command
@bot.tree.command(name="science", description="Answer a science question")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def science(interaction: discord.Interaction, question: str):
    prompt = f"Answer this science question with the divine clarity and wisdom of Shree Krishna: {question}"
    response = await generate_response(prompt, interaction.user.display_name)
    if len(response) > 2000:
        await interaction.response.defer()
        await interaction.followup.send(response[:2000])
        await interaction.followup.send(response[2000:])
    else:
        await interaction.response.send_message(response)


# Math command
@bot.tree.command(name="math", description="Solve a math problem")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def math(interaction: discord.Interaction, problem: str):
    prompt = f"Solve this math problem and explain the solution with divine wisdom: {problem}"
    response = await generate_response(prompt, interaction.user.display_name)
    if len(response) > 2000:
        await interaction.response.defer()
        await interaction.followup.send(response[:2000])
        await interaction.followup.send(response[2000:])
    else:
        await interaction.response.send_message(response)


# Mythology command
@bot.tree.command(name="mythology",
                  description="Provide information about a mythology topic")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def mythology(interaction: discord.Interaction, topic: str):
    prompt = f"Provide information about this mythology topic with the insight and serenity of Shree Krishna: {topic}"
    response = await generate_response(prompt, interaction.user.display_name)
    if len(response) > 2000:
        await interaction.response.defer()
        await interaction.followup.send(response[:2000])
        await interaction.followup.send(response[2000:])
    else:
        await interaction.response.send_message(response)


# Joke command
@bot.tree.command(name="joke", description="Tell a joke")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def joke(interaction: discord.Interaction, topic: str = None):
    if topic:
        prompt = f"Tell a funny joke about {topic}"
    else:
        prompt = "Tell a random funny joke"
    response = await generate_response(prompt, interaction.user.display_name)
    if len(response) > 2000:
        await interaction.response.defer()
        await interaction.followup.send(response[:2000])
        await interaction.followup.send(response[2000:])
    else:
        await interaction.response.send_message(response)


# Story command
@bot.tree.command(name="story", description="Tell a short story")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def story(interaction: discord.Interaction, theme: str = None):
    if theme:
        prompt = f"Tell a short story about {theme}"
    else:
        genres = ["sci-fi", "fantasy", "mystery", "romance", "adventure"]
        prompt = f"Tell a short {random.choice(genres)} story"

    # Acknowledge the interaction with a deferred response
    await interaction.response.defer()

    response = await generate_response(prompt, interaction.user.display_name)

    # Split and send long responses
    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await interaction.followup.send(response[i:i + 2000])
    else:
        await interaction.followup.send(response)


# Advice command without memory
@bot.tree.command(name="advice", description="Get life advice on a topic")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def advice(interaction: discord.Interaction, topic: str):
    prompt = f"""Provide life advice on topic mentioned below with the divine wisdom and compassion of Shree Krishna. 
    Include insights from the Bhagavad Gita and relevant parables to illuminate the advice. Also, include a relevant quote from a Disney or Dreamworks movie to support the advice.:
    {topic}"""

    try:
        response = await generate_response(prompt, interaction.user.display_name)
        if len(response) > 2000:
            # Defer response
            await interaction.response.defer()
            # Send response in chunks
            for i in range(0, len(response), 2000):
                await interaction.followup.send(response[i:i + 2000])
        else:
            await interaction.response.send_message(response)
    except Exception as e:
        logger.error(f"Error in advice command: {e}")
        await interaction.response.send_message(
            "An error occurred while processing your request. Please try again later.",
            ephemeral=True)


# Ask Me Anything command
@bot.tree.command(name="ask", description="Ask me anything")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def ask(interaction: discord.Interaction, question: str):
    # Filter vulgarity or inappropriate content
    if any(vulgar_word in question.lower()
           for vulgar_word in ["vulgarity", "inappropriate"]):
        await interaction.response.send_message(
            "Sorry, I can't answer that question.", ephemeral=True)
        return

    prompt = f"Answer this question with the divine wisdom and grace of Shree Krishna: {question}"
    response = await generate_response(prompt, interaction.user.display_name)
    if len(response) > 2000:
        await interaction.response.defer()
        await interaction.followup.send(response[:2000])
        await interaction.followup.send(response[2000:])
    else:
        await interaction.response.send_message(response)


# Respond to mentions and engage in small talk
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        content = message.content
        user_name = message.author.display_name  # Fetch user's display name
        user_id = message.author.id  # Fetch user's ID

        # Remove bot mention from the message content
        bot_mention_pattern = re.escape(f"<@{bot.user.id}>")
        cleaned_content = re.sub(bot_mention_pattern, '', content).strip()

        if any(phrase in cleaned_content.lower() for phrase in
               ["who are you", "what can you do", "tell me about yourself"]):
            response = generate_bot_intro()
            if len(response) > 2000:
                await message.channel.send(response[:2000])
                await message.channel.send(response[2000:])
            else:
                await message.channel.send(response)
        else:
            if message.reference:
                original_message = await message.channel.fetch_message(
                    message.reference.message_id)
                question = original_message.content
                cleaned_question = re.sub(bot_mention_pattern, '', question).strip()
                response = await generate_response(cleaned_question, user_name)
                if len(response) > 2000:
                    await message.channel.send(response[:2000])
                    await message.channel.send(response[2000:])
                else:
                    await message.channel.send(
                        f"<@{user_id}>! ⚡️\n\n{response}")
            else:
                prompt = f"Respond to this message with the divine wisdom and grace of Shree Krishna: {cleaned_content}"
                response = await generate_response(prompt, user_name)
                if len(response) > 2000:
                    await message.channel.send(response[:2000])
                    await message.channel.send(response[2000:])
                else:
                    await message.channel.send(
                        f"<@{user_id}>! ⚡️\n\n{response}")

    await bot.process_commands(message)


# Run the bot
webserver.keep_alive()
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
