import csv
import functools
from typing import Callable

from uncertainty.utypes import *

from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.configuration_metamodel.models import Configuration

from fm_sublog.models import FMOpinion, UNCERTAINTY_DEGREES, FUSE_OPERATORS


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
            if header != 'Element':
                opinions[header] = dict()
                
        for row in reader:
            element = row['Element']
            for stakeholder in opinions:
                op_str = row[stakeholder]
            
                # Parse opinion
                if op_str in UNCERTAINTY_DEGREES:
                    opinion = FMOpinion.from_uncertainty_degree(element, op_str, strong_opinions)
                else:
                    try:
                        op = eval(op_str)
                        if isinstance(op, tuple):
                            opinion = FMOpinion.from_tuple(element, op)
                        else:
                            raise Exception(f'Invalid format for opinion at element {element}: {op}')
                    except:
                        raise Exception(f'Invalid opinion at element {element}: {op_str}')
                opinions[stakeholder].update({element: opinion})
    return opinions


def get_product_opinion(product: Configuration, opinions: dict[str, FMOpinion]) -> sbool:
    """Return the SBoolean vector for the opinion of a stakeholder applying the AND operator."""
    features_op = [opinions[f].opinion if product.elements[f] else ~opinions[f].opinion for f in opinions]
    return functools.reduce(lambda a, b: a & b, features_op)


def get_product_opinions(product: Configuration, opinions: dict[str, dict[str, FMOpinion]]) -> sbool:
    """Return a list of SBoolean vectors for the opinions of all stakeholder."""
    return [get_product_opinion(product, opinions[stakeholder]) for stakeholder in opinions]

def rank_products(products: list[Configuration], opinions: dict[str, dict[str, FMOpinion]], fuse_operator: Callable) -> dict[Configuration, tuple[sbool, float]]:
    """Given a list of products, return the products ranked by their projection based on the opinions of the stakeholders."""
    rank = dict()
    for product in products:
        product_opinions = get_product_opinions(product, opinions)
        fuse_opinion = fuse_operator(product_opinions)
        projection = fuse_opinion.projection()        
        rank[product] = (fuse_opinion, projection)
    
    return sorted(rank.items(), key=lambda x : x[1][1], reverse=True)
