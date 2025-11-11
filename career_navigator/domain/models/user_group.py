from enum import Enum


class UserGroup(str, Enum):
    EXPERIENCED_CONTINUING = "experienced_continuing"
    EXPERIENCED_CHANGING = "experienced_changing"
    INEXPERIENCED_WITH_GOAL = "inexperienced_with_goal"
    INEXPERIENCED_NO_GOAL = "inexperienced_no_goal"

