"""
自动化解析vscode marketplace网页，得到其插件下载地址。// 然后使用wget将其下载到本地
不使用wget，其只能在linux平台上使用。
这里使用
"""

from argparse import ArgumentParser
from urllib.request import urlopen, urlretrieve
import re
from os.path import join
import platform
import subprocess


PATTER = r"\"MoreInfo\":\{(.*?)\}"


def request_parse_page(page_url):
    req = urlopen(page_url)
    for line in req:
        res = re.search(PATTER, line.decode("utf-8"))
        if res:
            info = {}
            for kv in res.group(1).split(","):
                k, v = kv.split(":", 1)
                info[k.strip('"')] = v.strip('"')
            break
    publisher, ext_name = info["UniqueIdentifierValue"].split(".")
    version = info["VersionValue"]
    return publisher, ext_name, version


def main():
    parser = ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-t", "--to", default=None)
    args = parser.parse_args(["https://marketplace.visualstudio.com/items?itemName=ms-python.python"])
    assert args.url.startswith("https://marketplace.visualstudio.com/")

    publisher, ext_name, version = request_parse_page(args.url)
    download_url = (
        "https://{publisher}.gallery.vsassets.io/_apis/public/gallery/"
        "publisher/{publisher}/extension/{ext_name}/{version}/"
        "assetbyname/Microsoft.VisualStudio.Services.VSIXPackage"
    ).format(publisher=publisher, ext_name=ext_name, version=version)
    fn = "%s.%s-%s.vsix" % (publisher, ext_name, version)

    if args.to:
        fn = join(args.to, fn)
    if platform.system() == "Windows":
        urlretrieve(download_url, fn)
    elif platform.system() == "Linux":
        subprocess.run(["wget", download_url, "-o", fn])


if __name__ == "__main__":
    main()
