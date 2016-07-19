import unittest
import pyparsing
from interface.advanced_search import ComparisonNode, search, AndNode, OrNode, get_query

# Search string --> [ expected parse tree, expected mongo query ]
search_dict = {

    'url = amazon': [
        pyparsing.ParseResults([ComparisonNode(['url', '$regex', 'amazon'])]),
        {'url': {'$regex': 'amazon'}}
    ],

    'url == amazon': [
        pyparsing.ParseResults([ComparisonNode(['url', '==', 'amazon'])]),
        {'url': 'amazon'}
    ],

    'url ~ ./amazon./:_-': [
        pyparsing.ParseResults([ComparisonNode(['url', '$regex', './amazon./: -'])]),
        {'url': {'$regex': './amazon./: -'}}
    ],

    'id $gte 1': [
        pyparsing.ParseResults([ComparisonNode(['frontend_id', '$gte', '1'])]),
        {'frontend_id': {'$gte': '1'}}
    ],

    'id $gt 1': [
        pyparsing.ParseResults([ComparisonNode(['frontend_id', '$gt', '1'])]),
        {'frontend_id': {'$gt': '1'}}
    ],

    'id $lte 1': [
        pyparsing.ParseResults([ComparisonNode(['frontend_id', '$lte', '1'])]),
        {'frontend_id': {'$lte': '1'}}
    ],

    'id $lt 1': [
        pyparsing.ParseResults([ComparisonNode(['frontend_id', '$lt', '1'])]),
        {'frontend_id': {'$lt': '1'}}
    ],

    'timestamp $gte 2016-07-07_12:00:00': [
        pyparsing.ParseResults(
            [
                ComparisonNode(['timestamp', '$gte', '2016-07-07 12:00:00'])
            ]
        ),
        {'timestamp': {'$gte': '2016-07-07 12:00:00'}}
    ],

    'timestamp == 2016-07-07': [
        pyparsing.ParseResults(
            [
                ComparisonNode(['timestamp', '==', '2016-07-07'])
            ]
        ),
        {'timestamp': '2016-07-07'}
    ],

    'url = amazon and id == 1': [
        [
            [ComparisonNode(['url', '$regex', 'amazon']),
             AndNode(['and']),
             ComparisonNode(['frontend_id', '==', '1'])
             ]
        ],
        {'$and': [{'url': {'$regex': 'amazon'}}, {'frontend_id': '1'}]}
    ],

    'url = amazon or id == 1': [
        [
            [ComparisonNode(['url', '$regex', 'amazon']),
             OrNode(['or']),
             ComparisonNode(['frontend_id', '==', '1'])
             ]
        ],
        {'$or': [{'url': {'$regex': 'amazon'}}, {'frontend_id': '1'}]}
    ],

    # and has precedence over or
    'url = amazon and id == 1 or id == 2': [
        [
            [
                [ComparisonNode(['url', '$regex', 'amazon']),
                 AndNode(['and']),
                 ComparisonNode(['frontend_id', '==', '1'])
                 ],
                OrNode(['or']),
                ComparisonNode(['frontend_id', '==', '2'])
            ]
        ],
        {'$or': [{'$and': [{'url': {'$regex': 'amazon'}}, {'frontend_id': '1'}]}, {'frontend_id': '2'}]}
    ],

    'url = amazon or id == 1 and id == 2': [
        [
            [
                ComparisonNode(['url', '$regex', 'amazon']),
                OrNode(['or']),
                [ComparisonNode(['frontend_id', '==', '1']),
                 AndNode(['and']),
                 ComparisonNode(['frontend_id', '==', '2'])
                 ]

            ]
        ],
        {'$or': [{'url': {'$regex': 'amazon'}}, {'$and': [{'frontend_id': '1'}, {'frontend_id': '2'}]}]}
    ],

    'url = amazon and id == 1 and id == 2': [
        [
            [
                ComparisonNode(['url', '$regex', 'amazon']),
                AndNode(['and']),
                ComparisonNode(['frontend_id', '==', '1']),
                AndNode(['and']),
                ComparisonNode(['frontend_id', '==', '2'])


            ]
        ],
        {'$and': [{'$and': [{'url': {'$regex': 'amazon'}}, {'frontend_id': '1'}]}, {'frontend_id': '2'}]}
    ],

    # add parentheses to give or precedence
    'url = amazon and (id == 1 or id == 2)': [
        [
            [
                ComparisonNode(['url', '$regex', 'amazon']),
                AndNode(['and']),
                [
                    ComparisonNode(['frontend_id', '==', '1']),
                    OrNode(['or']),
                    ComparisonNode(['frontend_id', '==', '2'])
                ]
            ]
        ],
        {'$and': [{'url': {'$regex': 'amazon'}}, {'$or': [{'frontend_id': '1'}, {'frontend_id': '2'}]}]}
    ],

    # long combination
    '(id == 1 or id == 2) and (url == amazon or id $gte 1)': [
        [
            [
                [
                    ComparisonNode(['frontend_id', '==', '1']),
                    OrNode(['or']),
                    ComparisonNode(['frontend_id', '==', '2'])

                ],
                AndNode(['and']),
                [
                    ComparisonNode(['url', '==', 'amazon']),
                    OrNode(['or']),
                    ComparisonNode(['frontend_id', '$gte', '1'])
                ]
            ]


        ],
        {'$and':
            [
                {'$or':
                    [{'frontend_id': '1'}, {'frontend_id': '2'}]
                 },
                {'$or':
                    [{'url': 'amazon'}, {'frontend_id': {'$gte': '1'}}]
                 }
            ]
         }
    ]

}

# String which are meant to return False by parser
exception_searches = [

    'url == amazon and',  # invalid and expression
    'or url $gte 1',  # invalid or expression
    'and = 1',  # and as field key
    'timestamp > 1'  # > character is not used
    '% #@&`|;',  # other invalid characters
    'this_field = google'  # invalid field name

]


class TestParseTree(unittest.TestCase):

    # Create valid parse tree from string
    def test_string_to_parse_tree(self):
        for string in search_dict:
            self.assertEqual(search(string).asList(),
                             list(search_dict[string][0])
                             )

    # Non valid strings return false for parse tree
    def test_exceptions_searches(self):
        for string in exception_searches:
            self.assertFalse(search(string))

    # Create valid mongo query from parse tree
    def test_parse_tree_to_mongo_query(self):
        for string in search_dict:
            self.assertEqual(get_query(search(string)), search_dict[string][1])


