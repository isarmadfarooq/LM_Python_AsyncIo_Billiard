import aiohttp
import asyncio
import argparse
import logging
import json
from multiprocessing import Pool

logging.basicConfig(
    filename="suggestion_checker.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
)


async def fetch_google_suggestions(keyword):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    suggestions = json.loads(data)[1]
                    return suggestions
                else:
                    raise Exception(f"Failed to fetch suggestions for {keyword}")
        except Exception as e:
            print(f"Error fetching suggestions for {keyword}: {e}")
            return []


def is_misspelled(keyword, suggestions):
    if not suggestions:
        return True
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


def get_correct_keyword(suggestions):
    if suggestions:
        return min(suggestions, key=len)
    else:
        return ""


async def process_suggestion(keyword):
    try:
        suggestions = await fetch_google_suggestions(keyword)
    except Exception as e:
        logging.error(f"Error fetching suggestions for {keyword}: {e}")
        suggestions = []
    return suggestions


async def process_keyword(keyword):
    suggestions = await process_suggestion(keyword)
    misspelled = is_misspelled(keyword, suggestions)
    correct_keyword = None

    if misspelled:
        correct_keyword = get_correct_keyword(suggestions)

    reason = None if misspelled else f"Corrected to: {correct_keyword}"

    result = {
        "keyword": keyword,
        "suggestions": suggestions,
        "is_misspelled": misspelled,
        "correct_keyword": correct_keyword,
        "reason": reason,
    }
    return result


def process_keywords_parallel(keyword):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(process_keyword(keyword))


def main():
    parser = argparse.ArgumentParser(description="Google Suggestion Checker")
    parser.add_argument("keywords", nargs="+", help="List of keywords to check")
    args = parser.parse_args()

    with Pool() as pool:
        results = pool.map(process_keywords_parallel, args.keywords)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()