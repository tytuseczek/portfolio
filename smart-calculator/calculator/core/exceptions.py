class CalculatorError(Exception):
    pass


class UnexpectedCalculatorError(CalculatorError):
    pass


class IncorrectValueCalculatorError(CalculatorError):
    pass


class NotSupportedCalculatorError(CalculatorError):
    pass


class UnableToFindSolutionCalculatorError(CalculatorError):
    pass


class InternalLatexParsingCalculatorError(Exception):
    pass


class LatexParsingCalculatorError(CalculatorError):
    pass
