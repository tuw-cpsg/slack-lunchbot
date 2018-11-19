# slack-lunchbot

This hungry bot searches websites of restaurants arount TU Wien and tells you all possible lunch menus.

# Config

You need to create an slack app (follow this [instruction](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html)) and create a config file that contains the Bot User OAuth Access Token:
```
cat > config.yaml << EOF
SLACK_BOT_TOKEN: xoxb-0123456789ab-0123456789ab-0123456789abcdefghijklmn
EOF
```
