import aiohttp
import asyncio


async def fetch_google_suggestions(keyword):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.text()
                return data.split(",")
            else:
                raise Exception(f"Failed to fetch suggestions for {keyword}")


def is_misspelled(keyword, suggestions):
    if keyword in suggestions:
        return False
    if len(keyword) <= 2:
        return False
    shortest_suggestions = min(suggestions, key=len)
    key_words = keyword.split()
    suggestion_words = shortest_suggestions.split()
    if len(key_words) < len(suggestion_words):
        return key_words == suggestion_words[: len(key_words)]
    if len(key_words) > len(suggestion_words):
        return True
    return True


def get_correct_keyword(keyword, suggestions):
    return min(suggestions, key=len)


async def main():
    keyword = "iphone"
    suggestions = await fetch_google_suggestions(keyword)
    print(suggestions)


if __name__ == "__main__":
    asyncio.run(main())
