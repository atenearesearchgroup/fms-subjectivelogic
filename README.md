# Table of Contents
- [Table of Contents](#table-of-contents)
- [Subjective logic applied to Feature Models](#subjective-logic-applied-to-feature-models)
  - [Description](#description)
  - [Requirements](#requirements)
  - [Download and installation](#download-and-installation)
  - [Execution of the scripts](#execution-of-the-scripts)
  
# Belief Uncertainty for Feature Models

## Description
This repository contains all the resources and artifacts associated with the paper "XX" submitted to the special issue "YYY" of the Journal of Systems & Software.

We propose to deal with the uncertainty of the stakeholders in the context of software product line (SPL) evolution by using subjective logic.
This software artifact consists on three scripts that support the three evolution scenarios proposed in the paper:
- Scenario 1: Feature model evolution
- Scenario 2: Next release problem
- Scenario 3: Variability reduction


## Requirements
The scripts are implemented 100% in Python and are built on top of [Flama](https://flamapy.github.io/) to manage and analize feature models in the UVL format, and on top of the [Uncertainty Datatypes Python Library](https://github.com/atenearesearchgroup/uncertainty-datatypes-python/blob/master/docs/UserGuide.md).
In particular, the main dependencies are:

- [Python 3.11+](https://www.python.org/)
- [Flama](https://flamapy.github.io/)
- [Uncertainty Datatypes Python Library](https://github.com/atenearesearchgroup/uncertainty-datatypes-python/blob/master/docs/UserGuide.md)

The framework has been tested in Linux (Mint and Ubuntu) and Windows 11.

## Download and installation
1. Install [Python 3.11+](https://www.python.org/). 
2. Download/Clone this repository and enter into the main directory.
3. Create a virtual environment: `python -m venv env`
4. Activate the environment: 
   
   In Linux: `source env/bin/activate`

   In Windows: `.\env\Scripts\Activate`

   ** In case that you are running Ubuntu, please install the package python3-dev with the command `sudo apt update && sudo apt install python3-dev` and update wheel and setuptools with the command `pip  install --upgrade pip wheel setuptools` right after step 4.
   
5. Install the dependencies: `pip install -r requirements.txt`
   
## Execution of the scripts
Here we show how to execute each scenario with the concrete examples used throught the paper, so that you can reproduce the paper's results. 

Feature models are given in the Universal Variability Language (UVL) format.
The stakeholder's opinions are given in a .csv file to the following format:
```
Element, StakeholderOpinion1, StakeholderOpinion2, StakeholderOpinion3, ..., FusionOperator
featureNameA, opinionA1, opinionA2, opinionA3, ..., eCBF
featureNameB, opinionB1, opinionB2, opinionB3, ... , ABF
...
```
where the column `Element` is the name of the feature to be considered. The following columns are the opinions for each stakeholder. Opinions are given as a SBoolean vector (e.g., `"(0.67, 0.00, 0.33, 0.50)"`), or as a degree of uncertainty (e.g., `PROBABLE`). The last column represents the fusion operator to use when fusing the opinions for the given feature (e.g., `ABF`). The following fusion operators are available: `CBF, CCF, aCBF, eCBF, ABF, WBF, MinBF, MajBF`.

Moreover, the scripts are generic and can be executed with any other feature model and stakeholder's opinions.
For each script, we describe its syntaxis, inputs, outputs, and an example of execution.

- **Scenario 1: Feature model evolution.** It takes the stakeholder's opinions about features to be included or removed in the planned feature model of the SPL, and return the fused opinions of the stakeholder for each feature along with its projection and the decision to be made according to a given threshold.
  
  - Execution: `python scenario1.py -o OPINIONS [-s] [-t THRESHOLD]`
  - Inputs: 
    - The `OPINIONS` of the stakeholders is a .csv file containing their opinions for each feature to be considered.
    - Optionally, the `-s` parameter specifies whether the degrees of uncertainty for the stakelholder's opinions in the .csv file should be considered as strong opinions or as moderate opinions. If ommited, moderate opinions are considered.
    - The `-t` parameter specifies the threshold (0.0 <= t <= 1.0) to consider in the decisions. If the resulting projection of the fused opionions of a features is greater than the threshold, the feature will be added/removed from the planned feature model. Default 0.5.
  - Outputs:
    - A list of fused opinions, its projection, and the decisions for each feature in the .csv file.
  - Example: `python scenario1.py -o opinions/scenario1_EVO_miband2.csv -t 0.75`

- **Scenario 2: Next release problem.** It takes a feature model and the stakeholder's opinions about features to be implemented for the next release, and returns fused opinions for each feature taking into account the related/dependent features. The script groups the features according to its dependencies. First, it shows the feature with cross-tree constraints, then the group of related feature in the tree, and then the indendepent features. Finally, it shows a ranking of the features priorization to be implemented according to the opinions.
  
  - Execution: `python scenario2.py -fm FEATURE_MODEL -o OPINIONS [-s]`
  - Inputs: 
    - The `FEATURE_MODEL` parameter specifies the file path of the feature model in UVL format.
    - The `OPINIONS` of the stakeholders is a .csv file containing their opinions for each feature to be considered.
    - Optionally, the `-s` parameter specifies whether the degrees of uncertainty for the stakelholder's opinions in the .csv file should be considered as strong opinions or as moderate opinions. If ommited, moderate opinions are considered.
  - Outputs:
    - Fusion opinions for each features classified in features with cross-tree constraints, group of related features in a tree, and independent features. Also, a ranking of features is shown.
  - Example: `python scenario2.py -fm xiaomi-spl/models/miband2_planned.uvl -o opinions/scenario2_NRP_miband2.csv`

- **Scenario 3: Variability reduction.** It takes a feature model and the stakeholder's opinions about features already implemented, generate a sample of products of a given size and determine those products that should be realized in the following release of the SPL according to the fused opinions of the stakeholders. The scripts shows a list of products ordered by the fused opinions of the stakeholders. For each product, the script combines the opinions from a stakeholder of each feature present in the product, and then fuse all combined stakeholder's opinions.
  
  - Execution: `python scenario3.py -fm FEATURE_MODEL -o OPINIONS [-n N_PRODUCTS] [-f FUSION_OPERATOR] [-s]`
  - Inputs: 
    - The `FEATURE_MODEL` parameter specifies the file path of the feature model in UVL format.
    - The `OPINIONS` of the stakeholders is a .csv file containing their opinions for each feature to be considered.
    - The `N_PRODUCTS` parameter specifies the number of products to be generated from the feature model. Default all.
    - The `FUSION_OPERATOR` parameter specifies the fusion operator to be used for fusing the stakeholder's opinions about each product. Default `ABF`. 
    - Optionally, the `-s` parameter specifies whether the degrees of uncertainty for the stakelholder's opinions in the .csv file should be considered as strong opinions or as moderate opinions. If ommited, moderate opinions are considered.
  - Outputs:
    - Ordered list of products with the fused opinions and its projection for each product.
  - Example: `python scenario3.py -fm xiaomi-spl/models/miband2_realized.uvl -o opinions/scenario3_VR_miband2.csv`

