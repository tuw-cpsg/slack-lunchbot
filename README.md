# slack-lunchbot

This hungry bot searches websites of restaurants around TU Wien and tells you all possible lunch menus.

# Config

First, you need to create a slack app (follow this [instruction](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html)).
Then, create a config file that contains the Bot User OAuth Access Token.
The config file can also contain an array of restaurants with URL and a `xpath` and a day offset to each menu they provide.
An example config file can be generated like this:
```
cat > config.yaml << EOF
SLACK_BOT_TOKEN: xoxb-0123456789ab-0123456789ab-0123456789abcdefghijklmn

restaurants:
    - name: Mensa
      url: 'http://menu.mensen.at/index/index/locid/9'
      menus:
          - xpath: '//div[{}]/div[2]/div[1]/div[6]/p/strong/text()'
            day_offset: 1
          - xpath: '//div[{}]/div[2]/div[2]/div[6]/p/strong/text()'
            day_offset: 1
          - xpath: '//div[{}]/div[2]/div[3]/div[6]/p/strong/text()'
            day_offset: 1
EOF
```
It parses the TU Wien Freihaus Mensa and posts the three daily menus in the chat.
