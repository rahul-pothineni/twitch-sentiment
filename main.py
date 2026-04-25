import os
from pathlib import Path

from dotenv import load_dotenv

from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import ChannelChatMessageEvent
from twitchAPI.type import AuthScope
import asyncio
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["SSL_CERT_DIR"] = os.path.dirname(certifi.where())

load_dotenv()
APP_ID = os.getenv('TWITCH_APP_ID')
APP_SECRET = os.getenv('TWITCH_APP_SECRET')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL')

# dev user auth scopes
SCOPES = [AuthScope.USER_READ_CHAT]

# Handle chat messages
async def on_chat(data: ChannelChatMessageEvent): 
    e = data.event
    print(f"[{e.broadcaster_user_login}] {e.chatter_user_login}: {e.message.text}")


async def run():
    twitch = await Twitch(APP_ID, APP_SECRET)

    #dev user authentication
    helper = UserAuthenticationStorageHelper(twitch, SCOPES)
    await helper.bind()

    #dev user login
    me = await first(twitch.get_users())

    #target channel
    target = await first(twitch.get_users(logins=[TARGET_CHANNEL]))
    if target is None:
        raise SystemExit(f"channel not found: {TARGET_CHANNEL}")

    print(f"authed as: {me.login}")
    print(f"monitoring: {target.login} (id={target.id})")

    # create eventsub websocket instance and start the client.
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    # listen for chat messages
    await eventsub.listen_channel_chat_message(
        broadcaster_user_id=target.id,
        user_id=me.id,
        callback=on_chat,
    )


    # eventsub will run in its own process
    # so lets just wait for user input before shutting it all down again
    print("listening — press Ctrl+C to stop")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await eventsub.stop()
        await twitch.close()

if __name__ == "__main__":
    asyncio.run(run())