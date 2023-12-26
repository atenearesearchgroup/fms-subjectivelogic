import argparse

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import (
    BDDProductsNumber,
    BDDSampling
)
#from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
#from flamapy.metamodels.pysat_metamodel.operations import Glucose3Products

from uncertainty.utypes import *

from fm_sublog.models import FUSE_OPERATORS
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
    
    # Generate products
    products = fm_utils.generate_products(fm, n_products)
    
    # Get opinions from stakeholders:
    #opinions = utils.get_product_opinion(products[0], opinions['Stakeholder1'])
    rank = utils.rank_products(products, opinions, FUSE_OPERATORS['ABF'])
    for i, (p, v) in enumerate(rank, 1):
        print(f'{i}: {p} -> {v}')
    
    #opinions = [get_product_opinion(product, opinions[stakeholder]) for stakeholder in opinions)]
    #print(opinion)   

    raise Exception
    result = sbool.epistemicCumulativeFusion(deciding_on_an_independent_feature)
    print(f'Deciding on an independent feature (ECBF): {result} -> {result.projection()}')
    
    abf_result = sbool.averagingFusion(CP_AND_NFC)
    wbf_result = sbool.weightedFusion(CP_AND_NFC)
    ccf_result = sbool.ccFusion(CP_AND_NFC)
    print(f'Deciding on a feature with cross-tree constraints (ABF): {abf_result} -> {abf_result.projection()}')
    print(f'Deciding on a feature with cross-tree constraints (WBF): {wbf_result} -> {wbf_result.projection()}')
    print(f'Deciding on a feature with cross-tree constraints (CCF): {ccf_result} -> {ccf_result.projection()}')

    #sat_model = FmToPysat(fm).transform()
    #products = Glucose3Products().execute(sat_model).get_result()
    #for i, p in enumerate(products, 1):
    #    print(f'P{i}: {p}')

    bdd_model = FmToBDD(fm).transform()

    n_products = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Products: {n_products}')

    products = BDDSampling(size=n_products).execute(bdd_model).get_result()
    for i, p in enumerate(products, 1):
        print(f'P{i}: {p}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evolution Scenario 3: Variability Reduction.')
    parser.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, required=True, help='Feature model (.uvl).')
    parser.add_argument('-o', '--opinions', dest='opinions', type=str, required=True, help="Stakeholders' opinions (.csv).")
    parser.add_argument('-n', '--n_products', dest='n_products', type=int, required=False, default=0, help='Number of products to rank (default all).')
    args = parser.parse_args()

    main(args.feature_model, args.opinions, args.n_products)
