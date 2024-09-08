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
import asyncpg

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

# New: Conversation history
conversation_history = {}
MAX_HISTORY_LENGTH = 10

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
    features = "\n".join(random.sample(bot_features, 4))  # Randomly select 4 features
    return f"{intro}\n\n⚡ **What I Can Do:**\n{features}\n\n{getting_started}"

# Helper function to generate response using Gemini API
def replace_bot_name_with_user(response_text, user_name):
    bot_name = bot.user.name
    return response_text.replace(bot_name, user_name)

async def generate_response(prompt, user_name, user_id):
    try:
        # Retrieve user's conversation history
        history = conversation_history.get(user_id, [])
        
        # Construct the full prompt with conversation history and context
        full_prompt = "Previous conversation context:\n"
        for msg in history[-MAX_HISTORY_LENGTH:]:
            if msg['role'] == 'Human':
                full_prompt += f"User {user_name}: {msg['content']}\n"
            elif msg['role'] == 'Assistant':
                full_prompt += f"Assistant (You): {msg['content']}\n"
        
        full_prompt += f"\nCurrent context: The user {user_name} has just sent a new message in the conversation.\n"
        full_prompt += f"User {user_name}'s message: {prompt}\n\n"
        full_prompt += "Please generate a response to the user's latest message, taking into account the conversation history and context provided above. Respond as the AI assistant:\n"

        response = await asyncio.to_thread(model.generate_content, full_prompt)
        final_response = replace_bot_name_with_user(response.text, user_name)
        
        # Update conversation history with the user's message and the bot's response
        history.append({"role": "Human", "content": prompt})
        history.append({"role": "Assistant", "content": final_response})
        conversation_history[user_id] = history[-MAX_HISTORY_LENGTH:]
        
        return final_response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I'm having trouble coming up with a response right now. Try again later!"


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    
    # Set the status of the bot
    await bot.change_presence(
        activity=discord.Streaming(
            name="Sparking up conversations in the Galactic Ark server! ⚡",
            url="https://discord.gg/SauNXfapR7"
        ),
        status=discord.Status.online
    )
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# Command error handler
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True)
    else:
        logger.error(f"Command error: {error}")
        if interaction.response.is_done():
            await interaction.followup.send(
                "An error occurred while processing your command. Please try again later.",
                ephemeral=True)
        else:
            await interaction.response.send_message(
                "An error occurred while processing your command. Please try again later.",
                ephemeral=True)

# New command to reset conversation
@bot.tree.command(name="new_conversation", description="Start a new conversation")
async def new_conversation(interaction: discord.Interaction):
    user_id = interaction.user.id
    conversation_history[user_id] = []
    await interaction.response.send_message("Your conversation history has been reset. Let's start anew!", ephemeral=True)

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
    await interaction.response.defer()
    prompt = f"Answer this science question: {question}"
    response = await generate_response(prompt, interaction.user.display_name, interaction.user.id)
    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await interaction.followup.send(response[i:i+2000])
    else:
        await interaction.followup.send(response)

# Math command
@bot.tree.command(name="math", description="Solve a math problem")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def math(interaction: discord.Interaction, problem: str):
    await interaction.response.defer()
    prompt = f"Solve this math problem and explain the solution: {problem}"
    response = await generate_response(prompt, interaction.user.display_name, interaction.user.id)
    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await interaction.followup.send(response[i:i+2000])
    else:
        await interaction.followup.send(response)

# Mythology command
@bot.tree.command(name="mythology", description="Provide information about a mythology topic")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def mythology(interaction: discord.Interaction, topic: str):
    await interaction.response.defer()
    prompt = f"Provide information about this mythology topic with the insight and serenity of Shree Krishna: {topic}"
    response = await generate_response(prompt, interaction.user.display_name, interaction.user.id)
    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await interaction.followup.send(response[i:i+2000])
    else:
        await interaction.followup.send(response)

# Joke command
@bot.tree.command(name="joke", description="Tell a joke")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def joke(interaction: discord.Interaction, topic: str = None):
    await interaction.response.defer()
    if topic:
        prompt = f"Tell a funny joke about {topic}"
    else:
        prompt = "Tell a new random funny joke"
    response = await generate_response(prompt, interaction.user.display_name, interaction.user.id)
    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await interaction.followup.send(response[i:i+2000])
    else:
        await interaction.followup.send(response)

# Story command
@bot.tree.command(name="story", description="Tell a short story")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def story(interaction: discord.Interaction, theme: str = None):
    await interaction.response.defer()
    if theme:
        prompt = f"Tell a short story about {theme}"
    else:
        genres = ["sci-fi", "fantasy", "mystery", "romance", "adventure"]
        prompt = f"Tell a short {random.choice(genres)} story"

    response = await generate_response(prompt, interaction.user.display_name, interaction.user.id)

    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await interaction.followup.send(response[i:i+2000])
    else:
        await interaction.followup.send(response)

