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


class Moderator:
    def __init__(self, connect_panel=False, app_id="", app_key="", app_secret="", app_cluster=""):
        self.pusher_client = pusher.Pusher(
            app_id=app_id, key=app_key, secret=app_secret, cluster=app_cluster
        )
        self.pysher_client = pysher.Pusher(
            key=app_key, secret=app_secret, cluster=app_cluster, user_data={
                "type": "moderator"}
        )
        self.channel = None
        self.panel = None
        self.elapsed = False
        self.answers = []
        self.bots = []
        self.conversation = []
        self.current_message = None
        self.connect_panel = connect_panel
        self.init_connection()
        while True:
            time.sleep(1)

    def calculate_message_ranking(self, message: Message):
        evaluate.lemmatize_message(message)
        evaluate.check_conversation_partner(self.current_message, message)
        evaluate.check_sentence_similarity(
            self.conversation, message, self.current_message)
        evaluate.check_conversation_shares(
            self.conversation, message)
        evaluate.check_topic_similarity(
            self.conversation, message)
        evaluate.check_polarity_similarity(message, self.current_message)
        message.calculate_ranking_number()

    def choose_next_message(self):
        next_message = evaluate.select_highest_rated_message(self.answers)
        self.conversation.append(next_message)
        self.current_message = next_message
        return next_message

    def make_elapsed(self, message_id=None):
        if message_id == self.current_message.id:
            self.elapsed = True
            time.sleep(0.5)
            if len(self.answers) > 0:
                self.emit_message(self.choose_next_message())

    def wait_for_responses(self, message):
        if self.connect_panel:
            self.panel.bind(
                f"client-message-done-{message.id}", self.make_elapsed)
        else:
            timeout = (len(message.message) * 0.1)
            Timer(timeout, self.make_elapsed).start()

    def emit_message(self, message: Message):
        self.pusher_client.trigger(
            channels="chatting-chatbots",
            event_name=f"moderator_message",
            data=message.to_json_event_string(),
        )
        if self.connect_panel:
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
        if data["responding_to"] == self.current_message.id:
            response = json.loads(data["response"])
            message = Message(
                id=response["id"],
                bot_id=response["bot_id"],
                bot_name=response["bot_name"],
                message=response["message"],
            )
            if self.elapsed is False:
                self.calculate_message_ranking(message)
                if self.connect_panel:
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
        if self.connect_panel:
            self.panel.bind("client-provoke-message", self.provoke_message)
        else:
            first_message = input("Message: ")
            self.provoke_message(first_message)

    def register_chatbot(self, data):
        data = json.loads(data)
        bot = Bot(id=data["id"], name=data["name"], method=data["method"])
        self.bots.append(bot)
        if self.connect_panel:
            self.pusher_client.trigger(
                channels="private-panel",
                event_name="bot-registered",
                data=bot.to_json(),
            )

    def connect_handler(self, _):
        self.channel = self.pysher_client.subscribe("chatting-chatbots")
        if self.connect_panel:
            self.panel = self.pysher_client.subscribe("private-panel")
        self.channel.bind("chatbot_connection", self.register_chatbot)
        self.init_chat()

    def init_connection(self):
        self.pysher_client.connection.bind(
            "pusher:connection_established", self.connect_handler
        )
        self.pysher_client.connect()

        # start a local server to authenticate client messages of panel
        if self.connect_panel:
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
