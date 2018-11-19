#!/usr/bin/python

from lxml import html
from slackclient import SlackClient
import datetime
import json
import os
import re
import requests
import time
import yaml

config = None
for loc in os.curdir, os.path.expanduser('~'), '/etc/lunchbot':
    try:
        with open(os.path.join(loc,'config.yaml'), 'r') as stream:
            try:
                config = yaml.load(stream)
                break
            except yaml.YAMLError as exc:
                print(exc)
                quit()
    except IOError as exc:
        print(exc)

if config == None:
    print('No valid configuration found.')
    quit()

# instantiate Slack client
slack_client = SlackClient(config['SLACK_BOT_TOKEN'])
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 3 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
KEYWORD_REGEX = "(mittag|essen|hunger|hungrig|hungry)"
THANKS_REGEX = "(dank|thanks|thx)"
MENTION_REGEX = ".*{}|{}.*"

def parse_teigwareat():
    page = requests.get('http://teigware.at/')
    tree = html.fromstring(page.text)
    menu1 = tree.xpath('//tr[{}]/td[2]/text()'.format(datetime.datetime.today().weekday()+3))[0].strip().encode('utf-8')
    menu2 = tree.xpath('//tr[{}]/td[4]/text()'.format(datetime.datetime.today().weekday()+3))[0].strip().encode('utf-8')
    return '{} or {} @ http://teigware.at'.format(menu1, menu2)

def parse_mensa():
    page = requests.get('http://menu.mensen.at/index/index/locid/9')
    tree = html.fromstring(page.text)
    menu1 = tree.xpath('//div[{}]/div[2]/div[1]/div[6]/p/strong/text()'.format(datetime.datetime.today().weekday()+1))[0].strip().encode('utf-8')
    menu2 = tree.xpath('//div[{}]/div[2]/div[2]/div[6]/p/strong/text()'.format(datetime.datetime.today().weekday()+1))[0].strip().encode('utf-8')
    menu3 = tree.xpath('//div[{}]/div[2]/div[3]/div[6]/p/strong/text()'.format(datetime.datetime.today().weekday()+1))[0].strip().encode('utf-8')
    return '{}, {} or {} @ Mensa'.format(menu1, menu2, menu3)

def parse_schroedinger():
    page = requests.get('http://menu.mensen.at/index/index/locid/52')
    tree = html.fromstring(page.text)
    menu1 = tree.xpath('//div[{}]/div[2]/div[1]/div[6]/p/strong/text()'.format(datetime.datetime.today().weekday()+1))[0].strip().encode('utf-8')
    menu2 = tree.xpath('//div[{}]/div[2]/div[2]/div[6]/p/strong/text()'.format(datetime.datetime.today().weekday()+1))[0].strip().encode('utf-8')
    return '{} or {} @ Cafe Schroedinger'.format(menu1, menu2)

def parse_dabba():
    return 'http://nam-nam.at/wp-content/uploads/Wochenkarten/Nam-Nam-Wochenkarte-Dabba.pdf'

def parse_swingkitchen():
    page = requests.get('https://www.swingkitchen.com/')
    tree = html.fromstring(page.text)
    menu = tree.xpath('//div[42]/div/div[2]/h5/a/span/text()')[0].strip().encode('utf-8')
    return '{} @ Swing Kitchen'.format(menu)

def parse_tewa():
    page = requests.get('http://tewa-naschmarkt.at/tagesteller/')
    tree = html.fromstring(page.text)
    menu1 = tree.xpath('//tr[{}]/td[1]/strong/text()'.format(datetime.datetime.today().weekday()*2+4))[0].strip().encode('utf-8')
    menu2 = tree.xpath('//tr[{}]/td[1]/strong/text()'.format(datetime.datetime.today().weekday()*2+5))
    menu2 = " or {}".format(menu2[0].strip().encode('utf-8')) if len(menu2) > 0 else ""
    return '{}{} @ http://tewa-naschmarkt.at/'.format(menu1, menu2)

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            matches = re.search(MENTION_REGEX.format(starterbot_id, starterbot_user), event["text"])
            if matches and re.search(THANKS_REGEX, event["text"], re.IGNORECASE):
                slack_client.api_call(
                    "chat.postMessage",
                    channel=event["channel"],
                    text="You're welcome!"
                )
            if re.search(KEYWORD_REGEX, event["text"], re.IGNORECASE):
                slack_client.api_call(
                    "chat.postMessage",
                    channel=event["channel"],
                    text="I'm hungry too..\nlet's get some lunch!"
                )
                slack_client.api_call(
                    "chat.postMessage",
                    channel=event["channel"],
                    text="What about {}?".format(parse_teigwareat())
                )
                slack_client.api_call(
                    "chat.postMessage",
                    channel=event["channel"],
                    text="Or do you like {} better?".format(parse_mensa())
                )
                slack_client.api_call(
                    "chat.postMessage",
                    channel=event["channel"],
                    text="This one sounds good as well: {}".format(parse_schroedinger())
                )
                slack_client.api_call(
                    "chat.postMessage",
                    channel=event["channel"],
                    text="U know what? There's a special: {}".format(parse_swingkitchen())
                )
                slack_client.api_call(
                    "chat.postMessage",
                    channel=event["channel"],
                    text="Did you already check out {}?".format(parse_dabba())
                )
                slack_client.api_call(
                    "chat.postMessage",
                    channel=event["channel"],
                    text="Another suggestion: {}?".format(parse_tewa())
                )
#            user_id, message = parse_direct_mention(event["text"])
#            if user_id == starterbot_id:
#                return message, event["channel"]
    return None, None

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Lunch Bot connected and hungry!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        starterbot_user = slack_client.api_call("auth.test")["user"]

        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
