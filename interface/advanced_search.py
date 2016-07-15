import pyparsing
from django.db.models import Q


class Node(list):
        def __eq__(self, other):
                return list.__eq__(self, other) and self.__class__ == other.__class__

        def __repr__(self):
                return '%s(%s)' % (self.__class__.__name__, list.__repr__(self))

        @classmethod
        def group(cls, expr):
                def group_action(s, l, t):
                        try:
                                lst = t[0].asList()
                        except (IndexError, AttributeError), e:
                                lst = t
                        return [cls(lst)]

                return pyparsing.Group(expr).setParseAction(group_action)

        def get_query(self):
                raise NotImplementedError()

class ComparisonNode(Node): pass
class AndNode(Node):pass
class OrNode(Node):pass
class NotNode(Node):pass


# GRAMMAR
not_operator        = pyparsing.oneOf(['not', '^'], caseless=True)
and_operator        = pyparsing.oneOf(['and', '&'], caseless=True)
or_operator         = pyparsing.oneOf(['or', '|'], caseless=True)

ident = pyparsing.Word(pyparsing.alphanums+'.')


comparison_operator = pyparsing.oneOf(['==', '=', '~', '!=', '>', '>=', '<', '<='])


pending = pyparsing.Keyword('pending', caseless=True).setParseAction(lambda t: int(1))
failed = pyparsing.Keyword('failed', caseless=True).setParseAction(lambda t: int(2))
finished = pyparsing.Keyword('finished', caseless=True).setParseAction(lambda t: int(3))
timeout = pyparsing.Keyword('timeout', caseless=True).setParseAction(lambda t: int(4))

status_keyword = finished | pending | timeout | failed

integer = pyparsing.Regex(r'[+-]?\d+').setParseAction(lambda t: int(t[0]))
float_ = pyparsing.Regex(r'[+-]?\d+\.\d*').setParseAction(lambda t: float(t[0]))

quote = pyparsing.QuotedString('"')

literal_true = pyparsing.Keyword('true', caseless=True)
literal_false = pyparsing.Keyword('false', caseless=True)
boolean_literal = literal_true | literal_false

comparison_operand = status_keyword | quote | ident | float_ | integer
comparison_expr = ComparisonNode.group(comparison_operand + comparison_operator + comparison_operand)


boolean_expr = pyparsing.operatorPrecedence(
    comparison_expr | boolean_literal,
    [
        (NotNode.group(not_operator), 1, pyparsing.opAssoc.RIGHT),
        (AndNode.group(and_operator), 2, pyparsing.opAssoc.LEFT),
        (OrNode.group(or_operator),  2, pyparsing.opAssoc.LEFT),
    ])

grammar = boolean_expr


def search(string):
    try:
        return grammar.parseString(string, parseAll=True)
    except pyparsing.ParseException:
        return False

def get_query(query):
    return_Q = Q()
    iterable = iter(xrange(len(query)))
    for i in iterable:
        if type(query[i]) is pyparsing.ParseResults:
            return_Q = get_query(query[i])
        if type(query[i]) is AndNode:
            return_Q &= get_element(query[i + 1])
            next(iterable)
        if type(query[i]) is OrNode:
            return_Q |= get_element(query[i + 1])
            next(iterable)
        if type(query[i]) is ComparisonNode:
            return_Q &= Q(**{query[i][0] + '__exact': query[i][2]})

    return return_Q


def get_element(element):

    if type(element) is ComparisonNode:
        return Q(**{element[0] + '__exact': element[2]})

    if type(element) is pyparsing.ParseResults:
        return get_query(element)

