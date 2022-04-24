import os
import logging
import datetime
import requests
import fake_useragent
from io import BytesIO
from urllib import parse
from diskcache import Cache
from flask_cors import CORS
from bs4 import BeautifulSoup
from flask import Flask, Response, send_file, request


app = Flask(__name__)
CORS(app)
fu = fake_useragent.UserAgent()
logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=logging.DEBUG, filename='./log/log')
cache = Cache(directory="./cache", size_limit=2 ** 30)


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
    image_urls = list(map(lambda e:parse.urljoin(e, "favicon.ico"), [url, domain]))
    image_urls = list(set(image_urls))
    mimetype = "image/x-icon"
    res = requests.get(url, headers=get_header())
    soup = BeautifulSoup(res.content, features="html.parser")
    icon_link = soup.find("link", {"rel":"icon"}) or soup.find("link", {"rel":"shortcut"})
    if icon_link:
        image_url = icon_link.get("href")
        type = icon_link.get("type")
        logging.info("icon_link: %s, %s", image_url, type)
        if not parse.urlparse(image_url).scheme:
            image_urls = list(map(lambda e:parse.urljoin(e, image_url), [url, domain]))
        if type:
            mimetype = type
    logging.info("image_urls: %s", ", ".join(image_urls))
    download_name = os.path.basename(parse.urlparse(image_urls[0]).path)
    res = Response(status=500)
    for image_url in image_urls:
        image_res = requests.get(image_url, headers=get_header())
        if image_res.status_code != 200:
            res = Response(f"'{image_url}' Can't get", status=image_res.status_code)
        elif len(image_res.content) == 0:
            res = Response(f"'{image_url}' Response length is 0", status=400)
        else:
            res = send_file(BytesIO(image_res.content), mimetype=mimetype, download_name=download_name)
            break
    cache.set(url, res, expire=datetime.timedelta(weeks=4).total_seconds())
    return res


if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
    cache.close()