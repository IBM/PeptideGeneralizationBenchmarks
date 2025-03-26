# Peptide Generalization Benchmarks

## 1. Introduction

This set of benchmarks are meant to evaluate the  ability of peptide representation methods and models to provide meaningful features of canonical and non-canonical peptides useful for machine learning. The main metric the benchmark measures is the ability of a representation technique to extrapolate from canonical peptides to non-canonical peptides, as this is the most common scenario in real-world pharmaceutical development.

Here, we define canonical peptides as those protein sequences with less than 50 amino acids and composed by the 20 standard amino acids; non-canonical peptides are defined as peptides with chemical modifications either in the back-bone, cyclizations, or modified or wholly synthetical side-chains.


## 2. Datasets

The benchmark is currently integrated by four different prediction tasks:

1. Protein-peptide binding affinity (Regression)
2. Cell penetration (Classification)
3. Antibacterial activity (Classification)
4. Antiviral activity (Classification)

For each of these tasks there are two subsets of data (canonical), the file starts with `c-` and non-canonical, file starts with `nc-`. We are continuously looking to improve the benchmarks and make them more comprehensive so we welcome any suggestions for tasks or datasets that may be relevant for 1) drug development or 2) bio-catalyst optimization. If you have a suggestion, please open an [issue](https://github.com/IBM/PeptideGeneralizationBenchmarks/issues) or contact us at [raul.fernandezdiaz@ucdconnect.ie](mailto:raul.fernandezdiaz@ucdconnect.ie)

## 3. Submission and scoring

All datasets have been partitioned using the Hestia-GOOD framework (more information in the [Hestia-GOOD paper](https://openreview.net/pdf?id=qFZnAC4GHR) or [Github Repository](https://github.com/IBM/Hestia-GOOD)). The final model score for each dataset is the average across all thresholds and 5 independent runs. Error measurements are provided as standard error of the mean across thresholds and independent runs. The significant rank is defined through the statistical analysis of the significant differences between models with Kruskal-Wallis and *post-hoc* Wilcoxon test with Bonferroni correction for multiple testing.

The performance is measured as Spearman's $\rho$ correlation coefficient for the regression tasks and as Matthew's Correlation coefficient for binary classification tasks. 

Currently, we support only one category of evaluation, which representation transfer, where a featurization method or representation learning model encodes each peptide into a single vector that then is used to train a machine learning model (LightGBM) to predict the associated label.

We will only accept submissions of the files with the peptide representations. We will then run the training pipeline to ensure the fair comparison between models. We release the test partitions for all datasets to facilitate users developing and checking their own methods. We aim to update the leaderboard within a week of submission. We will only update the leaderboard with methods that have provided a minimum documentation of the workflow/model/technique used.

## 4. Leaderboards

### 4.1. Representation of canonical peptides

The first subtask only concerns the files with canonical peptides.

| Representation   | Protein-peptide binding affinity   | Cell penetration   | Antibacterial   | Antiviral   | Average   | Significant rank |
|:-----------------|:-----------------------------------|:-------------------|:----------------|:------------|:----------| --- | 
| ESM2 8M          | 0.9±0.007                          | 0.91±0.009         | 0.81±0.02       | 0.78±0.01   | 0.85±0.01 | **-1-** |
| Prot-T5-XL       | 0.9±0.005                          | 0.91±0.009         | 0.81±0.02       | 0.77±0.01   | 0.85±0.01 | **-1-** |
| ESM2 150M        | 0.88±0.007                         | 0.91±0.008         | 0.81±0.02       | 0.76±0.01   | 0.84±0.01 | **-1-** |
| ChemBERTa-2      | 0.89±0.006                         | 0.9±0.01           | 0.8±0.02        | 0.73±0.01   | 0.83±0.01 | 2 |
| ECFP-16          | 0.9±0.006                          | 0.92±0.01          | 0.77±0.02       | 0.74±0.01   | 0.83±0.01 | 2 |
| PeptideCLM       | 0.86±0.005                         | 0.9±0.01           | 0.79±0.02       | 0.71±0.01   | 0.81±0.01 | 3 |
| Pepland          | 0.89±0.008                         | 0.88±0.01          | 0.78±0.02       | 0.7±0.01    | 0.81±0.01 | 3 |
| Molformer-XL     | 0.88±0.008                         | 0.91±0.01          | 0.77±0.02       | 0.68±0.02   | 0.81±0.01 | 3 |
| PepFuNN          | 0.76±0.01                          | 0.89±0.01          | 0.68±0.02       | 0.73±0.01   | 0.77±0.01 | 4 |


## 4.2. Representation of non-canonical peptides

The second subtask only concerns non-canonical peptides.

| Representation   | Protein-peptide binding affinity   | Cell penetration   | Antibacterial   | Antiviral   | Average   | Significant rank |
|:-----------------|:-----------------------------------|:-------------------|:----------------|:------------|:----------| --- |
| Molformer-XL     | 0.85±0.02                          | 0.89±0.01          | 0.88±0.006      | 0.91±0.01   | 0.88±0.01 | **-1-** |
| ChemBERTa-2      | 0.88±0.01                          | 0.84±0.02          | 0.87±0.005      | 0.91±0.01   | 0.87±0.01 |  **-1-** |
| ECFP-16          | 0.87±0.01                          | 0.71±0.02          | 0.9±0.006       | 0.87±0.01   | 0.84±0.01 | 2 |
| PeptideCLM       | 0.85±0.01                          | 0.78±0.01          | 0.88±0.005      | 0.83±0.02   | 0.83±0.01 | 2 |
| Pepland          | 0.83±0.01                          | 0.62±0.02          | 0.85±0.01       | 0.78±0.01   | 0.77±0.01 | 3 |
| PepFuNN          | 0.73±0.02                          | 0.62±0.01          | 0.88±0.006      | 0.74±0.02   | 0.74±0.01 | 4 |


## 4.3. Generalisation from canonical to non-canonical

The last subtask measures how well models trained with each of the representations can generalise/extrapolate from a canonical training set to a non-canonical test set.

| Representation   | Protein-peptide binding affinity   | Cell penetration   | Antibacterial   | Antiviral   | Average   |
|:-----------------|:-----------------------------------|:-------------------|:----------------|:------------|:----------|
| ChemBERTa-2      | 0.15±0.01                          | 0.073±0.01         | 0.27±0.006      | 0.38±0.02   | 0.22±0.01 | **-1-** |
| ECFP-16          | 0.055±0.01                         | 0.051±0.02         | 0.32±0.006      | 0.35±0.02   | 0.19±0.01 | **-1-** |
| PeptideCLM       | 0.32±0.01                          | 0.019±0.02         | 0.23±0.008      | 0.16±0.01   | 0.18±0.01 |  2 |
| Molformer-XL     | 0.14±0.008                         | -0.0057±0.02       | 0.39±0.008      | 0.11±0.01   | 0.16±0.01 | 2 |
| PepFuNN          | -0.17±0.02                         | -0.025±0.01        | 0.38±0.01       | 0.29±0.01   | 0.12±0.01 | 2 |
| Pepland          | 0.055±0.009                        | 0.16±0.02          | -0.035±0.007    | 0.15±0.02   | 0.08±0.01 | 3 |
