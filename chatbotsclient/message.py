import json


class Message:
    def __init__(self, id, message, bot_id, bot_name):
        self.__id = id
        self.__message = message
        self.__message_lemma = message
        self.__bot_id = bot_id
        self.__bot_name = bot_name
        self.__ranking_number = 0.0
        self.__similarity_score = 0.0
        self.__share_score = 0.0
        self.__topic_score = 0.0
        self.__polarity_score = 0.0
        self.__conversation_partner_score = 0.0

    # region getters

    @property
    def id(self):
        return self.__id

    @property
    def message(self):
        return self.__message

    @property
    def bot_id(self):
        return self.__bot_id

    @property
    def bot_name(self):
        return self.__bot_name

    @property
    def ranking_number(self):
        return self.__ranking_number

    @property
    def similarity_score(self):
        return self.__similarity_score

    @property
    def share_score(self):
        return self.__share_score

    @property
    def topic_score(self):
        return self.__topic_score

    @property
    def polarity_score(self):
        return self.__polarity_score
    
    @property
    def conversation_partner_score(self):
        return self.__conversation_partner_score

    @property
    def message_lemma(self):
        return self.__message_lemma

    # endregion

    # region setters
    # maybe ranking number should be read-only and only set by calculate_ranking_number
    @ranking_number.setter
    def ranking_number(self, value):
        self.__ranking_number = value

    @similarity_score.setter
    def similarity_score(self, value):
        self.__similarity_score = value

    @share_score.setter
    def share_score(self, value):
        self.__share_score = value

    @topic_score.setter
    def topic_score(self, value):
        self.__topic_score = value

    @polarity_score.setter
    def polarity_score(self, value):
        self.__polarity_score = value

    @conversation_partner_score.setter
    def conversation_partner_score(self, value):
        self.__conversation_partner_score = value

    @message_lemma.setter
    def message_lemma(self, value):
        self.__message_lemma = value

    # endregion

    # correct weight values need to be tested
    def calculate_ranking_number(
        self,
        similarity_weight: float = 1,
        share_weight: float = 1,
        topic_weight: float = 1,
        polarity_weight: float = 1,
        conversation_partner_weight: float = 1,
    ):
        self.__ranking_number = (
            similarity_weight * self.__similarity_score
            + share_weight * self.__share_score
            + topic_weight * self.__topic_score
            + polarity_weight * self.__polarity_score
            + conversation_partner_weight * self.__conversation_partner_score
        )

    def to_json_event_string(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "type": "message",
                "message": self.message,
                "bot_id": self.bot_id,
                "bot_name": self.bot_name,
                "topic_score": self.topic_score,
                "similarity_score": self.similarity_score,
                "share_score": self.share_score,
                "polarity_score": self.polarity_score,
                "conversation_partner_score": self.conversation_partner_score,
                "ranking_number": self.ranking_number,
                "message_lemma": self.message_lemma,
            }
        )
