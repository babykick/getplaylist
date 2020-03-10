import sys
import subprocess
import optparse
import shlex
import re
from urllib.parse import urlparse, urljoin

import requests
from lxml.html import fromstring


# extractor 命名规则 xxxxDownloader
class YoukuDownloader:
    # fetcher = 'youtube-dl -o "{save_dir}/%(title)s.%(ext)s" --proxy ""'
    fetcher = 'youtube-dl -o "{save_dir}/%(title)s.%(ext)s"'
    
    @classmethod
    def extract(cls, page):
        return fromstring(page).xpath('(//div[@class="anthology-content"])[1]/div[@class="pic-text-item"]/a/@href')


class BilibiliDownloader:
    fetcher = 'youtube-dl -o "{save_dir}/%(title)s.%(ext)s" --proxy ""'
    
    @classmethod 
    def extract(cls, page):
        data = re.search(r'window.__INITIAL_STATE__=(.*)')
        return [urljoin('https://bilibili.com', lnk) for lnk in fromstring(page).xpath('//div[@class="cur-list"]/ul[@class="list-box"]/li/a/@href')]


def fetch_page(url):
    s = requests.session()
    s.headers = {
                 'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                 'referer': f'http://{urlparse(url).netloc}'
                 }

    r = s.get(url)
    return r.text


def get_extractor(url):
    domain_name = urlparse(url).netloc.split('.')[-2]
    ex = globals().get(f'{domain_name.title()}Downloader')
    if ex:
        return ex
    else:
        raise NotImplementedError(f'No extractor found for {domain_name}')


def download_list(url, save_dir):
    save_dir = save_dir.replace('\\', '/')
    extractor = get_extractor(url)
    page = fetch_page(url)
    print(page)
    urls = extractor.extract(page)
    print('Total', len(urls))
    for url in urls:
        print(url)
        cmd = f'{extractor.fetcher.format(save_dir=save_dir)} "{url}"'
        print(cmd)
        cmd = shlex.split(cmd)
        subprocess.run(cmd)


if __name__ == '__main__':
    # url = sys.argv[-1]
    p = optparse.OptionParser()
    p.add_option('-d', '--save-dir', action='store', dest='save_dir', default='.')
    option, args = p.parse_args()
    url = args[0]
    download_list(url, option.save_dir)