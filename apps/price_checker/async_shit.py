import asyncio
import aiohttp
from apps.price_checker.models import Product

sites = []
for elem in Product.objects.all():
    sites.append(elem.url)

async def fetch_price(session, url):
    async with session.get(url) as response:
        return await response.text()

async def process_sites():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_price(session, url) for url in sites]
        results = await asyncio.gather(*tasks)
        for url, html in zip(sites, results):
            print(f"Данные с {url} получены!")

asyncio.run(process_sites())