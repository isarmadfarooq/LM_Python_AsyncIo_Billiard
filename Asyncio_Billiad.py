import aiohttp
import asyncio
import argparse
import logging
import json
from billiard import Pool

logging.basicConfig(filename="suggestion.log", level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def fetch_suggestions_for_keyword(keyword, session):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                suggestions = await response.text()
                suggestions = json.loads(suggestions)[1]
                return (keyword, suggestions)
            else:
                raise Exception(f"Failed to fetch suggestions for {keyword}")
    except Exception as e:
        return (keyword, str(e))


async def fetch_keywords(keywords):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_suggestions_for_keyword(keyword, session) for keyword in keywords
        ]
        results = await asyncio.gather(*tasks)
        return results


def get_correct_keyword(suggestions):
    if suggestions:
        return min(suggestions, key=len)
    else:
        return ""


def is_misspelled(keyword, suggestions):
    misspelled = True
    correct_keyword = None

    if suggestions:
        correct_keyword = get_correct_keyword(suggestions)
        if keyword in suggestions or len(keyword) <= 2:
            misspelled = False
            correct_keyword = keyword

        if len(keyword) > len(correct_keyword):
            misspelled = True
        elif len(keyword) < len(correct_keyword):
            misspelled = False

    result = {
        "keyword": keyword,
        "suggestions": suggestions,
        "is_misspelled": misspelled,
        "correct_keyword": correct_keyword,
        "reason": None,
    }
    return result


def process_keywords(keywords):
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(fetch_keywords(keywords))
    with Pool() as pool:
        parsed_results = pool.starmap(is_misspelled, results)

    result_json = json.dumps(parsed_results, indent=4)

    logger.info(result_json)


def main():
    parser = argparse.ArgumentParser(description="Google Suggestion Checker")
    parser.add_argument("keywords", nargs="+", help="List of keywords to check")
    args = parser.parse_args()
    process_keywords(args.keywords)


if __name__ == "__main__":
    main()
