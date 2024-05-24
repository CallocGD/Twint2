from selectolax.lexbor import LexborHTMLParser, LexborNode
from attrs import define, field
from yarl import URL
import orjson
import re
from typing import AnyStr, Optional, Union
from iters import wrap_async_iter

import asyncio
import random
from aiofiles import open as aopen

async def random_backoff():
    """Used to prevent the server from rate-limiting us"""
    return await asyncio.sleep(random.uniform(0.5, 3))


# def test_file():
#     with open("test.html", "rb") as r:
#         data = r.read()
#     return data

# def test_file2():
#     with open("test2.txt", "rb") as r:
#         data = r.read()
#     return data


@define
class Image:
    src: str

    @classmethod
    def _init_from_node(cls, node: LexborNode):
        return cls(node.attrs["src"])

    @property
    def url(self) -> URL:
        """Turns the source into a yarl.URL() class object"""
        return URL(self.src)


@define
class Video:
    url: str
    type: str
    client:"Client"

    @classmethod
    def _init_from_node(cls, node: LexborNode, client:"Client"):
        video = cls.__new__(Video)
        attrs = node.attributes
        video.url = attrs["src"]
        video.type = attrs["type"]
        video.client = client
        return video

    async def download(self, filename:str): 
        """Downloads the chosen video"""
        async with aopen(filename, "wb") as w:
            async with self.client.client as client:
               async with client.get(self.url) as resp:
                   async for chunk in resp.content.iter_chunked(10240):
                        await w.write(chunk)

@define
class Tweet:
    author: str
    profile_picture: str
    text: str

    node: LexborNode
    """allows lower level acess to the tweet"""

    cache: dict = field(factory=dict)

    @classmethod
    def _init_from_node(cls, node: LexborNode):
        tweet = cls.__new__(Tweet)
        img = node.css_first("img").attributes
        tweet.author = img["alt"].strip("@")
        tweet.profile_picture = img["src"]
        tweet.text = node.css_first("div.break-words").text(separator=" ", strip=True)
        tweet.node = node
        tweet.cache = {}
        return tweet

    @property
    def images(self) -> list[Image]:
        if not self.cache.get("images"):
            self.cache["images"] = list(
                map(Image._init_from_node, self.node.css("img")[1:])
            )
        return self.cache["images"]

    @property
    def videos(self) -> list[Video]:
        """Returns a list of videos if they exist"""
        if not self.cache.get("videos"):
            self.cache["videos"] = [Video._init_from_node(node, self.client) for node in self.node.css("video > source")]
        return self.cache["videos"]

    @property
    def time(self):
        """Time the tweet was posted at..."""
        if not self.cache.get("time"):
            self.cache["time"] = self.node.css_first("div.text-gray-600").text(
                strip=True
            )
        return self.cache["time"]


# class PageDelegate(ABC):
#     @abstractmethod
#     def get_tweets(self) -> list[Tweet]:
#         ...


@define
class HTMLResponseInfo:
    """HTML Response belonging to a page of tweets"""

    parser: LexborHTMLParser
    client: Optional[Union["Client"]]
    pageInfo: dict[str, str] = field(factory=dict)

    @classmethod
    def from_html(cls, data: AnyStr, client: Optional["Client"] = None):
        parser = LexborHTMLParser(data)
        # Convert pageinfo to something useful
        pageInfo = orjson.loads(
            re.sub(
                r"(\w+)\s?:",
                r'"\1":',
                parser.css_first("script")
                .text(strip=True)
                .strip("var pageInfo = ")
                .replace("'", '"'),
            ).strip(";")
        )
        return cls(parser=parser, pageInfo=pageInfo, client=client)

    @classmethod
    def from_incomplete_html(
        cls,
        data: Union[bytes, str],
        pageInfo: dict[str, str] = {},
        client: Optional["Client"] = None,
    ):
        data = (
            ("<html><body>" + data + "</body></html>")
            if isinstance(data, str)
            else (b"<html><body>" + data + b"</body></html>")
        )
        return cls(parser=LexborHTMLParser(data), pageInfo=pageInfo, client=client)

    def get_tweets(self):
        return list(
            map(Tweet._init_from_node, self.parser.css("div.masonry-item > div.tweet"))
        )

    @property
    def data_cursor(self) -> Optional[str]:
        if self.parser.html:
            if m := re.search(r"data-cursor\s*\=\"([^\"]+)\"", self.parser.html):
                return m.group(1)

    def next_url(self):
        data = self.data_cursor
        return (
            (
                URL("https://www.muskviewer.com/api")
                / self.pageInfo["screenName"]
                % {"id": self.pageInfo["id"], "cursor": data}
            )
            if data
            else None
        )

    async def get_next_page(self):
        if url := self.next_url:
            # There's only going to be a partial part of the html included so we need to add in some additional info
            return HTMLResponseInfo.from_incomplete_html(
                await self.client.get(url), self.pageInfo, self.client
            )

    def write_test_offline(self, filename: str):
        """saves the htmlpage as a file for debugging site-changes"""
        if self.parser.html:
            with open(filename + ".html", "w") as w:
                w.write(self.parser.html)

    @wrap_async_iter
    async def scrape_next_pages_recursively(self):
        page = self
        while page := await page.get_next_page():
            if page and page.get_tweets() or page.data_cursor:
                yield page
                await random_backoff()
            else:
                break


# Don't allow any recursive imports...
from .requester import Client
