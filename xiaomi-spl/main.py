from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.pysat_metamodel.operations import Glucose3Products


FM_PATH = 'models/miband5.uvl'


def main():
    fm = UVLReader(FM_PATH).transform()
    sat_model = FmToPysat(fm).transform()

    products = Glucose3Products().execute(sat_model).get_result()
    for i, p in enumerate(products, 1):
        print(f'P{i}: {p}')


if __name__ == '__main__':
    main()
