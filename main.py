import os
import requests
from bs4 import BeautifulSoup
from urllib import parse
from flask import Flask, Response, send_file
from flask_cors import CORS
from io import BytesIO
import logging
import fake_useragent

logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=logging.DEBUG, filename='./log/log')

app = Flask(__name__)
CORS(app)
fu = fake_useragent.UserAgent()

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
    url_pr = parse.urlparse(url)
    if not url_pr.scheme:
        return Response(f"'{url}' Lack schema", status=400)
    domain = parse.urlunparse((url_pr.scheme, url_pr.netloc, "", "", "", ""))
    logging.info("domain: %s", domain)
    image_urls = list(map(lambda e:parse.urljoin(e, "favicon.ico"), [url, domain]))
    mimetype = "image/x-icon"
    res = requests.get(url, headers=get_header())
    soup = BeautifulSoup(res.content, features="html.parser")
    icon_link = soup.find("link", {"rel":"shortcut icon"})
    if icon_link:
        image_url = icon_link.get("href")
        type = icon_link.get("type")
        logging.info("icon_link: %s, %s", image_url, type)
        if not parse.urlparse(image_url).scheme:
            image_urls = list(map(lambda e:parse.urljoin(e, image_url), [url, domain]))
        if type:
            mimetype = type
    logging.info("image_urls: %s, %s", *image_urls)
    download_name = os.path.basename(parse.urlparse(image_urls[0]).path)
    res = Response(status=500)
    for image_url in image_urls:
        image_res = requests.get(image_url, headers=get_header())
        if image_res.status_code != 200:
            res = Response(f"'{image_url}' Can't get", status=image_res.status_code)
        elif len(image_res.content) == 0:
            res = Response(f"'{image_url}' Response length is 0", status=400)
        else:
            return send_file(BytesIO(image_res.content), mimetype=mimetype, download_name=download_name)
    return res


if __name__ == "__main__":
    app.run("0.0.0.0", 5000)