# Twint2

An Attempt to Revive the Original Twint Osint tool with the use of a different backend which is muskviewer (originally called twuko).
Back in 2021/2022 I programmed my own tools for using twitter since the twint api had a tendency to misbehave if I wasn't playing
my cards right and with the recent lockout I stopped completely. However I saw an opportunity with this site since I had used it in my 
earlydays of programming for user-targeted osint so I pulled out some old projects I had that were in the cobwebs and starting to 
modernize my original techniques I was using a little bit and now here we are. Know that the commandline frontend is being worked on but the Object Oriented backend is now ready for use...



## Plans with this tool for the Future 

- Move to Curl-ffi away from aiohttp if Tor is sucessful with muskviewer with it. (Just need to bypass that damned IUAM (I'm under attack mode) page)
- Output to other formats such as json on all attrs models



## How To Use The Backend
```python

import asyncio
from twint2 import Client


async def main():
    async with Client() as client:
        page_1 = await client.get_user("robtopgames")
        for tweet in page_1.get_tweets():
            text = tweet.text.replace('\n', ' ')
            print(f"{tweet.author}: {text}")

if __name__ == "__main__":
    asyncio.run(main())
```

