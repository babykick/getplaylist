# Usage

Example: 
```
> getplaylist "https://www.youtube.com/watch?v=AkFqg5wAuFk&list=PLxYReOMcJaFfGz1daUgyTUh9SerOLl3Vz" --savedir "D:/pantera"
> getplaylist "https://www.bilibili.com/video/BV1BJ411U7hW?from=search&seid=3542744301823873168" --savedir "D:/course"
> getplaylist --listfile list.txt
> getplaylist https://space.bilibili.com/412127397/video --pglimit 1 # 仅下载第一页
```

Command line:
```
usage: getplaylist [-h] [--listfile LISTFILE] [--savedir SAVEDIR] [--useindex]
                   [--displayid]
                   [url]

positional arguments:
  url                  target playlist url

optional arguments:
  -h, --help           show this help message and exit
  --listfile LISTFILE  file containing video links
  --savedir SAVEDIR    directory downloaded video saved
  --useindex           use index or not in format
  --displayid          add display id in output template
  ```