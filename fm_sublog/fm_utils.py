from flamapy.metamodels.fm_metamodel.models import FeatureModel

from flamapy.metamodels.configuration_metamodel.models import Configuration

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber, BDDSampling


def generate_products(fm: FeatureModel, n_configs: int = 0) -> list[Configuration]:
    """Random sampling of a given number of products from the feature model.
    If the number is 0, all possible products are returned."""
    bdd_model = FmToBDD(fm).transform()
    if n_configs == 0:
        n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    return BDDSampling(size=n_configs).execute(bdd_model).get_result()
    