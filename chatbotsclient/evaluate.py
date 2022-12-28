from typing import List
import spacy
from .message import Message

nlp = spacy.load("en_core_web_lg")


def check_sentence_similarity(conversation: List[Message], message: Message) -> None:
    """Check Conversation Shares"""
    if len(conversation) == 0:
        return

    prev_message = conversation[-1].message_lemma
    prev_message_doc = nlp(prev_message)

    message_doc = nlp(message.message_lemma)
    similarity = prev_message_doc.similarity(message_doc)
    message.similarity_score = similarity
    # treshhold if sentences are to similar or loop happend
    if similarity > 0.95 or loop_checker(conversation, message.message):
        message.similarity_score = -5.0 + similarity


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


def check_conversation_shares(conversation: List[Message], message: Message):
    """Check Conversation Shares"""
    conversation_message_count = len(conversation)
    bot_message_count_dict = {}

    for entry in conversation:
        if entry.bot_id in bot_message_count_dict.keys():
            bot_message_count_dict[entry.bot_id] += 1
        else:
            bot_message_count_dict[entry.bot_id] = 1

    if message.bot_id in bot_message_count_dict.keys():
        share = (
            bot_message_count_dict[message.bot_id] / conversation_message_count
        ) * 100
        normalized_share_score = share / 100
        message.share_score = 1 - normalized_share_score
    else:
        message.share_score = 1


def select_highest_rated_message(ranked_messages: List[Message]):
    highest_rated_message = ranked_messages[0]
    for message in ranked_messages[1:]:
        if message.ranking_number > highest_rated_message.ranking_number:
            highest_rated_message = message
    return highest_rated_message


def lemmatize_message(message: Message) -> None:
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
    # clone and reverse conversation array, so that it starts with the last message
    conv = full_conversation[:]
    conv.reverse()

    # get subjects and objects of message and conversation
    msg_phrases = get_subjects_and_objects(possible_next_message.message)
    conv_entries = [""] * window_size
    i = 0
    for message in conv[-window_size:]:
        conv_entries[i] = get_subjects_and_objects(message.message)
        i += 1

    relevance = 1
    sim = 0
    for entry_phrases in conv_entries:
        for entry_phrase in entry_phrases:
            entry_doc = nlp(entry_phrase)
            # check if conversation phrase and its word vector are valid
            if entry_doc and entry_doc.vector_norm:
                for msg_phrase in msg_phrases:
                    # calculate 'topic' similarity between a possible messsage and a conversation message
                    sim = entry_doc.similarity(nlp(msg_phrase))
                    # print("similarity is ",sim, " for '", msg_phrase, "' and '", entry_phrase, "'")
                    if sim >= 0.8:
                        possible_next_message.topic_score = sim * relevance
                        # no need to check further, because relevance will shrink the outcome anyway
                        return

        # relevance shrinks further down the conversation
        relevance = relevance * 0.9

    # no match. Score is zero.
    possible_next_message.topic_score = 0
