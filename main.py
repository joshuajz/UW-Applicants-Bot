import discord
import os
from dotenv import load_dotenv
from spreadsheet import pull_channel
import gspread
from embed import create_embed, add_field
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice

load_dotenv()

# Intents
intents = discord.Intents().default()
intents.members = True
intents.reactions = True

# Bot Instance
client = discord.Client(intents=intents)

# Slash Command Instance
slash = SlashCommand(client, sync_commands=True)
# Load Service Account and Open Spreadsheet
sheet = gspread.service_account(f"{os.getcwd()}/service_account.json").open_by_key(
    os.environ.get("GOOGLE_SHEET_KEY")
)


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
    guild_ids=[int(os.environ.get("GUILD"))],
    options=[
        create_option(
            name="School",
            description="The school that a decision was made for.",
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
            name="Status",
            description="Decision Type",
            option_type=3,
            required=True,
            choices=[
                create_choice(name="Accepted", value="Accepted"),
                create_choice(name="Rejected", value="Rejected"),
                create_choice(name="Waitlisted", value="Waitlisted"),
                create_choice(name="Deferred", value="Deferred"),
            ],
        ),
        create_option(
            name="Average",
            description="Your top 6 average",
            option_type=3,
            required=True,
        ),
        create_option(
            name="Date",
            description="The date you were given a decision.",
            option_type=3,
            required=True,
        ),
        create_option(
            name="Type",
            description="Applicant Type",
            option_type=3,
            required=True,
            choices=[
                create_choice(name="101 (Ontario)", value="101"),
                create_choice(name="105 (International)", value="105F"),
                create_choice(name="105 (Domestic -> Not Ontario)", value="105D"),
            ],
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
    ctx,
    school: str,
    program: str,
    status: str,
    average: str,
    date: str,
    app_type: str,
    other=None,
):
    aliases = ["waterloo", "uw", "university of waterloo", "uwaterloo"]
    waterloo_decision = True if school.lower() in aliases else False

    average = average.replace("%", "")

    colour = "magenta"
    if status == "Accepted":
        colour = "light_green"
    elif status == "Waitlisted":
        colour = "orange"
    elif status == "Deferred":
        colour = "yellow"
    elif status == "Rejected":
        colour = "red"

    embed = create_embed("Decision Verification Required", "", colour)
    add_field(embed, "User", ctx.author.mention, True)
    add_field(embed, "User ID", ctx.author.id, True)
    add_field(embed, "School", school, True)
    add_field(embed, "Program", program, True)
    add_field(embed, "Status", status, True)
    add_field(embed, "Waterloo Decision", waterloo_decision, True)
    add_field(embed, "Average", average, True)
    add_field(embed, "Decision Made On", date, True)
    add_field(embed, "101/105", app_type, True)
    if other:
        add_field(embed, "Other", other, True)
    else:
        add_field(embed, "Other", "None", True)

    mod_queue = client.get_channel(int(os.environ.get("MOD_QUEUE")))
    mod_queue_message = await mod_queue.send(embed=embed)

    for emoji in ["✅", "❌"]:
        await mod_queue_message.add_reaction(emoji)

    await ctx.send("Information Successfully Sent To The Moderators For Review.")


@client.event
async def on_raw_reaction_add(ctx):
    if ctx.member.bot:
        return

    message = await client.get_channel(ctx.channel_id).fetch_message(ctx.message_id)

    if int(os.environ.get("MOD_QUEUE")) != int(ctx.channel_id):
        return

    message_embeds = message.embeds[0]

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
        status = embeds[4].value
        waterloo_decision = embeds[5].value
        average = embeds[6].value
        date_of_decision = embeds[7].value
        app_type = embeds[8].value
        other = embeds[9].value

    if other == "None":
        other = None

    user = client.get_user(int(user_id))

    if eval(waterloo_decision):
        program_school = program
    else:
        program_school = f"{school} - {program}"

    colour = "orange"
    if status == "Accepted":
        colour = "light_green"
    elif status == "Waitlisted":
        colour = "orange"
    elif status == "Deferred":
        colour = "yellow"
    elif status == "Rejected":
        colour = "red"

    embed = create_embed(
        f"{program_school}", f"{user.name}#{user.discriminator}", colour
    )
    add_field(embed, "Status", status, True)
    add_field(embed, "Average", average, True)
    add_field(embed, "Decision Made On", date_of_decision, True)
    add_field(embed, "Applicant Type", app_type, True)
    if other is not None:
        add_field(embed, "Other", other, True)
    embed.set_thumbnail(url=user.avatar_url)
    if eval(waterloo_decision):
        worksheet = sheet.worksheet("Waterloo")
        channel = client.get_channel(int(os.environ.get("WATERLOO_DECISIONS")))
        await channel.send(f"{user.mention}", embed=embed)

        if status == "Accepted":
            guild = client.get_guild(ctx.guild_id)
            accepted_role = guild.get_role(int(os.environ.get("ACCEPTED_ROLE")))
            member = guild.get_member(int(user_id))
            await member.add_roles(accepted_role)
    else:
        worksheet = sheet.worksheet("Other")
        channel = client.get_channel(int(os.environ.get("DECISIONS")))
        await channel.send(f"{user.mention}", embed=embed)

    user_str = f"{user.name}#{user.discriminator}"

    # Adding to worksheet
    wsheet_list = [
        status,
        program_school,
        average,
        date_of_decision,
        user_str,
        app_type,
    ]
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
    add_field(embed, "Status", status, True)
    add_field(embed, "Average", average, True)
    add_field(embed, "Decision Made On", date_of_decision, True)
    add_field(embed, "Applicant Type", app_type, True)
    if other is not None:
        add_field(embed, "Other", other, True)

    await dm_channel.send(embed=embed)

    await message.delete()


# Runs the bot with the token in .env
client.run(os.environ.get("BOT_TOKEN"))