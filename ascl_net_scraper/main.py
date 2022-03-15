from __future__ import annotations

import re
from dataclasses import dataclass
from typing import (
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    cast,
)

import bs4
import requests
from charmonium.cache import MemoizedGroup, memoize
from tqdm import tqdm

DEFAULT_PARSER = "html5lib"
group = MemoizedGroup(fine_grain_persistence=True)

@dataclass
class CodeRecord:
    ascl_id: Optional[Tuple[int, int]]
    title: str
    credit: List[str]
    abstract: str
    details_url: str


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
def scrape_index_list(
    max_count: Optional[int] = None,
    verbose: bool = True,
    parser: str = DEFAULT_PARSER,
) -> List[CodeRecord]:
    return list(scrape_index_lazy(max_count, verbose, parser))


def scrape_index_lazy(
    max_count: Optional[int] = None,
    verbose: bool = True,
    parser: str = DEFAULT_PARSER,
) -> Iterable[CodeRecord]:
    max_count = max_count if max_count is not None else 300000
    # 300000 ~ 100 * current value on 2022-03-10
    response = requests.get(f"https://ascl.net/code/all/limit/{max_count}")
    soup = bs4.BeautifulSoup(response.text, parser)
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
            details_url="https://ascl.net/"
            + u(item.select_one("span.title a")).attrs["href"],
        )


@dataclass
class DetailedCodeRecord:
    ascl_id: Optional[Tuple[int, int]]
    title: str
    credit: List[str]
    abstract: str
    url: str
    code_site: List[str]
    used_in: List[str]
    described_in: List[str]
    bibcode: Optional[str]
    preferred_citation_method: Optional[str]
    discuss_url: str
    views: int

    @staticmethod
    def from_code_record(code_record: CodeRecord) -> DetailedCodeRecord:
        return cast(DetailedCodeRecord, scrape_details(code_record.details_url))


def dl_to_dict(dl: bs4.Tag) -> Mapping[str, bs4.Tag]:
    children = list(dl.children)
    return {
        key.text: cast(bs4.Tag, val)
        for key, val in zip(children[::2], children[1::2])
    }


@memoize(group=group)
def scrape_details(
    url: str,
    parser: str = DEFAULT_PARSER,
) -> DetailedCodeRecord:
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, parser)
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
        code_site=(
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
        preferred_citation_method=str(cite_method) if cite_method else None,
        discuss_url=u(item.select_one("div.discuss > a")).attrs["href"],
        views=int(u(item.select_one("div.views")).text[7:]),
    )
