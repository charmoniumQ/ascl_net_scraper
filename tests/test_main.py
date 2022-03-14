from ascl_net_scraper import __version__


def test_main() -> None:
    records = scrape_index_list(10)
    for record in tqdm(records, total=len(records)):
        detailed_record = scrape_details(record.details_url)
        assert record.ascl_id == detailed_record.ascl_id
        assert record.title == detailed_record.title
        assert record.credit == detailed_record.credit
        assert record.abstract == detailed_record.abstract
        assert record.details_url == detailed_record.url

