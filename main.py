import discord
import os
from dotenv import load_dotenv
from spreadsheet import pull_channel
import gspread
from embed import create_embed, add_field

load_dotenv()

# Intents
intents = discord.Intents().default()
intents.members = True
intents.reactions = True

# Bot Instance
client = discord.Client(intents=intents)

# All of the "Extensions" or "Cogs" the bot starts with
startup_extensions = []

gc = gspread.service_account(f"{os.getcwd()}/service_account.json")

sheet = gc.open_by_key("1aFqCSU4vQUHyJIl44-3beRNqIvo7kutQ86nu8SpVZkE")

mod_queue_int = 806718856924102656


@client.event
async def on_ready():
    print(f"Logged in as {client.user}.")

    # await pull_channel(client, 798929515090804776)


@client.event
async def on_message(ctx):
    if ctx.content.lower().startswith("!decision"):
        content = ctx.content
        content = content.split(",")
        if len(content) != 4 and len(content) != 5:
            embed = create_embed(
                "!decision",
                "!decision University - Program, Percentage, Date Applied, Date Accepted, Other Information",
                "orange",
            )
            add_field(
                embed,
                "Example",
                "!decision Waterloo - Computer Science, 95, December, March 29, 101 Applicant + 100 Voluenteer Hours",
                True,
            )
            await ctx.channel.send(embed=embed)
            return
        content[0] = content[0][10::]
        waterloo_list = ["waterloo", "uw", "university of waterloo", "uwaterloo"]
        waterloo_admission = False
        for word in waterloo_list:
            if word in content[0].lower():
                waterloo_admission = True
                break

        if waterloo_admission:
            school_program = "-".join(content[0].split("-")[1::]).strip()
        else:
            school_program = content[0]

        other = None
        if len(content) == 5:
            other = content[-1]

        average = content[1].strip().replace("%", "")
        date_applied = content[2].strip()
        date_accepted = content[3].strip()

        user_embed = create_embed(
            "Succesfully Sent to Moderators",
            "Your Decision has been sent to the administrators of the server for review.  Please sit tight!",
            "light_green",
        )
        add_field(user_embed, "User", ctx.author.mention, True)
        add_field(user_embed, "School - Program", school_program, True)
        add_field(user_embed, "Waterloo Acceptance?", waterloo_admission, True)
        add_field(user_embed, "Average", average, True)
        add_field(user_embed, "Date Applied", date_applied, True)
        add_field(user_embed, "Date Accepted", date_accepted, True)
        add_field(user_embed, "Other", other, True)
        await ctx.channel.send(embed=user_embed)

        embed = create_embed("Decision Verification Required", "", "magenta")

        add_field(embed, "User", ctx.author.mention, True)
        add_field(embed, "User ID", ctx.author.id, True)
        add_field(embed, "School/Program", school_program, True)
        add_field(embed, "Waterloo Acceptance", waterloo_admission, True)
        add_field(embed, "Average", average, True)
        add_field(embed, "Date Applied", date_applied, True)
        add_field(embed, "Date Accepted", date_accepted, True)
        add_field(embed, "Other", other, True)

        mod_queue = client.get_channel(mod_queue_int)
        mod_queue_message = await mod_queue.send(embed=embed)

        emojis = ["✅", "❌"]
        for emoji in emojis:
            await mod_queue_message.add_reaction(emoji)

        # print(school_program, waterloo_admission, average, date_applied, date_accepted)


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
        for embed in message_embeds.fields:
            if embed.name == "User ID":
                user_id = embed.value
            elif embed.name == "School/Program":
                program_school = embed.value
            elif embed.name == "Waterloo Acceptance":
                waterloo_acceptance = embed.value
            elif embed.name == "Average":
                average = embed.value
            elif embed.name == "Date Applied":
                date_applied = embed.value
            elif embed.name == "Date Accepted":
                date_accepted = embed.value
            elif embed.name == "Other":
                other = embed.value

    if other == "None":
        other = None

    user = client.get_user(int(user_id))

    embed = create_embed(
        f"{program_school}", f"{user.name}#{user.discriminator}", "orange"
    )
    add_field(embed, "Average", average, True)
    add_field(embed, "Date Applied", date_applied, True)
    add_field(embed, "Date Accepted", date_accepted, True)
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
    wsheet_list = [program_school, average, date_applied, date_accepted, user_str]
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
    add_field(embed, "Date Applied", date_applied, True)
    add_field(embed, "Date Accepted", date_accepted, True)
    add_field(embed, "Waterloo?", waterloo_acceptance, True)
    if other is not None:
        add_field(embed, "Other", other, True)

    await dm_channel.send(embed=embed)

    await message.delete()


# Runs the bot with the token in .env
client.run(os.environ.get("bot_token"))