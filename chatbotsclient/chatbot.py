import json
import time
import uuid
from typing import Callable, List, Union
import pusher
import pysher
from .bot import Bot
from .message import Message


class Chatbot:
    """Chatbot"""

    def __init__(
        self,
        respond_method: Callable[[Message, List[Message]], str],
        name: str,
        method: Union[str, None] = None,
        app_id="", app_key="", app_secret="", app_cluster=""
    ):
        self.pusher_client = pusher.Pusher(
            app_id=app_id, key=app_key, secret=app_secret, cluster=app_cluster
        )
        self.bot_id = None
        self.bot_name = name
        self.method = method
        self.channel = None
        self.pysher_client = pysher.Pusher(
            key=app_key,
            secret=app_secret,
            cluster=app_cluster,
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
            id=data["id"], bot_id=data["bot_id"], bot_name=data["bot_name"], message=data["message"]
        )
        self.conversation.append(message)
        print(f"{message.bot_name}", end=": ")
        print(message.message)
        if message.bot_id != self.bot_id:
            response = self.respond_method(message, self.conversation)
            self.pusher_client.trigger(
                channels="chatting-chatbots",
                event_name=f"chatbot_response_{message.id}",
                data={
                    "responding_to": message.id,
                    "response": Message(
                        id=str(uuid.uuid4()),
                        bot_id=self.bot_id,
                        bot_name=self.bot_name,
                        message=response,
                    ).to_json_event_string()
                },
            )

    def connect_handler(self, _):
        self.bot_id = str(uuid.uuid4())
        self.channel = self.pysher_client.subscribe("chatting-chatbots")
        self.pusher_client.trigger(
            channels="chatting-chatbots",
            event_name="chatbot_connection",
            data=Bot(id=self.bot_id, name=self.bot_name,
                     method=self.method).to_json(),
        )
        # self.channel.bind(f"moderator_connection_{self.bot_id}", self.connection_established)
        self.channel.bind("moderator_message", self.message_received)

    def init_connection(self):
        self.pysher_client.connection.bind(
            "pusher:connection_established", self.connect_handler
        )

        self.pysher_client.connect()
