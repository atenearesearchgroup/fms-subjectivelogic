import argparse
import functools

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from uncertainty.utypes import *

from fm_sublog.models import FUSION_OPERATORS
from fm_sublog import utils
from fm_sublog import fm_utils


def main(fm_path: str, opinions_path: str, strong_opinions: bool, threshold: float):
    fm = UVLReader(fm_path).transform()  # NOTE: the feature model is not used in this script.
    opinions = utils.read_opinions(opinions_path, strong_opinions)

    features ={f for stakeholder in opinions.values() for f in stakeholder.keys()}
    
    print(f'FEATURES DECISIONS (Threshold: {threshold}):')
    count = 1
    for feature_name in features:
        # feature =  fm.get_feature_by_name(feature_name)
        # if feature is None:
        #     raise Exception(f'Feature {feature_name} does not exist in the feature model {fm_path}.')
        fusion_operator = utils.get_fusion_operator_for_feature(feature_name, opinions)
        feature_op = utils.get_fused_opinion_for_feature(feature_name, opinions)
        yes_no = 'YES' if feature_op.projection() > threshold else 'NO'
        print(f'{count}: {feature_name}. Fused opinion ({fusion_operator}): {feature_op} -> {feature_op.projection()} -> {yes_no}')
        count += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evolution Scenario 1 (Feature Model Evolution): Decision making tool based on the provided stakeholder's opinions to decide the evolution of the feature model.")
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Feature model (.uvl).')
    parser.add_argument('-o', '--opinions', dest='opinions', type=str, required=True, help="Stakeholders' opinions (.csv).")
    parser.add_argument('-s', '--strong_opinions', dest='strong_opinions', action='store_true', required=False, default=False, help="Consider strong degrees of uncertainty for stakelholder's opinions (default moderate).")
    parser.add_argument('-t', '--threshold', dest='threshold', required=False, type=float, default=0.5, help="Threshold to consider in the decisions.")
    args = parser.parse_args()

    main(args.feature_model, args.opinions, args.strong_opinions, args.threshold)
