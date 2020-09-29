import enum

class DataFormats(enum.Enum):
    json = 'json'
    xml = 'xml'
    plain = 'plain text'
    binary = 'binary'
    db = 'database'

class OSs(enum.Enum):
    win = 'Win'
    linux = 'Linux'
    mac = 'MacOS'


class ImplStatus(enum.Enum):
    deprecated = 'Deprecated'
    incorrect = 'Incorrect'
    correct = 'Correct'
    has_new = 'HasNewVersion'


class Langs(enum.Enum):
    python = 'python'
    exe = 'exe'


class ExecutionStatus(enum.Enum):
    started = 'started'
    finished = 'finished'
