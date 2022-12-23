## Installation
```
pip install https://github.com/Robstei/chatbotsclient/releases/download/0.0.6/chatbotsclient-0.0.6.tar.gz
```
## Usage
### Moderator
#### Setup
Simply instantiate a Moderator object. The moderator will wait for chatbots to connect and provides the possiblity to start the conversation by input.
```python
from chatbotsclient.moderator import Moderator

moderator = Moderator()
```
### Chatbot
#### Basic Setup
Instantiate a Chatbot object and pass your custom respond function. When ever a message is received from the moderator the provided respond method will be executed. The moderator script has to be running for the chatbots to connect to the websocket.
```python
from chatbotsclient.chatbot import Chatbot
from chatbotsclient.message import Message

def respond(message: Message):
    # custom answer computation of your chatbot
    answer = compute(message.message)
    return answer

chatbot = Chatbot(respond, "<chatbot_name>")
```
#### Full Conversation Setup
It is also possible to take the full conversation feed into account.
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

### Message Object
The message object is passed to the custom respond function of your bot. It contains the plain text message as well as information about the sending bot.
|Field|Description|
|---|---|
|message|Plain text message. Used to compute your chatbots answer.|
|bot_id|Id of the sending bot.|
|bot_name|Name of the sending bot. Could be used for entity replacement.|
