# Peptide Generalization Benchmarks

## 1. Introduction

This set of benchmarks is meant to evaluate the  ability of peptide representation methods and models to provide meaningful features of standard and modified peptides useful for machine learning. The main metric the benchmark measures is the ability of a representation technique to extrapolate from standard to modified peptides, as this is the most common scenario in real-world pharmaceutical development.

Here, we define standard peptides as those protein sequences with less than 50 amino acids and composed by the 20 canonical amino acids; modified peptides are defined as peptides with chemical modifications either in the back-bone, cyclizations, or any non-canonical side-chains.

If you want to learn more, please check out our [paper](https://link.springer.com/article/10.1186/s13321-025-01115-z). As this repository will continue to include the latest results, a static version of the repository at time of publication can be found [here](https://github.com/jcheminform/PeptideGeneralizationBenchmarks) or [here](https://github.com/IBM/PeptideGeneralizationBenchmarks/releases/tag/v.1.0.0).

## 2. Datasets

The benchmark is currently integrated by four different prediction tasks:

1. Protein-peptide binding affinity (Regression)
2. Cell penetration (Classification)
3. Antibacterial activity (Classification)
4. Antiviral activity (Classification)

For each of these tasks there are two subsets of data: standard (the file starts with `c-`) and modified (file starts with `nc-`). We are continuously looking to improve the benchmarks and make them more comprehensive so we welcome any suggestions for tasks or datasets that may be relevant for 1) drug development or 2) bio-catalyst optimization. If you have a suggestion, please open an [issue](https://github.com/IBM/PeptideGeneralizationBenchmarks/issues) or contact us at [raul.fernandezdiaz@ucdconnect.ie](mailto:raul.fernandezdiaz@ucdconnect.ie).

The representations can be downloaded from here: [PeptideGeneralizationBenchmarks - Representations](https://drive.google.com/file/d/1MySH5qBAHpAkHYqIAkkMS7rj8QJBZEBJ/view?usp=sharing).

## 3. Running the benchmarks

You will need to clone the repo.

```bash
git clone https://github.com/IBM/PeptideGeneralizationBenchmarks
cd PeptideGeneralizationBenchmarks
```

### 3.1 Prepare peptide representations

Then you will need to adapt the `rep_transfer/represent_peptides.py` file to account for your peptide representation/featurization method/model. The output should be a matrix with $`N \times E`$ with $`N`$ being the number of peptides in each dataset and $`E`$ the dimensions of the embedding space. 

### 3.2 Run all the benchmarks

To compute the representations and run all the benchmarks simply run:

```bash
./run_all.sh <name-of-representation> svm
./run_all.sh <name-of-representation> lightgbm
```

## 3.3 Statistical analysis of the results

The statistical analysis of the results can be easily performed by running the `analysis/results_analysis.ipynb` notebook.


## 4. Submission and scoring

All datasets have been partitioned using the Hestia-GOOD framework (more information in the [Hestia-GOOD paper](https://openreview.net/pdf?id=qFZnAC4GHR) or [Github Repository](https://github.com/IBM/Hestia-GOOD)). The final model score for each dataset is the average across all thresholds and 5 independent runs. Error measurements are provided as standard error of the mean across thresholds and independent runs. The significant rank is defined through the statistical analysis of the significant differences between models with Kruskal-Wallis and *post-hoc* Wilcoxon test with Bonferroni correction for multiple testing.

The performance is measured as Spearman's $\rho$ correlation coefficient for the regression tasks and as Matthew's Correlation coefficient for binary classification tasks. 

Currently, we support only one category of evaluation, representation transfer, where a featurization method or representation learning model encodes each peptide into a single vector that then is used to train a machine learning model (LightGBM) to predict the associated label.

Submissions can be made through a dedicated issue (Issue type: Submission), we expect a zip file with the `Results/` directory generated from running the `rep_transfer/evaluation.py` and `rep_transfer/evaluation_joint.py`.

If you have any doubts as to how to run the scripts, please do not hesitate to open an [issue](https://github.com/IBM/PeptideGeneralizationBenchmarks/issues) or contact us at [raul.fernandezdiaz@ucdconnect.ie](mailto:raul.fernandezdiaz@ucdconnect.ie).

## 5. Leaderboards
### 5.1. Interpolation standard to standard peptides

Results with

| Representation | Antibacterial   | Antiviral   | Cell penetration   | Protein-peptide binding affinity   | Average   |   Significant rank |
|:---------------|:----------------|:------------|:-------------------|:-----------------------------------|:----------|-------------------:|
| ESM2 8M        | 0.81±0.02       | 0.78±0.01   | 0.91±0.01          | 0.90±0.01                          | 0.85±0.01 |                  1 |
| ESM2 650M      | 0.81±0.02       | 0.76±0.01   | 0.92±0.01          | 0.91±0.00                          | 0.84±0.01 |                  1 |
| ECFP-16 counts | 0.79±0.02       | 0.75±0.01   | 0.94±0.01          | 0.91±0.01                          | 0.84±0.01 |                  1 |
| Prot-T5-XL     | 0.81±0.02       | 0.77±0.01   | 0.91±0.01          | 0.90±0.00                          | 0.84±0.01 |                  1 |
| ESM2 150M      | 0.81±0.02       | 0.74±0.01   | 0.91±0.01          | 0.90±0.01                          | 0.83±0.01 |                  1 |
| ECFP-16        | 0.77±0.02       | 0.74±0.01   | 0.92±0.01          | 0.90±0.01                          | 0.83±0.01 |                  1 |
| ChemBERTa-2    | 0.80±0.02       | 0.73±0.01   | 0.90±0.01          | 0.89±0.01                          | 0.82±0.01 |                  1 |
| ProtBERT       | 0.79±0.02       | 0.71±0.01   | 0.91±0.01          | 0.92±0.01                          | 0.82±0.01 |                  1 |
| Pepland        | 0.78±0.02       | 0.70±0.01   | 0.88±0.01          | 0.89±0.01                          | 0.81±0.01 |                  2 |
| PeptideCLM     | 0.79±0.02       | 0.71±0.01   | 0.90±0.01          | 0.86±0.00                          | 0.81±0.01 |                  2 |
| Molformer-XL   | 0.77±0.02       | 0.68±0.02   | 0.91±0.01          | 0.88±0.01                          | 0.80±0.01 |                  2 |
| PepFuNN        | 0.68±0.02       | 0.73±0.01   | 0.89±0.01          | 0.76±0.01                          | 0.76±0.01 |                  3 |
| Avalon FP      | 0.68±0.02       | 0.73±0.01   | 0.85±0.02          | 0.62±0.01                          | 0.72±0.01 |                  4 |

### 5.2. Interpolation modified to modified peptides

Results with LightGBM.

|    Representation  | Antibacterial   | Antiviral   | Cell penetration   | Protein-peptide binding affinity   | Average   |   Significant rank |
|:---------------|:----------------|:------------|:-------------------|:-----------------------------------|:----------|-------------------:|
| Molformer-XL   | 0.88±0.01       | 0.91±0.01   | 0.89±0.01          | 0.85±0.02                          | 0.88±0.01 |                  1 |
| ChemBERTa-2    | 0.87±0.00       | 0.91±0.01   | 0.84±0.02          | 0.88±0.01                          | 0.88±0.01 |                  1 |
| Prot-T5-XL     | 0.87±0.01       | 0.84±0.02   | 0.93±0.01          | 0.84±0.02                          | 0.87±0.01 |                  1 |
| Avalon FP      | 0.83±0.01       | 0.90±0.01   | 0.72±0.01          | 0.90±0.01                          | 0.85±0.01 |                  2 |
| ProtBERT       | 0.85±0.01       | 0.87±0.02   | 0.87±0.01          | 0.81±0.02                          | 0.85±0.01 |                  2 |
| ECFP-16        | 0.90±0.01       | 0.87±0.01   | 0.71±0.01          | 0.87±0.01                          | 0.84±0.01 |                  2 |
| ESM2 650M      | 0.89±0.00       | 0.91±0.01   | 0.72±0.01          | 0.80±0.02                          | 0.83±0.01 |                  2 |
| PeptideCLM     | 0.88±0.00       | 0.83±0.02   | 0.78±0.01          | 0.85±0.01                          | 0.83±0.01 |                  2 |
| ECFP-16 counts | 0.89±0.01       | 0.87±0.01   | 0.65±0.04          | 0.86±0.02                          | 0.82±0.01 |                  2 |
| ESM2 150M      | 0.86±0.01       | 0.91±0.01   | 0.60±0.02          | 0.82±0.02                          | 0.80±0.01 |                  2 |
| ESM2 8M        | 0.78±0.01       | 0.89±0.02   | 0.68±0.02          | 0.82±0.02                          | 0.80±0.01 |                  3 |
| Pepland        | 0.85±0.01       | 0.78±0.01   | 0.62±0.02          | 0.83±0.01                          | 0.77±0.01 |                  3 |
| PepFuNN        | 0.88±0.01       | 0.74±0.02   | 0.44±0.01          | 0.73±0.02                          | 0.70±0.02 |                  4 |


## 5.3. Standard to modified extrapolation

The last subtask measures how well models trained with each of the representations can generalise/extrapolate from a standard training set to a modified test set.

|   Representation     | Antibacterial   | Antiviral   | Cell penetration   | Protein-peptide binding affinity   | Average   |   Significant rank |
|:---------------|:----------------|:------------|:-------------------|:-----------------------------------|:----------|-------------------:|
| PepFuNN        | 0.32±0.06       | 0.49±0.03   | -0.04±0.04         | 0.23±0.03                          | 0.25±0.04 |                  1 |
| ECFP-16        | 0.25±0.06       | 0.54±0.03   | -0.08±0.04         | 0.08±0.03                          | 0.19±0.04 |                  1 |
| ECFP-16 counts | 0.27±0.06       | 0.51±0.03   | -0.09±0.04         | 0.03±0.03                          | 0.18±0.04 |                  1 |
| ChemBERTa-2    | 0.02±0.06       | 0.14±0.03   | 0.03±0.04          | 0.37±0.03                          | 0.14±0.04 |                  1 |
| Prot-T5-XL     | 0.08±0.06       | 0.01±0.03   | 0.01±0.04          | 0.34±0.03                          | 0.11±0.04 |                  2 |
| ESM2 150M      | 0.08±0.06       | -0.00±0.03  | 0.02±0.04          | 0.31±0.03                          | 0.10±0.04 |                  2 |
| ESM2 650M      | -0.01±0.06      | 0.09±0.03   | 0.11±0.04          | 0.14±0.03                          | 0.08±0.04 |                  2 |
| ProtBERT       | 0.02±0.06       | 0.02±0.03   | 0.05±0.04          | 0.24±0.03                          | 0.08±0.04 |                  2 |
| Pepland        | 0.20±0.06       | -0.06±0.03  | 0.07±0.04          | 0.12±0.03                          | 0.08±0.04 |                  2 |
| ESM2 8M        | 0.08±0.06       | 0.01±0.03   | -0.03±0.04         | 0.21±0.03                          | 0.07±0.04 |                  2 |
| Molformer-XL   | 0.07±0.06       | 0.01±0.03   | 0.06±0.04          | 0.11±0.03                          | 0.06±0.04 |                  2 |
| PeptideCLM     | -0.01±0.06      | 0.03±0.03   | -0.14±0.04         | 0.26±0.03                          | 0.04±0.04 |                  2 |
