import copy
import itertools

from flamapy.core.models import ASTOperation
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature, Constraint

from flamapy.metamodels.configuration_metamodel.models import Configuration

from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD
from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber, BDDSampling

from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.pysat_metamodel.operations import Glucose3Products


def generate_products(fm: FeatureModel, n_configs: int = 0) -> list[Configuration]:
    """Random sampling of a given number of products from the feature model.
    If the number is 0, all possible products are returned."""
    sat_model = FmToPysat(fm).transform()
    return Glucose3Products().execute(sat_model).get_result()


def generate_productsBDD(fm: FeatureModel, n_configs: int = 0) -> list[Configuration]:
    """Random sampling of a given number of products from the feature model.
    If the number is 0, all possible products are returned."""
    bdd_model = FmToBDD(fm).transform()
    if n_configs == 0:
        n_configs = BDDProductsNumber().execute(bdd_model).get_result()
    return BDDSampling(size=n_configs).execute(bdd_model).get_result()

def get_feature_constraints_dependencies(fm: FeatureModel, feature: Feature, analyzed_features: set[Feature] = set()) -> set[Feature]:
    """Return the list of features that depend on the given feature of a feature model."""
    # Get constraints dependencies 
    # NOTE: this is a simplification that takes all the feature involved in the same constraints that the given feature.
    # NOTE: only consider REQUIRES constraints
    dependencies = set()
    for ctc in fm.get_constraints():
        if is_requires_constraint(ctc):
            left, right = left_right_features_from_simple_constraint(ctc)
            if feature.name == left:
                dependencies.add(fm.get_feature_by_name(right))
    
    new_dependencies = set()
    for f in dependencies:
        if f not in analyzed_features:
            analyzed_features.add(f)
            new_dependencies.update(get_feature_constraints_dependencies(fm, f, analyzed_features))
    dependencies.update(new_dependencies)
    return dependencies


def get_feature_ancestors(feature: Feature) -> list[Feature]:
    return [] if feature.is_root() else [feature.get_parent()] + get_feature_ancestors(feature.get_parent())


def get_configurations_from_tree(fm: FeatureModel, feature: Feature) -> list[Configuration]:
    """Given a root feature, return all possible configurations of the tree."""
    feature_config = Configuration(elements={feature: True})
    if feature.is_leaf():
        return [feature_config]
    all_configs = []
    for relation in feature.get_relations():
        if relation.is_mandatory():
            sub_configs = get_configurations_from_tree(fm, relation.children[0])
            configs = add_feature_to_configurations(feature, sub_configs)
            if not all_configs:
                all_configs.extend(configs)
            else:
                new_configs = []
                for c in configs:
                    copy_all_configs = copy.deepcopy(all_configs)
                    new_configs.extend(add_configurations_to_configurations([c], copy_all_configs))
                all_configs = new_configs
        elif relation.is_optional():
            sub_configs = get_configurations_from_tree(fm, relation.children[0])
            configs = add_feature_to_configurations(feature, sub_configs)
            configs.append(feature_config)
            if not all_configs:
                all_configs.extend(configs)
            else:
                copy_all_configs = copy.deepcopy(all_configs)
                all_configs = add_configurations_to_configurations(configs, all_configs)
                all_configs.extend(copy_all_configs)
        elif relation.is_alternative():
            configs = []
            for child in relation.children:
                sub_configs = get_configurations_from_tree(fm, child)
                sub_configs = add_feature_to_configurations(feature, sub_configs)
                configs.extend(sub_configs)
            all_configs.extend(configs)
        elif relation.is_or():
            configs_dict: dict[Feature, list[Configuration]] = dict()
            for child in relation.children:
                sub_configs = get_configurations_from_tree(fm, child)
                sub_configs = add_feature_to_configurations(feature, sub_configs)
                configs_dict[child] = sub_configs
            
            configs = []
            for size in range(1, len(relation.children) + 1):
                combinations = itertools.combinations(relation.children, size)
                for combi in combinations:
                    configs_combi = []
                    for child in combi:
                        configs_combi = add_configurations_to_configurations(copy.deepcopy(configs_dict[child]), configs_combi)
                    configs.extend(configs_combi)
            all_configs.extend(configs)
    return all_configs


def add_feature_to_configurations(feature: Feature, configurations: list[Configuration]) -> list[Configuration]:
    for config in configurations:
        config.elements.update({feature: True})
    return configurations


def add_configurations_to_configurations(new_configurations: list[Configuration], configurations: list[Configuration]) -> list[Configuration]:
    if not configurations:
        return new_configurations
    for config in configurations:
        for new_c in new_configurations:
            config.elements.update(new_c.elements)
    return configurations


def is_requires_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is a requires constraint."""
    root_op = constraint.ast.root
    if root_op.is_binary_op():
        if root_op.data in [ASTOperation.REQUIRES, ASTOperation.IMPLIES]:
            return root_op.left.is_term() and root_op.right.is_term()
        elif root_op.data == ASTOperation.OR:
            neg_left = root_op.left.data == ASTOperation.NOT and root_op.left.left.is_term()
            neg_right = root_op.right.data == ASTOperation.NOT and root_op.right.left.is_term()
            return neg_left and root_op.right.is_term() or neg_right and root_op.left.is_term()
    return False


def left_right_features_from_simple_constraint(simple_ctc: Constraint) -> tuple[str, str]:
    """Return the names of the features involved in a simple constraint.
    
    A simple constraint can be a requires constraint or an excludes constraint.
    A requires constraint can be represented in the AST of the constraint with one of the 
    following structures:
        A requires B
        A => B
        !A v B
    An excludes constraint can be represented in the AST of the constraint with one of the 
    following structures:
        A excludes B
        A => !B
        !A v !B
    """
    root_op = simple_ctc.ast.root
    if root_op.data in [ASTOperation.REQUIRES, ASTOperation.IMPLIES, ASTOperation.EXCLUDES]:
        left = root_op.left.data
        right = root_op.right.data
        if right == ASTOperation.NOT:
            right = root_op.right.left.data
    elif root_op.data == ASTOperation.OR:
        left = root_op.left.data
        right = root_op.right.data
        if left == ASTOperation.NOT and right == ASTOperation.NOT:  # excludes
            left = root_op.left.left.data
            right = root_op.right.left.data
        elif left == ASTOperation.NOT:  # implies: A -> B
            left = root_op.left.left.data
            right = root_op.right.data
        elif right == ASTOperation.NOT:  # implies: B -> A
            left = root_op.right.left.data
            right = root_op.left.data
    return (left, right)