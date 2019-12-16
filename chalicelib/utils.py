import requests, json
from . import config
from urllib.parse import urlparse, parse_qsl


def parse_request(request):
    return dict(parse_qsl(request.raw_body.decode()))


def format_quote(quote):
    if quote['change'] > 0:
        updown = 'up'
        emoji = ":money_mouth_face:"
    else:
        updown = 'down'
        emoji = ":cold_sweat:"

    text = "{} latest price is {}. It is {} {} ({:0.2f}%) {}".format(quote['companyName'], quote['latestPrice'], updown, quote['change'], quote['changePercent']*100, emoji)

    return text


def get_quote(symbol):
    r = requests.get(config.QUOTE_URL.format(symbol, config.IEX_TOKEN))
    
    return json.loads(r.content.decode('utf-8'))