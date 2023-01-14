from message import Message
import evaluate

full_conversation = [
    Message(0,"Are you a fan of Google or Microsoft?", "1", "Freddy"),
    Message(1,"Both are excellent technology they are helpful in many ways. For the security purpose both are super.", "2", "Ben"),
    Message(2,"I'm not  a huge fan of Google, but I use it a lot because I have to. I think they are a monopoly in some sense.", "3", "Jefrey"),
    Message(3,"Google provides online related services and products, which includes online ads, search engine and cloud computing.", "4", "Tom"),
    Message(4,"Yeah, their services are good. I'm just not a fan of intrusive they can be on our personal lives.", "5", "Lisa"),
]

all_possible_messages = [
    Message(5,"Google is leading the alphabet subsidiary and will continue to be the Umbrella company for Alphabet internet interest.", "1", "Freddy"),
    Message(5,"Sorry i don't get it.", "2", "Ben"),
    Message(5,"I like to dance every night.", "3", "Jefrey"),
    Message(5,"Some companies are good, some are bad.", "4", "Tom"),
    Message(5,"Ok, bye", "5", "Lisa")
]


for message in all_possible_messages:
    print(evaluate.check_topic_similarity(full_conversation, message))