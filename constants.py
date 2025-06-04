import random

random_words = [
    "scuba",
    "cactus",
    "banana",
    "penguin",
    "giraffe",
    "octopus",
    "jelly",
    "fish",
    "turtle",
    "dolphin",
    "whale",
    "seahorse",
    "star",
    "coral",
    "anemone",
    "urchin",
    "clam",
    "lobster",
    "crab",
    "squid",
    "octagon",
    "hexagon",
    "circle",
    "square",
    "rhombus",
    "trapezoid",
    "kite",
    "ellipse",
]


def get_random_word():
    return random.choice(random_words)


def get_room_name():
    return f"{get_random_word()} {get_random_word()}"


brief_funny_waiting_messages = [
    "waiting…",
    "still waiting…",
    "hmmmm…",
    "anyone?",
    "anyone there?",
    "still waiting.",
    "hurry up!!",
    "are you there?",
    "waiting for you…",
    "patience now…",
    "r u still there?",
    "come on…",
    "giving up…",
    "bored now",
    "waiting…",
]


def get_random_waiting_message():
    return random.choice(brief_funny_waiting_messages)
