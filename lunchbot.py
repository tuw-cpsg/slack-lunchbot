#!/usr/bin/python3

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
for loc in os.getcwd(), os.path.expanduser('~'), '/etc/lunchbot', os.path.dirname(os.path.abspath(__file__)):
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
MENTION_REGEX = "^(<@{}.*>|@?{})(.*)"
KEYWORD_REGEX = "(mittag|essen|hunger|hungrig|hungry)"
THANKS_REGEX = "(dank|thanks|thx)"

def parse_restaurant(data):
    page = requests.get(data['url'])
    tree = html.fromstring(page.text)
    msg = '{}:'.format(data['name'])
    for menu in data['menus']:
        day_offset = menu['day_offset'] if 'day_offset' in menu else 0
        day_multiply = menu['day_multiply'] if 'day_multiply' in menu else 1
        xpath = menu['xpath']
        if '{}' in xpath:
            xpath = xpath.format(datetime.datetime.today().weekday()*day_multiply+day_offset)

        _menu = re.sub('\s+', ' ', ''.join(tree.xpath(xpath)))
        if len(_menu) > 0:
            #_menu = _menu[0].strip()
            msg += '\n- {}'.format(_menu)
    return msg

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            print(event["text"])
            user_id, message = parse_direct_mention(event["text"])
            if user_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX.format(starterbot_id, starterbot_user), message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def parse_bot_commandsi(slack_events):
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
                for restaurant in config['restaurants']:
                    slack_client.api_call(
                        "chat.postMessage",
                        channel=event["channel"],
                        text=parse_restaurant(restaurant)
                    )
    return None, None

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    print("handle_command({}, {})".format(command, channel))
    # Default response is help text for the user
    default_response = "Not sure what you mean.."

    # Finds and executes the given command, filling in response
    response = None

    # This is where you start to implement more commands!
    if re.search(KEYWORD_REGEX, command, re.IGNORECASE):
        response = "I'm hungry too.. \n let's get some lunch!"
        for restaurant in config['restaurants']:
            response += "\n" + parse_restaurant(restaurant)

    if re.search(THANKS_REGEX, command, re.IGNORECASE):
        response = "You're welcome!"

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    connect_counter = 0;
    while True:
        if slack_client.rtm_connect(with_team_state=False):
            print("Lunch Bot connected and hungry!")
            connect_counter = 0;
            # Read bot's user ID by calling Web API method `auth.test`
            starterbot_id = slack_client.api_call("auth.test")["user_id"]
            starterbot_user = slack_client.api_call("auth.test")["user"]
    
            try:
                while True:
                    command, channel = parse_bot_commands(slack_client.rtm_read())
                    if command:
                        handle_command(command, channel)
                    time.sleep(RTM_READ_DELAY)
            except Exception as e:
                print("Error in parse_bot_commands: {}".format(str(e)))


        else:
            print("Connection failed. Exception traceback printed above.")

        connect_counter = connect_counter + 1
        time.sleep(60)

        if(connect_counter > 3):
            quit()
