import requests
from bs4 import BeautifulSoup
from urllib import parse
from flask import Flask, Response, send_file
from flask_cors import CORS
from io import BytesIO
import logging

logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=logging.DEBUG, filename='./log/log')

app = Flask(__name__)
CORS(app)

@app.errorhandler(OSError)
def oserror_handler(e):
    logging.warning(e)
    return Response("Network error", status=400)

@app.route("/")
def index():
    return "example: http://DOMAIN/http://www.baidu.com"

@app.route("/<path:domain>", methods=['GET'])
def proxy(domain):
    if parse.urlparse(domain).scheme != '':
        res = requests.get(domain)
        soup = BeautifulSoup(res.content)
        icon_link = soup.find("link", {"rel":"icon"})
        image_url = parse.urljoin(domain, "favicon.ico")
        if icon_link:
            href = icon_link.get("href")
            if parse.urlparse(href).scheme == "":
                image_url = parse.urljoin(domain, href)
            else:
                image_url = href
        logging.info(image_url)
        image = requests.get(image_url).content
        return send_file(BytesIO(image), mimetype="image/x-icon", download_name='favicon.ico')
    return Response(f"'{domain}' Lack schema", status=400)


if __name__ == "__main__":
    app.run("0.0.0.0", 5000)