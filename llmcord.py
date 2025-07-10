import discord
from discord import app_commands
import requests
import re

# Load Discord bot token from token.txt
with open("token.txt", "r") as f:
    DISCORD_BOT_TOKEN = f.read().strip()

# Load model name from model.txt
with open("model.txt", "r") as f:
    OLLAMA_MODEL = f.read().strip()
    
MAX_DISCORD_LENGTH = 2000

#Clean model response by removing tags/thinking/empty lines
def extract_clean_response(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", text)
    cleaned = cleaned.strip()

    # Keep only the last meaningful paragraph
    paragraphs = [p.strip() for p in cleaned.split('\n') if p.strip()]
    return paragraphs[-1] if paragraphs else cleaned

class LlamaBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash commands synced")

client = LlamaBot()

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')

@client.tree.command(name="ask", description="Ask the LLM a question (concise reply)")
async def ask_command(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()

    final_prompt = f"{prompt}\n\nBe concise. Respond in one short paragraph."

    try:
        res = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': final_prompt,
                'stream': False
            }
        )
        raw_response = res.json().get('response', '[No reply]')
        response = extract_clean_response(raw_response)


        if len(response) > MAX_DISCORD_LENGTH:
            response = response[:MAX_DISCORD_LENGTH - 13] + "\n...[truncated]"

        await interaction.followup.send(
            f"**You asked:** {prompt}\n \n{response}"
        )

    except Exception as e:
        await interaction.followup.send(f"⚠️ Error: {e}")


client.run(DISCORD_BOT_TOKEN)
