import argparse

from flamapy.metamodels.configuration_metamodel.models import Configuration
from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber

#from uncertainty.utypes import *

from fm_sublog.models import FUSION_OPERATORS
from fm_sublog import utils
from fm_sublog import fm_utils
from fm_sublog.evaluation_utils import timer



TIME_GENERATION = 'TIME_GENERATION'
TIME_RANKING = 'TIME_RANKING'


def main(fm_path: str, opinions_path: str, n_products: int, fusion_operator: str, strong_opinions: bool):
    fm = UVLReader(fm_path).transform()
    opinions = utils.read_opinions(opinions_path, strong_opinions)
    
    bdd_model = FmToBDD(fm).transform()
    n_products = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Products: {n_products}')

    # Generate products
    with timer.Timer(name=TIME_GENERATION, logger=None):
        products = fm_utils.generate_products(fm, n_products)

    print(f'Products SAT: {len(products)}')
    products_fixed = []
    for p in products:
        elements = {f: True for f in p}
        products_fixed.append(Configuration(elements))
    products = products_fixed
    with timer.Timer(name=TIME_RANKING, logger=None):
        rank = utils.rank_products(products, opinions, FUSION_OPERATORS[fusion_operator])

    print('PRODUCTS RANKING:')
    # for i, (p, v) in enumerate(rank, 1):
    #     print(f'{i}. {[f for f in p.get_selected_elements()]}: {v[0]} -> {v[1]}')

    time_generation = round(timer.Timer.timers[TIME_GENERATION], 4)
    time_ranking = round(timer.Timer.timers[TIME_RANKING], 4)

    print(f'#Features: {len(fm.get_features())}')
    print(f'#Constraints: {len(fm.get_constraints())}')
    print(f'#Products: {len(products)}')
    print(f'Time (generation): {time_generation} s.')
    print(f'Time (ranking): {time_ranking} s.')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evolution Scenario 3 (Variability Reduction): Generate a given number of products from the feature model and rank them based on the provided stakeholder's opinions to help decide the final products to be realized.")
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Feature model (.uvl).')
    parser.add_argument('-o', '--opinions', dest='opinions', type=str, required=False, default=None, help="Stakeholders' opinions (.csv).")
    parser.add_argument('-n', '--n_products', dest='n_products', type=int, required=False, default=0, help='Number of products to rank (default all).')
    parser.add_argument('-f', '--fusion_operator', dest='fusion_operator', type=str, required=False, default='ABF', help=f'Fusion operator: {[f for f in FUSION_OPERATORS.keys()]} (default ABF). ')
    parser.add_argument('-s', '--strong_opinions', dest='strong_opinions', action='store_true', required=False, default=False, help="Consider strong degrees of uncertainty for stakelholder's opinions (default moderate).")
    args = parser.parse_args()

    if args.fusion_operator not in FUSION_OPERATORS:
        exit(f'Invalid fusion operator {args.fusion_operator}. Use one of {[f for f in FUSION_OPERATORS]}')
        
    main(args.feature_model, args.opinions, args.n_products, args.fusion_operator, args.strong_opinions)
