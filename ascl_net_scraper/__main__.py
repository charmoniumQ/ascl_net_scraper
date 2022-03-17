from .lib import scrape_index

# __name__ == "__main__" is needed so pytest ignores this.
if __name__ == "__main__":
    results = scrape_index(100)
    for result in results:
        result.get_details()
