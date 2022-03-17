from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Mapping, Optional, Tuple, TypeVar, cast

import bs4
import requests
from charmonium.cache import MemoizedGroup, memoize
from tqdm import tqdm

DEFAULT_PARSER = "html5lib"
group = MemoizedGroup(fine_grain_persistence=True, size="10MiB")


@dataclass
class CodeRecord:
    """Information about a code representing one entry in <https://ascl.net/code/all>."""

    ascl_id: Optional[Tuple[int, int]]
    title: str
    credit: List[str]
    abstract: str
    details_url: str

    def get_details(self) -> DetailedCodeRecord:
        return cast(DetailedCodeRecord, scrape_details(self.details_url))


def parse_ascl_id(ascl_id_str: str) -> Optional[Tuple[int, int]]:
    if m := re.match(r"\[ascl:(\d+).(\d+)\]", ascl_id_str):
        return (int(m.group(1)), int(m.group(2)))
    else:
        return None


_T = TypeVar("_T")


def unwrap(obj: Optional[_T]) -> _T:
    if obj is None:
        raise ValueError("Unable to parse page")
    return obj


@memoize(group=group)
def scrape_index(
    max_count: Optional[int] = None,
    verbose: bool = True,
) -> List[CodeRecord]:
    """Get `max_count` entries from <https://ascl.net/code/all>.

    Pass `None` to get all entries.

    This function caches the result, so if it is called with the same `max_count`, the result can be loaded from disk.
    """
    return list(scrape_index_lazy(max_count, verbose))


def scrape_index_lazy(
    max_count: Optional[int] = None,
    verbose: bool = True,
) -> Iterable[CodeRecord]:
    max_count = max_count if max_count is not None else 300000
    # 300000 ~ 100 * current value on 2022-03-10
    response = requests.get(f"https://ascl.net/code/all/limit/{max_count}")
    soup = bs4.BeautifulSoup(response.text, DEFAULT_PARSER)
    items = list(soup.select("div.codelist div.item"))
    u = unwrap
    item: bs4.Tag
    for item in tqdm(iter(items), total=len(items), disable=not verbose):
        assert item
        yield CodeRecord(
            ascl_id=parse_ascl_id(u(item.select_one("span.ascl_id")).text),
            title=u(item.select_one("span.title")).text.strip(),
            credit=[
                child.text for child in u(item.select_one("div.credit a")).children
            ],
            abstract=str(u(item.select_one("p"))),
            details_url=(
                "https://ascl.net/" + u(item.select_one("span.title a")).attrs["href"]
            ).replace(".net//", ".net/"),
        )


github_regex = re.compile(r"(https?://github.com/[a-zA-Z0-9\.\-/]")

@dataclass
class DetailedCodeRecord:
    """Detailed information about a code, for example <https://ascl.net/0000.000>."""

    ascl_id: Optional[Tuple[int, int]]
    title: str
    credit: List[str]
    abstract: str
    url: str
    code_sites: List[str]
    used_in: List[str]
    described_in: List[str]
    bibcode: Optional[str]
    preferred_citation_method: Optional[str]
    discuss_url: str
    views: int

    @property
    def github(self) -> Optional[str]:
        return cast(Optional[str], get_github_for(self))

@memoize(group=group)
def get_github_for(record: DetailedCodeRecord) -> Optional[str]:
    # First, see if any code_site is a github site.
    for site in record.code_sites:
        if re.match(github_regex, site):
            return site

    # Second, see if any code_site links to a github site.
    for site in record.code_sites:
        try:
            # A lot of old sites take forever to time out.
            text = requests.get(site, timeout=4).text
        except requests.exceptions.RequestException:
            # A lot of old sites are dead.
            continue
        for tag in bs4.BeautifulSoup(text).find_all("a"):
            if re.match(tag.attrs["href"], text):
                return tag.attrs["href"]

    # Third, give up.
    return None

def dl_to_dict(dl: bs4.Tag) -> Mapping[str, bs4.Tag]:
    return {
        key.text: cast(bs4.Tag, val)
        for key, val in zip(dl.find_all("dt"), dl.find_all("dd"))
    }


@memoize(group=group)
def scrape_details(
    url: str,
) -> DetailedCodeRecord:
    """Get detailed information about a code."""
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, DEFAULT_PARSER)
    item = soup.select_one("div.codelist div.item")
    assert item
    sites_soup = item.select_one("dl.sites")
    sites = dl_to_dict(sites_soup) if sites_soup else {}
    bibcode = item.select_one("dl.sites.bibcode > dd")
    cite_method = item.select_one("div.cite_method")
    u = unwrap
    return DetailedCodeRecord(
        ascl_id=parse_ascl_id(u(item.select_one("span.ascl_id")).text),
        title=u(item.select_one("span.title")).text.strip(),
        credit=[child.text for child in u(item.select_one("div.credit a")).children],
        abstract=str(item.select_one("p")),
        url=url,
        code_sites=(
            [link.attrs["href"] for link in sites["Code site:"].select("a")]
            if "Code site:" in sites
            else []
        ),
        used_in=(
            [link.attrs["href"] for link in sites["Used in:"].select("a")]
            if "Used in:" in sites
            else []
        ),
        described_in=(
            [link.attrs["href"] for link in sites["Described in:"].select("a")]
            if "Described in:" in sites
            else []
        ),
        bibcode=bibcode.text if bibcode else None,
        preferred_citation_method=str(cite_method.select_one("p"))
        if cite_method
        else None,
        discuss_url=u(item.select_one("div.discuss > a")).attrs["href"],
        views=int(u(item.select_one("div.views")).text[7:]),
    )
