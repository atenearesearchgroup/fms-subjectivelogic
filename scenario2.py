import argparse
import functools

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from uncertainty.utypes import *

from fm_sublog.models import FUSION_OPERATORS
from fm_sublog import utils
from fm_sublog import fm_utils


def main(fm_path: str, opinions_path: str, strong_opinions: bool):
    fm = UVLReader(fm_path).transform()
    opinions = utils.read_opinions(opinions_path, strong_opinions)

    features ={f for stakeholder in opinions.values() for f in stakeholder.keys()}
    analyzed_features = set()

    # Features with cross-tree constraints
    print('FEATURES WITH CROSS-TREE CONSTRAINTS:')
    count = 1
    for feature_name in features:
        feature =  fm.get_feature_by_name(feature_name)
        if feature not in analyzed_features:
            dependencies = fm_utils.get_feature_constraints_dependencies(fm, feature)
            if dependencies:  # feature with cross-tree constraints
                analyzed_features.add(feature)  
                involved_features = [feature] + list(dependencies)
                combined_opinions = [utils.get_opinions_for_related_features(involved_features, opinions[stakeholder]) for stakeholder in opinions]
                fusion_operator = utils.get_fusion_operator_for_feature(feature_name, opinions)
                fused_opinion = FUSION_OPERATORS[fusion_operator](combined_opinions)
                print(f'{count}: {' AND '.join([f.name for f in involved_features])}. Fused opinion ({fusion_operator}): {fused_opinion} -> {fused_opinion.projection()}')
                analyzed_features.update(dependencies)
    
    # Related group of features
    print('GROUP OF RELATED FEATURES:')
    count = 1
    for feature_name in features:
        feature =  fm.get_feature_by_name(feature_name)
        configurations = fm_utils.get_configurations_from_tree(fm, feature)
        if len(configurations) > 1:  # group of related features
            analyzed_features.add(feature) 
            print(f'Group {count}: {feature_name} subtree.')
            count += 1
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
            print(f'Overall opinion: {' OR '.join([f for f in full_formula])}. Fused opinion ({fusion_operator}): {fused_opinion} -> {fused_opinion.projection()}')

    # Independent features:
    print('INDEPENDENT FEATURES:')
    count = 1
    for feature_name in features:
        feature =  fm.get_feature_by_name(feature_name)
        if feature not in analyzed_features: 
            fusion_operator = utils.get_fusion_operator_for_feature(feature_name, opinions)
            feature_op = utils.get_fused_opinion_for_feature(feature_name, opinions)
            print(f'{count}: {feature_name}. Fused opinion ({fusion_operator}): {feature_op} -> {feature_op.projection()}')

    # Rank features
    rank_features = dict()  # str -> (sbool, projection)
    for feature_name in features:
        feature_op = utils.get_fused_opinion_for_feature(feature_name, opinions)
        rank_features[feature_name] = (feature_op, feature_op.projection())
    features_priorization = sorted(rank_features.items(), key=lambda x : x[1][1], reverse=True)

    print("RANKING OF FEATURE PRIORITIES:")
    for i, (f, v) in enumerate(features_priorization, 1):
        print(f'{i}. {f}: {v[0]} -> {v[1]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evolution Scenario 2 (Next Release Problem): Decision making tool based on the provided stakeholder's opinions to help prioritizing the next features to be develop.")
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Feature model (.uvl).')
    parser.add_argument('-o', '--opinions', dest='opinions', type=str, required=True, help="Stakeholders' opinions (.csv).")
    parser.add_argument('-s', '--strong_opinions', dest='strong_opinions', action='store_true', required=False, default=False, help="Consider strong degrees of uncertainty for stakelholder's opinions (default moderate).")
    args = parser.parse_args()

    main(args.feature_model, args.opinions, args.strong_opinions)
