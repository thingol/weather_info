# -*- coding: utf-8 -*-
from io import BytesIO
from datetime import datetime

from PIL import Image
from flask import Flask, render_template, send_file

import requests

class rBytesIO(BytesIO):
    def close(self, really=False):
        if really:
            super.close()

app = Flask("Weather Info")

tstamp_fmt = '%a, %d %b %Y %X %Z'

de_ru = {"data":None,
         "url":"http://www.yr.no/sted/Tyskland/Th%C3%BCringen/Rudolstadt/meteogram.png",
         "tstamp":datetime.strptime("Thu, 01 Jan 1970 00:00:00 GMT", tstamp_fmt)}

import logging
from logging.handlers import SysLogHandler
from logging import Formatter

handler = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_LOCAL0)
handler.setLevel(logging.INFO)
handler.setFormatter(Formatter('weather_info - %(levelname)s: %(message)s'))
app.logger.addHandler(handler)
         
def update_image(url):
    global tstamp_fmt
    app.logger.info("Fetching new image.")
    res = requests.get(url)
    img = Image.open(BytesIO(res.content)).crop((10,45,453,267))
    ret = rBytesIO()
    img.save(ret, 'PNG')
    ret.seek(0)
    return (ret, datetime.strptime(res.headers['Date'], tstamp_fmt))

def fetch_image(img):
    
    if img['data'] is None:
        app.logger.info("No image cached.")
        img['data'], img['tstamp'] = update_image(img['url'])

    else:
        app.logger.debug("Time stamp: " + str(img['tstamp']))
        app.logger.info("Image cached. Checking validity")
        res = requests.head(img['url'])

        if datetime.strptime(res.headers['Last-Modified'], tstamp_fmt) > img['tstamp']:
            app.logger.info("Cache invalid.")
            img['data'], img['tstamp'] = update_image(img['url'])
        else:
            app.logger.info("Using cached version.")
            app.logger.debug("Image file object: " + str(img['data']))
            img['data'].seek(0)

    return img['data']
        

@app.route('/weather_info/', methods=['GET'])
def index():
    return render_template("index.html");


@app.route('/weather_info/de_ru.png', methods=['GET'])
def de_ru_png():
    return send_file(fetch_image(de_ru),
                     attachment_filename='de_ru.png',
                     mimetype='image/png')
    
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
