import asyncio

from apify import Actor

from catalog_preflight import audit_catalog


async def main():
    async with Actor:
        result = audit_catalog(await Actor.get_input())
        # One report item per run. Configure a single dataset-item billing event
        # in Console only after cloud and spending-limit tests. No custom charge.
        await Actor.push_data(result)


if __name__ == '__main__':
    asyncio.run(main())
