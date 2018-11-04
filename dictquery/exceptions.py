class DQException(Exception):
    pass


class DQSyntaxError(DQException, SyntaxError):
    pass


class DQEvaluationError(DQException):
    pass


class DQKeyError(DQException, KeyError):
    pass

class DQValidationError(DQException):
    pass
