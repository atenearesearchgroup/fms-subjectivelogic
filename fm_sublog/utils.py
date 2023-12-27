import csv
import functools
from typing import Callable

from uncertainty.utypes import *

from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature
from flamapy.metamodels.configuration_metamodel.models import Configuration

from fm_sublog.models import FMOpinion, UNCERTAINTY_DEGREES, FUSION_OPERATORS


HEADER_ELEMENT = 'Element'
HEADER_FUSIONOPERATOR = 'FusionOperator'

# def read_opinions(csv_filepath: str, strong_opinions: bool = False) -> dict[str, list[FMOpinion]]:
#     """Reader for FM element opinions in .csv.

#     The csv format is as follow:

#     Element, Opinion
#     featureNameA, opinion1
#     featureNameA, opinion2
#     featureNameA, opinion3
#     featureNameB, opinion1
#     ...
    
#     where Element can be the name of a feature, relation or constraint,
#     Opinions can be a list of values representing a SBoolean vector or a string constant representing the degree of uncertainty.

#     Return a dictionary of "featureName -> list of opinions".
#     """
#     opinions = dict()
#     with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile, delimiter=',', quotechar='"', skipinitialspace=True)
#         for row in reader:
#             element = row['Element']
#             op_str = row['Opinion']
            
#             # Parse opinion
#             if op_str in UNCERTAINTY_DEGREES:
#                 opinion = FMOpinion.from_uncertainty_degree(element, v, strong_opinions)
#             else:
#                 try:
#                     print(f'{op_str}, {type(op_str)}')
#                     op = eval(op_str)
#                     if isinstance(op, tuple):
#                         opinion = FMOpinion.from_tuple(element, op)
#                     else:
#                         raise Exception(f'Invalid format for opinion at element {element}: {op}')
#                 except:
#                     raise Exception(f'Invalid opinion at element {element}: {op_str}')

#             if element in opinions:
#                 opinions[element].append(opinion)
#             else:
#                 opinions[element] = [opinion]
#     return opinions


def read_opinions(csv_filepath: str, strong_opinions: bool = False) -> dict[str, dict[str, FMOpinion]]:
    """Reader for FM element opinions in .csv.

    The csv format is as follow:

    Element, OpinionStakeholder1, OpinionStakeholder2,...
    featureNameA, opinion1, opinion2,...
    featureNameB, opinion1, opinion2,...
    ...
    
    where Element can be the name of a feature, relation or constraint,
    Opinions can be a list of values representing a SBoolean vector or a string constant representing the degree of uncertainty.

    Return a dictionary of "stakeholder" -> dict of "featureName" -> opinion".
    """
    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"', skipinitialspace=True)
        
        opinions = dict()
        for header in reader.fieldnames:
            if header not in [HEADER_ELEMENT, HEADER_FUSIONOPERATOR]:
                opinions[header] = dict()
                
        for row in reader:
            element = row.get(HEADER_ELEMENT)
            fusion_operator = row.get(HEADER_FUSIONOPERATOR)
            if fusion_operator:
                if fusion_operator not in FUSION_OPERATORS:
                    raise Exception(f'Invalid fusion operator at element {element}: {fusion_operator}')
            else:
                fusion_operator = 'CBF'
            
            for stakeholder in opinions:
                op_str = row.get(stakeholder)
            
                if op_str:  # if there is an opinion for this stakeholder    
                    # Parse opinion
                    if op_str in UNCERTAINTY_DEGREES:
                        opinion = FMOpinion.from_uncertainty_degree(element, op_str, strong_opinions, fusion_operator)
                    else:
                        try:
                            op = eval(op_str)
                            if isinstance(op, tuple):
                                opinion = FMOpinion.from_tuple(element, op, fusion_operator)
                            else:
                                raise Exception(f'Invalid format for opinion at element {element}: {op}')
                        except:
                            raise Exception(f'Invalid opinion at element {element}: {op_str}')
                    opinions[stakeholder].update({element: opinion})
    return opinions


def get_product_opinion(product: Configuration, stakeholder_opinions: dict[str, FMOpinion]) -> sbool:
    """Return the SBoolean vector for the opinion of a stakeholder applying the AND operator."""
    features_op = [stakeholder_opinions[f].opinion if product.elements[f] else ~stakeholder_opinions[f].opinion for f in stakeholder_opinions]
    return functools.reduce(lambda a, b: a & b, features_op)


def get_product_opinions(product: Configuration, opinions: dict[str, dict[str, FMOpinion]]) -> list[sbool]:
    """Return a list of SBoolean vectors for the opinions of all stakeholder."""
    return [get_product_opinion(product, opinions[stakeholder]) for stakeholder in opinions]


def rank_products(products: list[Configuration], opinions: dict[str, dict[str, FMOpinion]], fusion_operator: Callable) -> dict[Configuration, tuple[sbool, float]]:
    """Given a list of products, return the products ranked by the projection based on the opinions of the stakeholders."""
    rank = dict()
    for product in products:
        product_opinions = get_product_opinions(product, opinions)
        fuse_opinion = fusion_operator(product_opinions)
        projection = fuse_opinion.projection()        
        rank[product] = (fuse_opinion, projection)
    
    return sorted(rank.items(), key=lambda x : x[1][1], reverse=True)


def get_opinions_for_related_features(features: list[Feature], stakeholder_opinions: dict[str, FMOpinion]) -> sbool:
    """Return the opinion combination of a stakeholder for a list of related/dependent features, combining them using the AND operators."""
    features_op = [stakeholder_opinions[f.name].opinion for f in features if f.name in stakeholder_opinions]
    return functools.reduce(lambda a, b: a & b, features_op)


def get_fusion_operator_for_feature(feature_name: str, opinions: dict[str, dict[str, FMOpinion]]) -> Callable:
    for feature_opinion in opinions.values():
        opinion = feature_opinion.get(feature_name)
    return opinion.fusion_operator


def get_fused_opinion_for_feature(feature_name: str, opinions: dict[str, dict[str, FMOpinion]]) -> sbool:
    feature_opinions = []
    for stakeholder in opinions:
        feature_opinions.append(opinions[stakeholder][feature_name].opinion)
    fusion_operator = get_fusion_operator_for_feature(feature_name, opinions)
    fused_opinion = FUSION_OPERATORS[fusion_operator](feature_opinions)
    return fused_opinion