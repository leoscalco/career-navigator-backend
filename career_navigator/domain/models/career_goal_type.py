from enum import Enum


class CareerGoalType(str, Enum):
    """Types of career goals."""
    CONTINUE_PATH = "continue_path"  # Continue current career path
    CHANGE_CAREER = "change_career"  # Change to a different career
    CHANGE_AREA = "change_area"  # Change area/domain within same career
    EXPLORE_OPTIONS = "explore_options"  # Explore different options

