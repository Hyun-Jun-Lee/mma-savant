from core.utils import download_html

url = "http://ufcstats.com/event-details/39f68882def7a507"

html_path = download_html(url)
print(html_path)