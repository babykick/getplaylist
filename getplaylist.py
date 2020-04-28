import os
import sys
import subprocess
import argparse
import shlex
import re
import json
from urllib.parse import urlparse, urljoin

import requests
from lxml.html import fromstring


cur_dir = os.path.abspath(os.path.dirname(__file__))


def get_sys_proxy():
    import urllib
    p = urllib.request.getproxies()   
    return p.get('https', '') or p.get('https', '')


def _argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='?', help='target playlist url')
    parser.add_argument('--listfile', help='file containing video links')
    parser.add_argument('--savedir', default=cur_dir, help='directory downloaded video saved')
    parser.add_argument('--noindex', action='store_true', help='use index or not in format')
    
    return parser.parse_args()


args = _argparse()


def fetch_page(url):
    s = requests.session()
    s.headers = {
                 'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                 'referer': f'http://{urlparse(url).netloc}'
                 }

    r = s.get(url)
    return r.text


class BaseDownloader:
    use_origin = False
    no_index = False

    def __init__(self, **args):
        self.no_index = self.no_index or args.pop('noindex')
        self.save_dir = args.pop('savedir', '')
        self.proxy = args.pop('proxy', '')
        self.url = args.pop('url')
        self.listfile = args.pop('listfile')
    
    def get_fetcher(self):
        # self.save_dir = self.save_dir.replace("\\", "/")
        format = os.path.join(self.save_dir, f'{"" if self.no_index else "%(playlist_index)s - "}%(title)s.%(ext)s')
        return f'youtube-dl "{self.url}" -o "{format}" {self.get_extra_args()} {"--proxy " + self.proxy if self.proxy else ""}' 

    def get_extra_args(self):
        return ''

    def download(self):
        save_dir, listfile = self.save_dir, self.listfile
        info = []
        if self.url:
            if self.use_origin:
                cmd = self.get_fetcher()
                print(cmd)
                subprocess.run(shlex.split(cmd))
                return
            else:
                page = fetch_page(self.url)
                info = self.extract(page)

        if listfile and os.path.exists(listfile):
            info = [{'url': line} for line in open(listfile)]
        
        if len(info) == 0:
            print('No playlist or video url provided')
            exit()

        print('Total', len(info))
        for v in info:
            url = v['url']
            print(url)
            if 'title' in v:
                cmd = self.get_fetcher().replace(r'%(title)s', v['title'])
            else:
                cmd = self.get_fetcher()
            print(cmd)
            cmd = shlex.split(cmd)
            subprocess.run(cmd)


# extractor 命名规则 xxxxDownloader
class YoukuDownloader(BaseDownloader):

    def extract(cls, page):
        return [ {'url': url} for url in 
                     fromstring(page).xpath('(//div[@class="anthology-content"])[1]/div[@class="pic-text-item"]/a/@href')]


class BilibiliDownloader(BaseDownloader):
    no_index = True

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

    def get_extra_args(self):
        return '--yes-playlist'


def get_downloader(url):
    domain_name = urlparse(url).netloc.split('.')[-2]
    ex = globals().get(f'{domain_name.title()}Downloader')
    if ex:
        return ex
    else:
        raise NotImplementedError(f'No extractor found for {domain_name}')
    

def download_list(args):
    dl = get_downloader(args.url)(**vars(args))
    dl.download()


def main():
    download_list(args)


if __name__ == '__main__':
    main()
    
