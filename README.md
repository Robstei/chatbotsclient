## Installation
```
pip install https://github.com/Robstei/chatbotsclient/releases/download/0.0.5/chatbotsclient-0.0.5.tar.gz
```
## Usage
### Basic Setup
Simply instantiate a Chatbot object and pass your custom respond function. When ever a message is received from the moderator the provided respond method will be executed.
```
from chatbotsclient.chatbot import Chatbot
from chatbotsclient.message import Message

def respond(message: Message):
    # custom answer computation of your chatbot
    answer = compute(message.message)
    return answer

chatbot = Chatbot(respond, "<chatbot_name>")
```
### With full conversation
It is also possible to take the full conversation feed into account.
```
from chatbotsclient.chatbot import Chatbot
from chatbotsclient.message import Message

def respond(message: Message, conversation: List[Message]):
    # custom answer computation of your chatbot
    answer = compute(message.message, conversation)
    return answer

chatbot = Chatbot(respond, "<chatbot_name>")
```