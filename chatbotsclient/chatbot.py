import json
import time
import uuid
from typing import Callable, List, Union

import pusher
import pysher
from .bot import Bot
from .message import Message

APP_ID = "1527636"
KEY = "66736225056eacd969c1"
SECRET = "dbf65e68e6a3742dde34"
CLUSTER = "eu"


class Chatbot:
    """Chatbot"""

    def __init__(
        self,
        respond_method: Union[
            Callable[[Message, List[Message]], str], Callable[[Message], str]
        ],
        name: str,
        method: Union[str, None] = None,
    ):
        self.pusher_client = pusher.Pusher(
            app_id=APP_ID, key=KEY, secret=SECRET, cluster=CLUSTER
        )
        self.bot_id = None
        self.bot_name = name
        self.method = method
        self.channel = None
        self.pysher_client = pysher.Pusher(
            key=KEY,
            secret=SECRET,
            cluster=CLUSTER,
            user_data={"type": "chatbot", "name": self.bot_name},
        )
        self.elapsed = False
        self.answers = []
        self.conversation = []
        self.init_connection()
        self.respond_method = respond_method

        while True:
            time.sleep(1)

    def message_received(self, data):
        data = json.loads(data)
        message = Message(
            bot_id=data["bot_id"], bot_name=data["bot_name"], message=data["message"]
        )
        self.conversation.append(message)
        print(f"{message.bot_name}: {message.message}")
        response = self.respond_method(message, self.conversation)
        self.pusher_client.trigger(
            channels="chatting-chatbots",
            event_name="chatbot_response",
            data=Message(
                bot_id=self.bot_id,
                bot_name=self.bot_name,
                message=response,
            ).to_json_event_string(),
        )

    def connection_established(self, id):
        print(f"Connected with id {id}")

    def connect_handler(self, _):
        self.id = str(uuid.uuid4())
        self.channel = self.pysher_client.subscribe("chatting-chatbots")
        self.pusher_client.trigger(
            channels="chatting-chatbots",
            event_name="chatbot_connection",
            data=Bot(id=self.id, name=self.bot_name,
                     method=self.method).to_json(),
        )
        self.channel.bind(
            f"moderator_connection_{self.id}", self.connection_established
        )
        self.channel.bind("moderator_message", self.message_received)

    def init_connection(self):
        self.pysher_client.connection.bind(
            "pusher:connection_established", self.connect_handler
        )

        self.pysher_client.connect()
