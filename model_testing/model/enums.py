import enum


class DataFormats(enum.Enum):
    json = 'json'
    xml = 'xml'
    plain = 'plain'
    binary = 'binary'
    database = 'database'


class Language(enum.Enum):
    python = 'python'
    exe = 'exe'


class ExecutionStatus(enum.Enum):
    started = 'started'
    finished = 'finished'
    canceled = 'canceled'
    failure = 'failure'


class ProgramStatus(enum.Enum):
    outdated = 'outdated'
    invalid = 'invalid'
    valid = 'valid'
    new_available = 'new_available'

