from typing import List
import spacy
import re
from .message import Message
from pke.unsupervised import TopicRank
from porter2stemmer import Porter2Stemmer   # pip install porter2stemmer
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')
nltk.download('vader_lexicon')

nlp = spacy.load("en_core_web_lg")


def handle_following_appostrophs(sentence):
    sentence = re.sub(r" s ", "'s ", sentence)
    sentence = re.sub(r" m ", "'m ", sentence)
    sentence = re.sub(r" re ", "'re ", sentence)
    sentence = re.sub(r" t ", "'t ", sentence)
    return sentence


def replace_after_sentence_sign(sentence):
    for index, char in enumerate(sentence):
        if char == "." or char == "?" or char == "!":
            # space counts as char
            if index + 2 < len(sentence):
                sentence = (
                    sentence[: index + 2]
                    + sentence[index + 2].upper()
                    + sentence[index + 3:]
                )
    return sentence


def check_conversation_partner(current_message: Message, message: Message) -> None:
    if message.bot_name in current_message.message:
        message.conversation_partner_score = 1.0


def check_sentence_similarity(conversation: List[Message], message: Message, current_message: Message) -> None:
    """Check Conversation Shares"""

    prev_message = current_message.message_lemma
    prev_message_doc = nlp(prev_message)

    message_doc = nlp(message.message_lemma)
    similarity = prev_message_doc.similarity(message_doc)
    message.similarity_score = similarity
    # treshhold if sentences are to similar or loop happend
    if similarity > 0.95 or loop_checker(conversation, message.message):
        message.similarity_score = -5.0 + similarity


def check_polarity_similarity(response: Message, current_message: Message) -> None:
    """Check Sentinemt"""
    analyzer = SentimentIntensityAnalyzer()
    response_polarity = analyzer.polarity_scores(response.message)["compound"]
    current_message_polarity = analyzer.polarity_scores(current_message.message)[
        "compound"]
    diff = response_polarity - current_message_polarity
    positive_diff = -diff if diff < 0 else diff
    inverse_diff = 1 - positive_diff
    response.polarity_score = inverse_diff


def loop_checker(
    full_conversation: List[Message],
    possible_next_message: Message,
    window_size: int = 20,
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
    corrected_message = handle_following_appostrophs(message.message)
    corrected_message = replace_after_sentence_sign(corrected_message)
    message_doc = nlp(corrected_message)
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
def check_object_subject_similarity(
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


# based on https://boudinfl.github.io/pke/build/html/unsupervised.html?highlight=rank#pke.unsupervised.TopicRank
def check_topic_similarity(
    full_conversation: List[Message],
    possible_next_message: Message,
    window_size: int = 0,
):
    # create 1 continuous string from the conversation
    conv = ''
    for message in full_conversation[-window_size:]:
        conv += message.message + ' '

    # create a TopicRank extractor
    conv_extractor = TopicRank()

    conv_extractor.load_document(
        conv,
        language='en',
        normalization='stemming')

    # select the keyphrase candidates, for TopicRank the longest sequences of
    # nouns and adjectives
    conv_extractor.candidate_selection(pos={'NOUN', 'PROPN', 'ADJ'})

    # weight the candidates using a random walk. The threshold parameter sets the
    # minimum similarity for clustering, and the method parameter defines the
    # linkage method
    conv_extractor.candidate_weighting(threshold=0.74,
                                       method='average')

    # stem the message candidate (same stem-algorithm (Porter) as the one used in pke package)
    stemmer = Porter2Stemmer()
    msg_doc = nlp(possible_next_message.message)
    msg_stems = []
    for token in msg_doc:
        stem = stemmer.stem(token.text.lower())
        msg_stems.append(stem)

    topic_score = 0
    # check if any of the message stems are part of the top 10 conversation topics
    for (keyphrase, score) in conv_extractor.get_n_best(n=10, stemming=True):
        if keyphrase in msg_stems:
            # the more stems match the higher the score
            topic_score += score

    possible_next_message.topic_score = topic_score
    return topic_score
