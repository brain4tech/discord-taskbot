"""
Constant values across the backend.
"""

DEFAULT_TASK_EMOJIS = (
    '🔴',
    '🟠',
    '🟣',
    '〰',
    '🖐🏼',
    '📰',
    '➖',
    '✅',
)

TASK_EMOJI_IDS = [
    'pending',
    'in_progress',
    'pending_merge',
    'empty_01',
    'self_assign',
    'open_discussion',
    'empty_02',
    'done',
]

DEFAULT_TASK_EMOJI_MAPPING = dict(zip(TASK_EMOJI_IDS, DEFAULT_TASK_EMOJIS))

TASK_STATUS_IDS = [
    'pending',
    'in_progress',
    'pending_merge',
    'done',
]

TASK_STATUS_NAMES = [
    "Pending",
    "In Progress",
    "Pending Merge",
    "Done"
]

TASK_STATUS_MAPPING = dict(zip(TASK_STATUS_IDS, TASK_STATUS_NAMES))
