import argparse
import functools

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductsNumber,
    BDDSampling
)
#from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
#from flamapy.metamodels.pysat_metamodel.operations import Glucose3Products

from uncertainty.utypes import *

from fm_sublog.models import FUSION_OPERATORS
from fm_sublog import utils
from fm_sublog import fm_utils


FM_PATH = 'models/miband5.uvl'

deciding_on_an_independent_feature = [
    sbool(0.95, 0.00, 0.05, 0.50), 
    sbool(0.10, 0.70, 0.20, 0.50), 
    sbool(0.30, 0.05, 0.65, 0.50)
]

deciding_on_a_feature_with_constraints_CP = [
    sbool(0.50, 0.10, 0.40, 0.50), 
    sbool(0.90, 0.03, 0.07, 0.50), 
    sbool(0.80, 0.15, 0.05, 0.50)
]

deciding_on_a_feature_with_constraints_NFC = [
    sbool(0.50, 0.25, 0.25, 0.50), 
    sbool(0.75, 0.20, 0.05, 0.50), 
    sbool(0.94, 0.03, 0.03, 0.50)
]

CP_AND_NFC = [x & y for x, y in zip(deciding_on_a_feature_with_constraints_CP, deciding_on_a_feature_with_constraints_NFC)]


def main(fm_path: str, opinions_path: str, n_products: int):
    fm = UVLReader(fm_path).transform()
    opinions = utils.read_opinions(opinions_path)

    features ={f for stakeholder in opinions.values() for f in stakeholder.keys()}
    analyzed_features = set()

    # Features with cross-tree constraints
    for feature_name in features:
        feature =  fm.get_feature_by_name(feature_name)
        if feature not in analyzed_features:
            dependencies = fm_utils.get_feature_constraints_dependencies(fm, feature)
            if dependencies:  # feature with cross-tree constraints
                analyzed_features.add(feature)  
                print(f'{feature_name} -> feature with cross-tree constraints.')
                involved_features = [feature] + list(dependencies)
                combined_opinions = [utils.get_opinions_for_related_features(involved_features, opinions[stakeholder]) for stakeholder in opinions]
                fusion_operator = utils.get_fusion_operator_for_feature(feature_name, opinions)
                fused_opinion = FUSION_OPERATORS[fusion_operator](combined_opinions)
                print(f'{' AND '.join([f.name for f in involved_features])}. Fused opinion ({fusion_operator}): {fused_opinion} -> {fused_opinion.projection()}')
                analyzed_features.update(dependencies)
    
    # Related group of features
    for feature_name in features:
        feature =  fm.get_feature_by_name(feature_name)
        configurations = fm_utils.get_configurations_from_tree(fm, feature)
        if len(configurations) > 1:  # group of related features
            analyzed_features.add(feature) 
            print(f'{feature_name} -> group of related features.')
            full_formula = []
            full_formula_opinions = {stakeholder: [] for stakeholder in opinions.keys()}

            for config in configurations:
                involved_features = [f for f in config.get_selected_elements() if f.name in features]
                combined_opinions = [utils.get_opinions_for_related_features(involved_features, opinions[stakeholder]) for stakeholder in opinions]
                fusion_operator = utils.get_fusion_operator_for_feature(feature_name, opinions)
                fused_opinion = FUSION_OPERATORS[fusion_operator](combined_opinions)
                print(f'{' AND '.join([f.name for f in involved_features])}. Fused opinion ({fusion_operator}): {fused_opinion} -> {fused_opinion.projection()}')
                
                analyzed_features.update(involved_features)
                full_formula.append('(' + ' AND '.join([f.name for f in involved_features]) + ')')

                for stakeholder in opinions:
                    full_formula_opinions[stakeholder].append(utils.get_opinions_for_related_features(involved_features, opinions[stakeholder]))
            
            overall_opinions = []
            for stakeholder in full_formula_opinions:
                overall_opinions.append(functools.reduce(lambda a, b: a | b, full_formula_opinions[stakeholder])) 
            fused_opinion = FUSION_OPERATORS[fusion_operator](overall_opinions)
            print(f'{' OR '.join([f for f in full_formula])}. Fused opinion ({fusion_operator}): {fused_opinion} -> {fused_opinion.projection()}')

    # Independent features:
    for feature_name in features:
        feature =  fm.get_feature_by_name(feature_name)
        if feature not in analyzed_features: 
            print(f'{feature_name} -> independent feature.')

    # Rank features
    rank_features = dict()  # str -> (sbool, projection)
    for feature_name in features:
        feature_op = utils.get_fused_opinion_for_feature(feature_name, opinions)
        rank_features[feature_name] = (feature_op, feature_op.projection())
    features_priorization = sorted(rank_features.items(), key=lambda x : x[1][1], reverse=True)
    for i, (f, v) in enumerate(features_priorization, 1):
        print(f'{i}. {f}: {v}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evolution Scenario 2 (Next Release Problem): Generate a given number of products from the feature model and rank them based on the provided stakeholder's opinions to help decide the final products to be realized.")
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Feature model (.uvl).')
    parser.add_argument('-o', '--opinions', dest='opinions', type=str, required=True, help="Stakeholders' opinions (.csv).")
    parser.add_argument('-n', '--n_products', dest='n_products', type=int, required=False, default=0, help='Number of products to rank (default all).')
    parser.add_argument('-f', '--fusion_operator', dest='fusion_operator', type=str, required=False, default='CBF', help=f'Fusion operator: {[f for f in FUSION_OPERATORS.keys()]} (default CBF). ')
    parser.add_argument('-s', '--strong_opinions', dest='strong_opinions', action='store_true', required=False, default=False, help="Consider strong degrees of uncertainty for stakelholder's opinions (default moderate).")
    args = parser.parse_args()

    main(args.feature_model, args.opinions, args.n_products)
