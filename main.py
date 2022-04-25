import os
import logging
import datetime
import requests
import mimetypes
import fake_useragent
from io import BytesIO
from urllib import parse
from diskcache import Cache
from flask_cors import CORS
from thefuzz import process
from bs4 import BeautifulSoup
from flask import Flask, Response, send_file, request


app = Flask(__name__)
CORS(app)
fu = fake_useragent.UserAgent()
logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=logging.DEBUG, filename='./log/log')
cache = Cache(directory="./cache", size_limit=2 ** 30)
icon_rel_list = ["icon", "shortcut", "apple-touch-icon"]
image_mimetypes = list(filter(lambda e:e.startswith("image/"), mimetypes.types_map.values()))


def get_header(ua=fu.random):
    return {
        "User-Agent": ua
    }

@app.errorhandler(OSError)
def oserror_handler(e):
    logging.warning(e)
    return Response("Network error", status=400)

@app.route("/")
def index():
    return "example: http://DOMAIN/http://www.baidu.com"

@app.route("/<path:url>", methods=['GET'])
def proxy(url):
    logging.info("url: %s", url)
    force = request.args.get("force")
    if force is None:
        result = cache.get(url)
        if result:
            logging.info("Hit cache")
            return result
    url_pr = parse.urlparse(url)
    if not url_pr.scheme:
        return Response(f"'{url}' Lack schema", status=400)
    domain = parse.urlunparse((url_pr.scheme, url_pr.netloc, "", "", "", ""))
    logging.info("domain: %s", domain)
    for turl in [url, domain]:
        logging.info("turl: %s", turl)
        res = requests.get(turl)
        soup = BeautifulSoup(res.content, features="html.parser")
        soup.find_all("link")
        links = soup.find_all("link")
        tlinks = filter(lambda e:set(e.get("rel")) & set(icon_rel_list), links)
        tlinks = sorted(tlinks, key=lambda e:(-len(set(e.get("rel")) & set(icon_rel_list)), sum([icon_rel_list.index(i) if i in icon_rel_list else 0 for i in e.get("rel")])))
        icon_urls = []
        icon_types = []
        for tlink in tlinks:
            logging.info("tlink: %s", tlink)
            icon_urls.append(tlink.get("href"))
            icon_type = tlink.get("type")
            icon_type = process.extractOne(icon_type, image_mimetypes)[0] if icon_type else "image/x-icon"
            icon_types.append(icon_type)
            if not parse.urlparse(icon_urls[-1]).scheme:
                icon_urls[-1] = parse.urljoin(turl, icon_urls[-1])
        icon_urls.append(parse.urljoin(turl, "favicon.ico"))
        icon_types.append("image/x-icon")
        res = Response(status=500)
        for icon_url, icon_type in zip(icon_urls, icon_types):
            logging.info("icon_url: %s, icon_type: %s", icon_url, icon_type)
            icon_res = requests.get(icon_url, headers=get_header())
            if icon_res.status_code != 200:
                res = Response(f"'{icon_url}' Can't get", status=icon_res.status_code)
            elif len(icon_res.content) == 0:
                res = Response(f"'{icon_url}' Response length is 0", status=400)
            else:
                res = send_file(BytesIO(icon_res.content), mimetype=icon_type, download_name=os.path.basename(parse.urlparse(icon_url).path))
                break
        else:
            continue
        break
    cache.set(url, res, expire=datetime.timedelta(weeks=4).total_seconds())
    return res

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
    cache.close()