import os
import slack
import slack.chat


slack.api_token = os.environ['STUPID_TOKEN']
slack.chat.post_message('#loud-launches', 'Eat some!', username='Stupid')
