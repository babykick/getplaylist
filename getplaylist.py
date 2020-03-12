import sys
import subprocess
import optparse
import shlex
import re
import json
from urllib.parse import urlparse, urljoin

import requests
from lxml.html import fromstring


def get_sys_proxy():
    import urllib
    p = urllib.request.getproxies()   
    return p.get('https', '') or p.get('https', '')

PROXY = get_sys_proxy()


class BaseDownloader:
    use_origin = False


# extractor 命名规则 xxxxDownloader
class YoukuDownloader(BaseDownloader):
    # fetcher = 'youtube-dl -o "{save_dir}/%(title)s.%(ext)s" --proxy ""'
    fetcher = 'youtube-dl -o "{save_dir}/%(title)s.%(ext)s"'
    
    @classmethod
    def extract(cls, page):
        return [ {'url': url} for url in 
                     fromstring(page).xpath('(//div[@class="anthology-content"])[1]/div[@class="pic-text-item"]/a/@href')]


class BilibiliDownloader(BaseDownloader):
    fetcher = 'youtube-dl -o "{save_dir}/%(title)s.%(ext)s" '#--proxy ' + PROXY
    
    @classmethod 
    def extract(cls, page):
        data = json.loads(re.search(r'window.__INITIAL_STATE__=(.*?);\(function\(\)\{var s', page, flags=re.DOTALL).group(1))
        aid = data['aid']
        import pprint;pprint.pprint(data)
        return [
                {
                    'url': urljoin('https://bilibili.com/video', f'av{aid}?p={v["page"]}'),
                    'title': v['part']
                } for v in data['videoData']['pages']
               ]


class YoutubeDownloader(BaseDownloader):
    use_origin = True

    fetcher = 'youtube-dl -o "{save_dir}/%(playlist_index)s - %(title)s.%(ext)s" --yes-playlist'


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
    print(save_dir)
    save_dir = save_dir.replace('\\', '/')
    extractor = get_extractor(url)
    if extractor.use_origin:
        cmd = f'{extractor.fetcher.format(save_dir=save_dir)} "{url}"'
        print(cmd)
        subprocess.run(shlex.split(cmd))
    else:
        page = fetch_page(url)
        # print(page)
        info = extractor.extract(page)
        print('Total', len(info))
        for v in info:
            print(v.get('url'))
            if 'title' in v:
                cmd = extractor.fetcher.format(save_dir=save_dir).replace(r'%(title)s', v['title'])
                cmd = f'{cmd} "{url}"'
            else:
                cmd = f'{extractor.fetcher.format(save_dir=save_dir)} "{url}"'
            print(cmd)
            cmd = shlex.split(cmd)
            subprocess.run(cmd)


if __name__ == '__main__':
    # get_sys_proxy();exit()
    p = optparse.OptionParser()
    p.add_option('-d', '--save-dir', action='store', dest='save_dir', default='.')
    option, args = p.parse_args()
    url = args[0]
    download_list(url, option.save_dir)