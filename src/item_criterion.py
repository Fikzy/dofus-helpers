class GroupItemCriterion:

    _criteria: list
    _operators: list[str]
    _criterion_text_from: str
    _clean_criterion_text_from: str
    _malformed: bool = False
    _single_operator_type: bool = False

    def __init__(self, criterion: str):

        if not criterion:
            return

        self._criterion_text_from = criterion
        self._clean_criterion_text_from = criterion.replace(" ", "")
        delimited_array = self._clean_criterion_text_from.split()