# Advice command
@bot.tree.command(name="advice", description="Get life advice on a topic")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def advice(interaction: discord.Interaction, topic: str):
    try:
        logger.info(f"Advice command called with topic: {topic}")
        
        await interaction.response.defer()
        
        prompt = f"""Provide life advice on topic mentioned below with the divine wisdom and compassion of Shree Krishna. 
        Include insights from the Bhagavad Gita and relevant parables to illuminate the advice. Also, include a relevant quote from a Disney or Dreamworks movie to support the advice.:
        {topic}"""

        logger.info("Generating response...")
        response = await generate_response(prompt, interaction.user.display_name, interaction.user.id)
        logger.info(f"Response generated. Length: {len(response)}")

        if len(response) > 2000:
            logger.info("Response longer than 2000 characters. Splitting...")
            for i in range(0, len(response), 2000):
                await interaction.followup.send(response[i:i + 2000])
                logger.info(f"Sent chunk of response. Length: {len(response[i:i + 2000])}")
        else:
            await interaction.followup.send(response)
            logger.info("Sent full response")

    except Exception as e:
        logger.error(f"Error in advice command: {e}", exc_info=True)
        await interaction.followup.send(
            "An error occurred while processing your request. Please try again later.",
            ephemeral=True)

# Ask Me Anything command
@bot.tree.command(name="ask", description="Ask me anything")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    # Filter vulgarity or inappropriate content
    if any(vulgar_word in question.lower() for vulgar_word in ["vulgarity", "inappropriate"]):
        await interaction.followup.send("Sorry, I can't answer that question.", ephemeral=True)
        return

    prompt = f"Answer this question with: {question}"
    response = await generate_response(prompt, interaction.user.display_name, interaction.user.id)
    if len(response) > 2000:
        for i in range(0, len(response), 2000):
            await interaction.followup.send(response[i:i+2000])
    else:
        await interaction.followup.send(response)

# Respond to mentions and engage in small talk
@bot.event
@bot.event
async def on_message(message):
    # Check if the message is from the bot itself
    if message.author == bot.user:
        return

    # Handle Direct Messages
    if message.guild is None and message.author != bot.user:  # Check if it's a DM and not from the bot itself
        await message.author.send("Hey there! 🌟 To make the most of our interactions, please join the Galactic Ark server by clicking [here](https://discord.gg/SauNXfapR7). This will unlock all the features and capabilities I have to offer. Can't wait to see you there! 🚀✨")
    else:
        # Handle messages in server channels
        user_name = message.author.display_name
        user_id = message.author.id
        content = message.content
        bot_mention_pattern = re.escape(f"<@{bot.user.id}>")
        cleaned_content = re.sub(bot_mention_pattern, '', content).strip()

        if bot.user.mentioned_in(message):
            if any(phrase in cleaned_content.lower() for phrase in
                   ["who are you", "what can you do", "tell me about yourself", "what is your name"]):
                response = generate_bot_intro()
                if len(response) > 2000:
                    await message.reply(response[:2000])
                    await message.reply(response[2000:])
                else:
                    await message.reply(response)
            else:
                # Handle replies
                if message.reference:
                    try:
                        original_message = await message.channel.fetch_message(message.reference.message_id)
                        if original_message.author == bot.user:
                            # If the original message was from the bot, treat the reply as a continuation
                            prompt = cleaned_content
                            response = await generate_response(prompt, user_name, user_id)
                            if len(response) > 2000:
                                await message.reply(response[:2000])
                                await message.reply(response[2000:])
                            else:
                                await message.reply(response)
                        else:
                            # If the original message was not from the bot, handle it as a new message
                            prompt = f"Respond to this message: {cleaned_content}"
                            response = await generate_response(prompt, user_name, user_id)
                            if len(response) > 2000:
                                await message.reply(response[:2000])
                                await message.reply(response[2000:])
                            else:
                                await message.reply(response)
                    except Exception as e:
                        logger.error(f"Error fetching original message: {e}")
                        await message.reply("I encountered an error while processing your message. Please try again later.")
                else:
                    # Handle new messages
                    prompt = f"Respond to this message: {cleaned_content}"
                    response = await generate_response(prompt, user_name, user_id)
                    if len(response) > 2000:
                        await message.reply(response[:2000])
                        await message.reply(response[2000:])
                    else:
                        await message.reply(response)

    await bot.process_commands(message)


# Run the bot
webserver.keep_alive()
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
