import discord
import os
from dotenv import load_dotenv
from spreadsheet import pull_channel
import gspread
from embed import create_embed, add_field
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option

load_dotenv()

# Intents
intents = discord.Intents().default()
intents.members = True
intents.reactions = True

# Bot Instance
client = discord.Client(intents=intents)

# Slash Command Instance
slash = SlashCommand(client, sync_commands=True)

# All of the "Extensions" or "Cogs" the bot starts with
startup_extensions = []

gc = gspread.service_account(f"{os.getcwd()}/service_account.json")

sheet = gc.open_by_key("1aFqCSU4vQUHyJIl44-3beRNqIvo7kutQ86nu8SpVZkE")

mod_queue_int = 806718856924102656

guilds = [742522966998515732]


@client.event
async def on_ready():
    print(f"Logged in as {client.user}.")
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, name="/decision command."
        )
    )
    # await pull_channel(client, 798929515090804776)


@slash.slash(
    name="decision",
    description="Allows you to record a decision to the channel and spreadsheet.",
    guild_ids=guilds,
    options=[
        create_option(
            name="School",
            description="The school you were accepted to.",
            option_type=3,
            required=True,
        ),
        create_option(
            name="Program",
            description="The program you applied to.",
            option_type=3,
            required=True,
        ),
        create_option(
            name="Average",
            description="Your top 6 average",
            option_type=3,
            required=True,
        ),
        create_option(
            name="Accepted_Date",
            description="The date you were accepted to the program.",
            option_type=3,
            required=True,
        ),
        create_option(
            name="Type",
            description="Applicant Type: 101/105",
            option_type=3,
            required=True,
        ),
        create_option(
            name="Other",
            description="Other information you want to provide",
            option_type=3,
            required=False,
        ),
    ],
)
async def _decision(
    ctx, school: str, program: str, average: str, date: str, app_type: str, other=None
):
    waterloo_list = ["waterloo", "uw", "university of waterloo", "uwaterloo"]
    waterloo_admission = False
    for word in waterloo_list:
        if word in school.lower():
            waterloo_admission = True

    average = average.replace("%", "")

    embed = create_embed("Decision Verification Required", "", "magenta")
    add_field(embed, "User", ctx.author.mention, True)
    add_field(embed, "User ID", ctx.author.id, True)
    add_field(embed, "School", school, True)
    add_field(embed, "Program", program, True)
    add_field(embed, "Waterloo Acceptance", waterloo_admission, True)
    add_field(embed, "Average", average, True)
    add_field(embed, "Date Accepted", date, True)
    add_field(embed, "101/105", app_type, True)
    if other:
        add_field(embed, "Other", other, True)
    else:
        add_field(embed, "Other", "None", True)

    mod_queue = client.get_channel(mod_queue_int)
    mod_queue_message = await mod_queue.send(embed=embed)

    emojis = ["✅", "❌"]
    for emoji in emojis:
        await mod_queue_message.add_reaction(emoji)

    await ctx.send("Information Successfully Sent to the Moderators.")


@client.event
async def on_raw_reaction_add(ctx):
    if ctx.member.bot:
        return

    message = await client.get_channel(ctx.channel_id).fetch_message(ctx.message_id)

    if mod_queue_int != int(ctx.channel_id):
        return

    message_embeds = message.embeds[0]

    decisions = 776621660341665802
    uw_decisions = 798929515090804776

    accepted_role = 789245639011729438

    if message_embeds.title != "Decision Verification Required":
        return

    other = None

    if ctx.emoji.name == "❌":
        await message.delete()
        return
    elif ctx.emoji.name == "✅":
        embeds = message_embeds.fields
        user_id = embeds[1].value
        school = embeds[2].value
        program = embeds[3].value
        waterloo_acceptance = embeds[4].value
        average = embeds[5].value
        date_accepted = embeds[6].value
        app_type = embeds[7].value
        other = embeds[8].value

    if other == "None":
        other = None

    user = client.get_user(int(user_id))

    if eval(waterloo_acceptance):
        program_school = program
    else:
        program_school = f"{school} - {program}"
    print(program_school)
    embed = create_embed(
        f"{program_school}", f"{user.name}#{user.discriminator}", "orange"
    )
    add_field(embed, "Average", average, True)
    add_field(embed, "Date Accepted", date_accepted, True)
    add_field(embed, "Applicant Type", app_type, True)
    if other is not None:
        add_field(embed, "Other", other, True)
    embed.set_thumbnail(url=user.avatar_url)
    if eval(waterloo_acceptance):
        worksheet = sheet.worksheet("Waterloo")
        channel = client.get_channel(uw_decisions)
        await channel.send(f"{user.mention}", embed=embed)

        guild = client.get_guild(ctx.guild_id)
        accepted_role = guild.get_role(accepted_role)
        member = guild.get_member(int(user_id))
        await member.add_roles(accepted_role)
    else:
        worksheet = sheet.worksheet("Other")
        channel = client.get_channel(decisions)
        await channel.send(f"{user.mention}", embed=embed)

    user_str = f"{user.name}#{user.discriminator}"

    # Adding to worksheet
    wsheet_list = [program_school, average, date_accepted, user_str, app_type]
    if other is not None:
        wsheet_list.append(other)

    worksheet.append_row(wsheet_list)

    dm_channel = user.dm_channel
    if dm_channel is None:
        await user.create_dm()
        dm_channel = user.dm_channel

    embed = create_embed(
        "Decision Added Successfully", f"{program_school}", "light_green"
    )
    add_field(embed, "Average", average, True)
    add_field(embed, "Date Accepted", date_accepted, True)
    add_field(embed, "Applicant Type", app_type, True)
    if other is not None:
        add_field(embed, "Other", other, True)

    await dm_channel.send(embed=embed)

    await message.delete()


# Runs the bot with the token in .env
client.run(os.environ.get("bot_token"))