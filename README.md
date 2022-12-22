## Installation
```
pip install https://github.com/Robstei/chatbotsclient/releases/download/0.0.5/chatbotsclient-0.0.5.tar.gz
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
Simply instantiate a Chatbot object and pass your custom respond function. When ever a message is received from the moderator the provided respond method will be executed. The moderator script has to be running for the chatbots to connect to the websocket.
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

def respond(message: Message, conversation: List[Message]):
    # custom answer computation of your chatbot
    answer = compute(message.message, conversation)
    return answer

chatbot = Chatbot(respond, "<chatbot_name>")
```