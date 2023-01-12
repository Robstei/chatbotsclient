import json
import time
import uuid
from threading import Timer
from typing import List
from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin

import pusher
import pysher
from .bot import Bot
from .message import Message
from . import evaluate

APP_ID = "1527636"
KEY = "66736225056eacd969c1"
SECRET = "dbf65e68e6a3742dde34"
CLUSTER = "eu"


class Moderator:
    def __init__(self):
        self.pusher_client = pusher.Pusher(
            app_id=APP_ID, key=KEY, secret=SECRET, cluster=CLUSTER
        )
        self.pysher_client = pysher.Pusher(
            key=KEY, secret=SECRET, cluster=CLUSTER, user_data={
                "type": "moderator"}
        )
        self.channel = None
        self.panel = None
        self.elapsed = False
        self.answers = []
        self.bots = []
        self.conversation = []
        self.current_message = None
        self.init_connection()

        while True:
            time.sleep(1)

    def calculate_message_ranking(self, message: Message):
        evaluate.lemmatize_message(message)
        evaluate.check_sentence_similarity(
            self.conversation, message, self.current_message)
        evaluate.check_conversation_shares(
            self.conversation, message)
        evaluate.check_topic_similarity(
            self.conversation, message)
        message.calculate_ranking_number()

        print(f"{message.ranking_number} - {message.bot_name}")
        print(
            f"Similarity: {message.similarity_score}, Share: {message.share_score}, Topic: {message.topic_score}"
        )

    def choose_next_message(self):
        next_message = evaluate.select_highest_rated_message(self.answers)
        self.conversation.append(next_message)
        self.current_message = next_message
        return next_message

    def make_elapsed(self, message_id):
        self.panel = self.pysher_client.unsubscribe("private-panel")
        time.sleep(0.5)
        self.panel = self.pysher_client.subscribe("private-panel")
        self.elapsed = True
        if len(self.answers) > 0:
            self.emit_message(self.choose_next_message())

    def wait_for_responses(self, message):
        self.panel.bind(f"client-message-done-{message.id}", self.make_elapsed)

    def emit_message(self, message: Message):
        self.pusher_client.trigger(
            channels="chatting-chatbots",
            event_name=f"moderator_message",
            data=message.to_json_event_string(),
        )
        self.pusher_client.trigger(
            channels="private-panel",
            event_name="message-sent",
            data=message.to_json_event_string(),
        )
        self.channel.bind(f"chatbot_response_{message.id}", self.add_response)
        self.answers.clear()
        self.elapsed = False
        self.wait_for_responses(message)

    def add_response(self, data):
        data = json.loads(data)
        message = Message(
            id=data["id"],
            bot_id=data["bot_id"],
            bot_name=data["bot_name"],
            message=data["message"],
        )
        if self.elapsed is False:
            self.calculate_message_ranking(message)
            self.pusher_client.trigger(
                channels="private-panel",
                event_name="message-ranked",
                data={
                    "message": self.current_message.to_json_event_string(), "response": message.to_json_event_string()},
            )
            self.answers.append(message)
        else:
            self.emit_message(message)

    def provoke_message(self, text):
        message = Message(
            id=str(uuid.uuid4()),
            bot_id=0,
            bot_name="Moderator",
            message=text
        )
        evaluate.lemmatize_message(message)
        self.current_message = message
        self.emit_message(message)

    def init_chat(self):
        self.panel.bind("client-provoke-message", self.provoke_message)

    def register_chatbot(self, data):
        data = json.loads(data)
        bot = Bot(id=data["id"], name=data["name"], method=data["method"])
        self.bots.append(bot)
        self.pusher_client.trigger(
            channels="private-panel",
            event_name="bot-registered",
            data=bot.to_json(),
        )
        # self.pusher_client.trigger(channels="chatting-chatbots", event_name=f"moderator_connection_{bot.id}",data=bot.id)

    def connect_handler(self, _):
        self.channel = self.pysher_client.subscribe("chatting-chatbots")
        self.panel = self.pysher_client.subscribe("private-panel")
        self.channel.bind("chatbot_connection", self.register_chatbot)
        self.init_chat()

    def init_connection(self):
        self.pysher_client.connection.bind(
            "pusher:connection_established", self.connect_handler
        )
        self.pysher_client.connect()

        app = Flask(__name__)
        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        @app.route('/pusher/auth', methods=['POST'])
        @cross_origin()
        def auth():
            data = request.form
            response = self.pusher_client.authenticate(
                data['channel_name'], data['socket_id'])
            return json.dumps(response)

        app.run(port=3000)
