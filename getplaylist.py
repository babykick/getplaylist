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


cur_dir = os.path.curdir


def get_sys_proxy():
    import urllib
    p = urllib.request.getproxies()   
    return p.get('https', '') or p.get('https', '')


def _argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='?', help='target playlist url')
    parser.add_argument('--listfile', default='', help='file containing video links')
    parser.add_argument('--savedir', default=cur_dir, help='directory downloaded video saved')
    parser.add_argument('--useindex', action='store_true', help='use index or not in format')
    parser.add_argument('--displayid', default='', action='store_true', help='add display id in output template')
    parser.add_argument('--extraargs', default='', help='extra arguments')
    
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
    use_index = False
    display_id = False

    def __init__(self, **args):
        self.use_index = self.use_index or args.get('useindex', False)
        self.save_dir = args.get('savedir', '')
        self.proxy = args.get('proxy', '')
        self.url = args.get('url', '')
        self.listfile = args.get('listfile', '')
        self.display_id = args.get('displayid', '')
        self.extra_args = args.get('extraargs', '')

        self.args = args 
        
    def get_fetcher(self, url):
        # self.save_dir = self.save_dir.replace("\\", "/")
        format = os.path.join(self.save_dir, f'{"" if not self.use_index else "%(playlist_index)s - "}%(title)s({"%(display_id)s" if self.display_id else ""}).%(ext)s')
        return f'youtube-dl "{url}" -o "{format}" {self.get_extra_args()} {"--proxy " + self.proxy if self.proxy else ""}' 

    def get_extra_args(self):
        return self.extra_args
    
    def download_from_list(self, info, select_downloader=False):
        print('Total', len(info))
        for v in info:
            url = v['url'].strip()
            print(url)
            dl = get_downloader(url)(**self.args) if select_downloader else self
            print('Select', dl)
            if 'title' in v:
                cmd = dl.get_fetcher(url).replace(r'%(title)s', v['title'])
            else:
                cmd = dl.get_fetcher(url)
            print(cmd)
            cmd = shlex.split(cmd)
            subprocess.run(cmd)

    def download(self):
        save_dir = self.save_dir
        info = []
        if self.url:
            if self.use_origin:
                cmd = self.get_fetcher(self.url)
                print(cmd)
                subprocess.run(shlex.split(cmd))
                return
            else:
                page = fetch_page(self.url)
                info = self.extract(page)

        
        if len(info) == 0:
            print('No playlist or video url provided')
            exit()
        
        self.download_from_list(info)


# extractor 命名规则 xxxxDownloader
class YoukuDownloader(BaseDownloader):

    def extract(cls, page):
        return [ {'url': url} for url in 
                     fromstring(page).xpath('(//div[@class="anthology-content"])[1]/div[@class="pic-text-item"]/a/@href')]


class BilibiliDownloader(BaseDownloader):
    use_index = False

    def extract(cls, page):
        data = json.loads(re.search(r'window.__INITIAL_STATE__=(.*?);\(function\(\)\{var s', page, flags=re.DOTALL).group(1))
        aid = data['aid']
        return [
                {
                    'url': urljoin('https://bilibili.com/video', f'av{aid}?p={v["page"]}'),
                    'title': v['part']
                } for v in data['videoData']['pages']
               ]


class YoutubeDownloader(BaseDownloader):
    use_origin = True

    def get_extra_args(self):
        if  self.use_origin and self.url and 'list=' in self.url:
            return '--yes-playlist'
        return ""


class GenericDownloader(BaseDownloader):
    use_origin = True


class ListFileDownloader(BaseDownloader):
    def download(self):
        if self.listfile and os.path.exists(self.listfile):
            info = [{'url': line} for line in open(self.listfile) if line.strip()]

        self.download_from_list(info, select_downloader=True)


def get_downloader(url):
    domain_name = urlparse(url).netloc.split('.')[-2]
    ex = globals().get(f'{domain_name.title()}Downloader')
    if ex:
        return ex
    else:
        return GenericDownloader


def download_list(args):
    if args.listfile:
        dl = ListFileDownloader(**vars(args))
    elif args.url:
        dl = get_downloader(args.url)(**vars(args))
    else:
        print('url or list file not given')
        exit()
    dl.download()


def main():
    download_list(args)


if __name__ == '__main__':
    main()
    
