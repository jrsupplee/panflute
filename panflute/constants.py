
__all__ = ['LIST_NUMBER_STYLES', 'LIST_NUMBER_DELIMITERS', 'TABLE_ALIGNMENT',
           'QUOTE_TYPES', 'CITATION_MODE', 'MATH_FORMATS', 'RAW_FORMATS',
           'SPECIAL_ELEMENTS', 'EMPTY_ELEMENTS']

from .elements import Null, Space, HorizontalRule, SoftBreak, LineBreak


# ---------------------------
# Constants
# ---------------------------

LIST_NUMBER_STYLES = {
    'DefaultStyle', 'Example', 'Decimal', 'LowerRoman',
    'UpperRoman', 'LowerAlpha', 'UpperAlpha'
}

LIST_NUMBER_DELIMITERS = {'DefaultDelim', 'Period', 'OneParen', 'TwoParens'}

TABLE_ALIGNMENT = {'AlignLeft', 'AlignRight', 'AlignCenter', 'AlignDefault'}

QUOTE_TYPES = {'SingleQuote', 'DoubleQuote'}

CITATION_MODE = {'AuthorInText', 'SuppressAuthor', 'NormalCitation'}
# AuthorInText: @foo - as John Doe (1921) said
# SupressAuthor: [-@foo]

MATH_FORMATS = {'DisplayMath', 'InlineMath'}

RAW_FORMATS = {'html', 'tex', 'latex'}

SPECIAL_ELEMENTS = LIST_NUMBER_STYLES | LIST_NUMBER_DELIMITERS | \
                   MATH_FORMATS | TABLE_ALIGNMENT | QUOTE_TYPES | CITATION_MODE

EMPTY_ELEMENTS = {Null, Space, HorizontalRule, SoftBreak, LineBreak}
