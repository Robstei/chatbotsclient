from typing import List

import spacy
from message import Message

nlp = spacy.load("en_core_web_lg")


def check_sentence_similarity(
    full_conversation: List[Message], possible_next_messages: List[Message]
) -> List[Message]:
    """Check Conversation Shares"""
    if len(full_conversation) == 0:
        return possible_next_messages

    possible_next_messages_ranked: List[Message] = []
    prev_message = full_conversation[-1].message_lemma
    prev_message_doc = nlp(prev_message)  # spacy nlp

    for message in possible_next_messages:
        message_doc = nlp(message.message_lemma)
        similarity = prev_message_doc.similarity(message_doc)
        message.ranking_number += similarity
        # treshhold if sentences are to similar or loop happend
        if similarity > 0.95 or loop_checker(full_conversation, message.message):
            message.ranking_number = -5.0 + similarity
        possible_next_messages_ranked.append(message)

    return possible_next_messages_ranked


def loop_checker(
    full_conversation: List[Message],
    possible_next_message: Message,
    window_size: int = 3,
):
    """Checks if message was already found in conversation (depends on window_size)"""
    for message in full_conversation[-window_size:]:
        if message.message == possible_next_message:
            return True

    return False


def check_conversation_shares(
    full_conversation: List[Message], possible_message: List[Message]
):
    """Check Conversation Shares"""
    ranked_messages: List[Message] = []

    conversation_message_count = len(full_conversation)
    bot_message_count = {}

    for message in full_conversation:
        if message.bot_id in bot_message_count:
            bot_message_count[message.bot_id] += 1
        else:
            bot_message_count[message.bot_id] = 1

    # final message ranking will be factored based on frequency of messages sent by bot_id
    for message in possible_message:
        if message.bot_id in bot_message_count:
            share = (
                bot_message_count[message.bot_id] / conversation_message_count
            ) * 100
            normalized = 1 - (share / 100)
            message.ranking_number = message.ranking_number * normalized
        else:
            message.ranking_number = message.ranking_number * 1
        ranked_messages.append(message)

    return ranked_messages


def select_highest_rated_message(ranked_messages: List[Message]):
    highest_rated_message = ranked_messages[0]
    for message in ranked_messages[1:]:
        if message.ranking_number > highest_rated_message.ranking_number:
            highest_rated_message = message

    print(type(highest_rated_message))
    return highest_rated_message


def lemmatize_messages(possible_messages: List[Message]) -> None:
    """Lemmatize Messages"""
    for message in possible_messages:
        lemmatized_message = ""
        message_doc = nlp(message.message)
        for token in message_doc:
            lemmatized_message = lemmatized_message + token.lemma_ + " "
        message.message_lemma = lemmatized_message.strip().lower()


irrelevant_phrases = [
    "i",
    "you",
    "they",
    "it",
    "he",
    "she",
    "we",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "their",
    "its",
    "his",
    "her",
    "our",
    "mine",
    "yours",
    "theirs",
    "ours",
    "myself",
    "yourself",
    "himself",
    "herself",
    "itself",
    "ourselves",
    "yourselves",
    "themselves",
]

# based on: https://stackoverflow.com/questions/28618400/how-to-identify-the-subject-of-a-sentence
def get_subjects_and_objects(sentence):
    """Get Subject and Objects"""
    sent = nlp(sentence)
    ret = []
    for token in sent:
        if "nsubj" in token.dep_:
            subtree = list(token.subtree)
            start = subtree[0].i
            end = subtree[-1].i + 1
            ret.append(str(sent[start:end]).lower())

        if "dobj" in token.dep_:
            subtree = list(token.subtree)
            start = subtree[0].i
            end = subtree[-1].i + 1
            ret.append(str(sent[start:end]).lower())

    # remove irrelevant subjects and objects like i or they
    for phrase in irrelevant_phrases:
        while phrase in ret:
            ret.remove(phrase)

    return ret


# this does not really check for topics in the classic nlp way, but if sentence subjects or objects of a message fit the ones in the past conversation
def check_topic_similarity(
    full_conversation: List[Message],
    possible_next_message: Message,
    window_size: int = 5,
):
    # get subjects and objects of message and conversation
    msg_phrases = get_subjects_and_objects(possible_next_message.message)
    conv_phrases = []
    for message in full_conversation[-window_size:]:
        conv_phrases.extend(get_subjects_and_objects(message.message))

    relevance = 1
    for conv_phrase in conv_phrases:
        for msg_phrase in msg_phrases:
            # calculate 'topic' similarity between a possible messsage and a conversation message
            sim = nlp(msg_phrase).similarity(nlp(conv_phrase))
            # print("Similarity is ",sim, " for '", msg_phrase, "' and '", conv_phrase, "'")
            if sim >= 0.8:
                possible_next_message.topic_score = sim * relevance
                # no need to check further, because relevance will shrink the outcome anyway
                return

        # relevance shrinks further down the conversation
        relevance = relevance * 0.9

    # no match. Score is zero.
    possible_next_message.topic_score = 0
