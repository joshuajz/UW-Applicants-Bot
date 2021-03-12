import discord
import os
from dotenv import load_dotenv
import gspread
from time import sleep
import asyncio

load_dotenv()

gc = gspread.service_account(f"{os.getcwd()}/service_account.json")

sheet = gc.open_by_key("1aFqCSU4vQUHyJIl44-3beRNqIvo7kutQ86nu8SpVZkE")


async def pull_channel(client, id):
    channel = client.get_channel(int(id))
    if int(id) == 776621660341665802:
        worksheet = sheet.worksheet("Other")
    else:
        worksheet = sheet.worksheet("Waterloo")

    l = []
    count = 0
    i = 0
    async for message in channel.history(limit=9999999):
        msg = message.content
        msg = msg.split("\n")
        other = ", ".join(msg[4::])
        msg = msg[0:4]

        final_msg = []

        for z in msg:
            if ":" in z:
                z = z.split(":")
                # print(z)
                if z[1] is None:
                    z = z[0]
                elif z[1] == " " or z[1] == "" or z[1] == ")":
                    z = z[0]
                elif z[1][0] == " ":
                    z = z[1][1::]
                else:
                    z = z[1]
                final_msg.append(z)
            else:
                final_msg.append(z)

        final_msg.append(message.author.name + "#" + message.author.discriminator)
        final_msg.append(other)
        print(final_msg)
        worksheet.append_row(final_msg)
        count += 1
        i += 1
        if i == 50:
            i = 0
            await asyncio.sleep(120)

    print(l)
