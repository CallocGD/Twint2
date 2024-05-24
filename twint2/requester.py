from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from .user_agents import random_useragent
from typing import Optional, Union

import asyncio

# Tor Client Library (Not Working currenlty)
# from stem.process import launch_tor_with_config
# from stem.control import Controller
# import stem

from iters import wrap_async_iter


class Client:
    """Used for scraping user's tweets locally..."""

    def __init__(self, proxy_url: Optional[str] = None) -> None:
        self.proxy_url = proxy_url
        self.user_agent = random_useragent()
        # To Prevent Circular imports or recursions
        from .response_parser import HTMLResponseInfo

        self.__resp_object = HTMLResponseInfo

    @property
    def client(self):
        return ClientSession(
            # raise_for_status=True,
            connector=(
                ProxyConnector.from_url(self.proxy_url) if self.proxy_url else None
            ),
            headers={
                "User-Agent": random_useragent(),
                # TO Obfuscate against IUAM
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
        )

    async def get(self, url: str):
        async with self.client as client:
            async with client.get(url) as response:
                data = await response.read()
        return data

    async def get_user(self, username: str):
        return self.__resp_object.from_html(
            await self.get(f"https://www.muskviewer.com/{username}"), self
        )

    @wrap_async_iter
    async def scrape_tweets_recursively(self, username: str):
        page = await self.get_user(username)
        yield page.get_tweets()

    # Serves no use other than being consistant with it's subclass
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return


# Currently has issues handling cloudflare so it can only be done with reputable proxies for now...
# class TorClient(Client):
#     """Scrapes tweets over tor"""
#     # Inspired by the torrequest library
#     def __init__(self,
#         proxy_port:int = 9050 ,
#         ctrl_port:int = 9051 ,
#         password:Optional[Union[bytes, str]] = None,
#         tor_cmd:Optional[str] = None,
#         **others
#     ) -> None:

#         self.others = others
#         self.tor_cmd = tor_cmd
#         self.proxy_url = "socks5://localhost:%i" % proxy_port
#         self.password = password if password else ""


#         self.proxy_port = proxy_port
#         self.ctrl_port = ctrl_port

#         self._tor_proc = None
#         if not self._tor_process_exists():
#           self._tor_proc = self._launch_tor()

#         self.ctrl = Controller.from_port(port=self.ctrl_port)
#         self.ctrl.authenticate(password=password)

#         super().__init__(proxy_url=self.proxy_url)

#     def _launch_tor(self):
#         if not self.tor_cmd:
#             return launch_tor_with_config(
#                 config={
#                   'SocksPort': str(self.proxy_port),
#                   'ControlPort': str(self.ctrl_port)
#                 },
#                 take_ownership=True)
#         else:
#             return launch_tor_with_config(tor_cmd=self.tor_cmd,
#                 config={
#                   'SocksPort': str(self.proxy_port),
#                   'ControlPort': str(self.ctrl_port)
#                 },
#                 take_ownership=True)

#     async def rotate_exit_node(self):
#         """Roates tor exit node to another one in an asynchronous manner"""
#         # This is more optimized than using stem
#         reader , writer = await asyncio.open_connection("127.0.0.1", self.ctrl_port)
#         if self.password:
#             await writer.write(f'AUTHENTICATE "{self.password}"\r\nSIGNAL NEWNYM\r\n'.encode())
#         else:
#             await writer.write(b"AUTHENTICATE\r\nSIGNAL NEWNYM\r\n")
#         await writer.drain()

#         resp = await reader.read(1024)
#         if resp != b'250 OK\r\n250 OK\r\n':
#             raise RuntimeError("Could Not Rotate Tor Exit Node")
#         writer.close()
#         await writer.wait_closed()

#     def _tor_process_exists(self):
#         """Checks to see if Tor is up"""
#         try:
#             ctrl = Controller.from_port(port=self.ctrl_port)
#             ctrl.close()
#             return True
#         except:
#             return False

#     async def close(self):
#         """Closes tor connections to shutdown the proxy created to tor"""
#         try:
#             if self.ctrl:
#                 await asyncio.to_thread(self.ctrl.close)

#         finally:
#             if self._tor_proc:
#                 self._tor_proc.terminate()

#     async def __aenter__(self):
#         return self

#     async def __aexit__(self,*args):
#         return await self.close()
