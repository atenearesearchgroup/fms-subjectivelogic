from uncertainty.utypes import *


STRONG_OPINIONS = {'CERTAIN': sbool(1.00, 0.00, 0.00, 0.50),
                   'PROBABLE': sbool(0.67, 0.00, 0.33, 0.50),
                   'POSSIBLE': sbool(0.33, 0.00, 0.67, 0.50),
                   'UNCERTAIN': sbool(0.00, 0.00, 1.00, 0.50),
                   'IMPROBABLE': sbool(0.00, 0.33, 0.67, 0.50),
                   'UNLIKELY': sbool(0.00, 0.33, 0.67, 0.50),
                   'IMPOSSIBLE': sbool(0.00, 1.00, 0.00, 0.50)}

MODERATE_OPINIONS = {'CERTAIN': sbool(1.00, 0.00, 0.00, 0.50),
                     'PROBABLE': sbool(0.75, 0.05, 0.20, 0.50),
                     'POSSIBLE': sbool(0.45, 0.15, 0.40, 0.50),
                     'UNCERTAIN': sbool(0.20, 0.20, 0.60, 0.50),
                     'IMPROBABLE': sbool(0.15, 0.45, 0.40, 0.50),
                     'UNLIKELY': sbool(0.05, 0.75, 0.20, 0.50),
                     'IMPOSSIBLE': sbool(0.00, 1.00, 0.00, 0.50)}

UNCERTAINTY_DEGREES = [STRONG_OPINIONS.keys()]

FUSION_OPERATORS = {'CBF': sbool.cbFusion,
                    'CCF': sbool.ccFusion,
                    'aCBF': sbool.aleatoryCumulativeFusion,
                    'eCBF': sbool.epistemicCumulativeFusion,
                    'ABF': sbool.averagingFusion,
                    'WBF': sbool.weightedFusion,
                    'MinBF': sbool.minimumFusion,
                    'MajBF': sbool.majorityFusion}


class FMOpinion():

    def __init__(self, element: str, opinion: sbool, fusion_operator: str = 'CBF') -> None:
        self.element = element
        self.opinion = opinion
        self.fusion_operator = fusion_operator

    @classmethod
    def from_tuple(cls, element: str, opinion: tuple[float], fusion_operator: str = 'CBF') -> 'FMOpinion':
        return cls(element, sbool(*opinion), fusion_operator)
    
    @classmethod
    def from_uncertainty_degree(cls, element: str, uncertainty_degree: str, strong: bool = False, fusion_operator: str = 'CBF') -> 'FMOpinion':
        return cls(element, STRONG_OPINIONS[uncertainty_degree.upper()], fusion_operator) if strong else cls(element, MODERATE_OPINIONS[uncertainty_degree.upper()], fusion_operator)

    def __str__(self) -> str:
        return f'{self.element}: {self.opinion} ({self.fusion_operator})'
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}; element: {self.element}, opinion: {self.opinion}, fusion_operator: {self.fusion_operator}'