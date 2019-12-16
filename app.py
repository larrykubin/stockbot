import slack, boto3, json, requests
from chalice import Chalice, Rate, Cron
from chalicelib import config, utils

app = Chalice(app_name='stockbot')

# dynamodb
db = boto3.resource('dynamodb')
watchlist_table = db.Table('watchlist')


@app.route('/', methods=['POST'], content_types=['application/x-www-form-urlencoded'])
def index():
    r = utils.parse_request(app.current_request)

    response = COMMANDS[r['command']](r)

    return response


def chart(request):
    symbol = request['text']

    attachments = []

    image_url = config.CHART_URL.format(symbol)
    attachments.append({"title": symbol, "image_url": image_url})

    return {
        "response_type": "in_channel",
        "text": "You requested a stock chart for {}".format(symbol),
        "attachments": attachments
    }


def quote(request):
    symbol = request['text']

    quote = utils.get_quote(symbol)    
    text = utils.format_quote(quote)

    return {
        "response_type": "in_channel",
        "text": text
    }


def watch(request):
    symbol = request['text']
    quote = utils.get_quote(symbol)

    watchlist_table.put_item(Item={
        'symbol': symbol,
        'start_quote': json.dumps(quote)
    })

    text = "Added {} to watchlist".format(request['text'])

    return {
        "response_type": "in_channel",
        "text": text
    }


def unwatch(request):
    watchlist_table.delete_item(Key={
        'symbol': request['text']
    })

    text = "Removed {} from watchlist".format(request['text'])

    return {
        "response_type": "in_channel",
        "text": text
    }


@app.schedule(Cron(30, 13, '?', '*', 'MON-FRI', '*'))
def market_open(event):
    client = slack.WebClient(token=config.SLACK_TOKEN)

    for symbol in config.SCHEDULED_SYMBOLS:
        quote = utils.get_quote(symbol)   
        text = utils.format_quote(quote)

        client.chat_postMessage(channel='#random', text=text, as_user=True)


@app.schedule(Rate(30, unit=Rate.MINUTES))
def watchlist(request):
    client = slack.WebClient(token=config.SLACK_TOKEN)

    watchlist = watchlist_table.scan()

    client.chat_postMessage(channel='#general', text="Here is your watchlist", as_user=True)

    for item in watchlist['Items']:
        quote = utils.get_quote(item['symbol'])
        text = utils.format_quote(quote)

        client.chat_postMessage(channel='#general', text=text, as_user=True)

    return {
        'success': True
    }





COMMANDS = {
    "/chart": chart,
    "/quote": quote,
    "/watchlist": watchlist,
    "/watch": watch,
    "/unwatch": unwatch
}
