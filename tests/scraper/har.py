from pathlib import Path

# recorded catalogue pages replayed by the offline scraper tests
HAR = Path(__file__).parent / "fixtures" / "books.har"
HAR_URL_PATTERN = "**/catalogue/page-*.html"
