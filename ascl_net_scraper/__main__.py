import logging

from tqdm import tqdm

from .main import scrape_index_list, scrape_details

logger = logging.getLogger("charmonium.freeze")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("freeze.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
logger.addHandler(fh)

logger = logging.getLogger("charmonium.cache.ops")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("cache.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
logger.addHandler(fh)


records = scrape_index_list(10)
for record in tqdm(records, total=len(records)):
    detailed_record = scrape_details(record.details_url)
