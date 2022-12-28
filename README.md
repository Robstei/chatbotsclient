## Installation
```
pip install https://github.com/Robstei/chatbotsclient/releases/download/1.0.0/chatbotsclient-1.0.0.tar.gz
```
## Upgrade
```
pip install -U https://github.com/Robstei/chatbotsclient/releases/download/1.0.0/chatbotsclient-1.0.0.tar.gz
```
## Usage
This package consists of a Moderator and a Chatbot class to make chatbots talk to each other. It is required to have a moderator instance up running before chatbots try connect to the conversation. Messages are sent through websocket channels using [pusher](https://pusher.com/). The moderator collects all messages from connected chatbots and selected the most suiting one. 

### Moderator
#### Setup
Simply instantiate a Moderator object. The moderator will wait for chatbots to connect and provides the possiblity to start the conversation by input.
The chatting-chatbots repository already consists of a moderator script: <code>chatting-chatbots/moderator/moderator.py</code>.
```python
# chatting-chatbots/moderator/moderator.py
from chatbotsclient.moderator import Moderator

moderator = Moderator()
```

Before connecting your chatbot to the conversation wait for the moderator to prompt "Message: ". Otherwise the connection might not be established successfully. Once chatbots are connected the conversation may be initialized by inputing a string.

![image](https://user-images.githubusercontent.com/33390325/209800753-2be32e97-40cf-4f13-a7dc-aa3a1a30a306.png)

While the conversation is ongoing the Moderator class will prompt message scores. Chatbots will only respond to messages of other chatbots.

### Chatbot
#### Basic Setup
Instantiate a Chatbot object and pass your custom respond function. When ever a message is received from the moderator the provided respond method will be executed. The moderator script has to be running in first place.
```python
from chatbotsclient.chatbot import Chatbot
from chatbotsclient.message import Message
from typing import List

def respond(message: Message, conversation: List[Message]):
    # custom answer computation of your chatbot
    answer = compute(message.message, conversation)
    return answer

chatbot = Chatbot(respond, "<chatbot_name>")
```

The compute function is meant as a placeholder for your specific method to return an answer to the provided message.

![image](https://user-images.githubusercontent.com/33390325/209801129-4f5a3dc2-44e3-46c2-a20d-84b7b5eca84c.png)

### Message Object
The message object is passed to the custom respond function of your bot. It contains the plain text message as well as information about the sending bot.
|Field|Description|
|---|---|
|message|Plain text message. Used to compute your chatbots answer.|
|bot_id|Id of the sending bot.|
|bot_name|Name of the sending bot. Could be used for entity replacement.|



### Ranking scores
The moderator ranks all incoming message by following criteria:
|Field|Description|
|---|---|
|Similarity|To fit the previous message, but also to prevent looping conversations|
|Conversation share|To ensure a varied conversation|
|Topic|Subject fitting|

