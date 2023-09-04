from aiohttp import web
from routes import web_server
from pyrogram import Client, __version__
from configs import API_ID, API_HASH, BOT_TOKEN, LOGGER, PORT

class FilterBot(Client):

    def __init__(self):
        super().__init__(
         name="pikaFilter", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, plugins={"root": "pikaFilter"}, workers=50, sleep_threshold=5,
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.LOGGER(__name__).info(f"{me.first_name}, Pyrogram v{__version__} ile birlikte {me.username} üzerinde başladı.")

        app = web.AppRunner(await web_server())
        await app.setup()       
        await web.TCPSite(app, "0.0.0.0", PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot durdu. Hoşçakal.")

FilterBot().run()