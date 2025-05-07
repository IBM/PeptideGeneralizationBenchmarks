# Peptide Generalization Benchmarks

## 1. Introduction

This set of benchmarks is meant to evaluate the  ability of peptide representation methods and models to provide meaningful features of canonical and non-canonical peptides useful for machine learning. The main metric the benchmark measures is the ability of a representation technique to extrapolate from canonical peptides to non-canonical peptides, as this is the most common scenario in real-world pharmaceutical development.

Here, we define canonical peptides as those protein sequences with less than 50 amino acids and composed by the 20 standard amino acids; non-canonical peptides are defined as peptides with chemical modifications either in the back-bone, cyclizations, or modified or wholly synthetical side-chains.

If you want to learn more, please check out our [paper preprint](https://chemrxiv.org/engage/chemrxiv/article-details/67d2f3ae81d2151a023d64f8).

## 2. Datasets

The benchmark is currently integrated by four different prediction tasks:

1. Protein-peptide binding affinity (Regression)
2. Cell penetration (Classification)
3. Antibacterial activity (Classification)
4. Antiviral activity (Classification)

For each of these tasks there are two subsets of data: canonical (the file starts with `c-`) and non-canonical (file starts with `nc-`). We are continuously looking to improve the benchmarks and make them more comprehensive so we welcome any suggestions for tasks or datasets that may be relevant for 1) drug development or 2) bio-catalyst optimization. If you have a suggestion, please open an [issue](https://github.com/IBM/PeptideGeneralizationBenchmarks/issues) or contact us at [raul.fernandezdiaz@ucdconnect.ie](mailto:raul.fernandezdiaz@ucdconnect.ie)

## 3. Running the benchmarks

You will need to clone the repo.

```bash
git clone https://github.com/IBM/PeptideGeneralizationBenchmarks
cd PeptideGeneralizationBenchmarks
```

### 3.1 Prepare peptide representations

Then you will need to adapt the `rep_transfer/represent_peptides.py` file to account for your peptide representation/featurization method/model. The output should be a matrix with $`N \times E`$ with $`N`$ being the number of peptides in each dataset and $`E`$ the dimensions of the embedding space. The order of the peptide representations should be the same as in the `downstream_data/` datasets. It is run by:

```bash
python rep_transfer/represent_peptides $dataset $name_of_your_representation
```

### 3.2 Run the benchmarks

The first two benchmarks (canonical and non-canonical representation) can be easily run by:

```bash
python rep_transfer/evaluation.py $dataset lightgbm $name_of_your_representation
```

Here the datasets are the names of the files in `downstream_data/`, so you should run 8 different calculations. The script will automatically run all thresholds and the 5 different seeds. Please do not change anything in the configuration or the HPO configuration to ensure fair comparison between methods.

To run the canonical to non-canonical extrapolation execute:

```bash
python rep_transfer/evaluation_joint.py $dataset lightgbm $name_of_your_representation canonical
```

Here the datasets are as follows: `antibacterial`, `antiviral`, `binding`, and `cpp`. Basically, the files in `downstream_data/` without the starting `c-` or `nc-`.


## 3.3 Statistical analysis of the results

The statistical analysis of the results can be easily performed by running the `analysis/results_analysis.ipynb` notebook.


## 4. Submission and scoring

All datasets have been partitioned using the Hestia-GOOD framework (more information in the [Hestia-GOOD paper](https://openreview.net/pdf?id=qFZnAC4GHR) or [Github Repository](https://github.com/IBM/Hestia-GOOD)). The final model score for each dataset is the average across all thresholds and 5 independent runs. Error measurements are provided as standard error of the mean across thresholds and independent runs. The significant rank is defined through the statistical analysis of the significant differences between models with Kruskal-Wallis and *post-hoc* Wilcoxon test with Bonferroni correction for multiple testing.

The performance is measured as Spearman's $\rho$ correlation coefficient for the regression tasks and as Matthew's Correlation coefficient for binary classification tasks. 

Currently, we support only one category of evaluation, representation transfer, where a featurization method or representation learning model encodes each peptide into a single vector that then is used to train a machine learning model (LightGBM) to predict the associated label.

Submissions can be made through a dedicated issue (Issue type: Submission), we expect a zip file with the `Results/` directory generated from running the `rep_transfer/evaluation.py` and `rep_transfer/evaluation_joint.py`.

If you have any doubts as to how to run the scripts, please do not hesitate to open an [issue](https://github.com/IBM/PeptideGeneralizationBenchmarks/issues) or contact us at [raul.fernandezdiaz@ucdconnect.ie](mailto:raul.fernandezdiaz@ucdconnect.ie).

## 5. Leaderboards

### 5.1. Representation of canonical peptides

The first subtask only concerns the files with canonical peptides. 

| Representation      | Antiviral (canonical)   | Protein-peptide binding affinity (canonical)   | Cell penetration (canonical)   | Antibacterial (canonical)   | Average     | Significant rank   |
|:--------------------|:------------------------|:-----------------------------------------------|:-------------------------------|:----------------------------|:------------|:-------------------|
| ESM2 8M             | 0.78 ± 0.01             | 0.90 ± 0.01                                    | 0.91 ± 0.01                    | 0.81 ± 0.02                 | 0.85 ± 0.01 | **--1--**          |
| ECFP-16 with counts | 0.75 ± 0.01             | 0.91 ± 0.01                                    | 0.94 ± 0.01                    | 0.79 ± 0.02                 | 0.84 ± 0.01 | **--1--**          |
| Prot-T5-XL          | 0.77 ± 0.01             | 0.90 ± 0.00                                    | 0.91 ± 0.01                    | 0.81 ± 0.02                 | 0.84 ± 0.01 | **--1--**          |
| ESM2 150M           | 0.76 ± 0.01             | 0.88 ± 0.01                                    | 0.91 ± 0.01                    | 0.81 ± 0.02                 | 0.83 ± 0.01 | 2                  |
| ECFP-16             | 0.74 ± 0.01             | 0.90 ± 0.01                                    | 0.92 ± 0.01                    | 0.77 ± 0.02                 | 0.83 ± 0.01 | 2                  |
| ChemBERTa-2         | 0.73 ± 0.01             | 0.89 ± 0.01                                    | 0.90 ± 0.01                    | 0.80 ± 0.02                 | 0.82 ± 0.01 | 2                  |
| PeptideCLM          | 0.71 ± 0.01             | 0.86 ± 0.00                                    | 0.90 ± 0.01                    | 0.79 ± 0.02                 | 0.81 ± 0.01 | 3                  |
| Pepland             | 0.70 ± 0.01             | 0.89 ± 0.01                                    | 0.88 ± 0.01                    | 0.78 ± 0.02                 | 0.81 ± 0.01 | 3                  |
| Molformer-XL        | 0.68 ± 0.02             | 0.88 ± 0.01                                    | 0.91 ± 0.01                    | 0.77 ± 0.02                 | 0.80 ± 0.01 | 4                  |
| PepFuNN             | 0.73 ± 0.01             | 0.76 ± 0.01                                    | 0.89 ± 0.01                    | 0.68 ± 0.02                 | 0.76 ± 0.01 | 5                  |

## 5.2. Representation of non-canonical peptides

The second subtask only concerns non-canonical peptides. Kruskal-Wallis $p=3\times10^{-7} $

| Representation      | Antiviral (non-canonical)   | Antibacterial (non-canonical)   | Protein-peptide binding affinity (non-canonical)   | Cell penetration (non-canonical)   | Average     | Significant rank   |
|:--------------------|:----------------------------|:--------------------------------|:---------------------------------------------------|:-----------------------------------|:------------|:-------------------|
| Molformer-XL        | 0.91 ± 0.01                 | 0.88 ± 0.01                     | 0.85 ± 0.02                                        | 0.89 ± 0.01                        | 0.88 ± 0.01 | **--1--**          |
| ChemBERTa-2         | 0.91 ± 0.01                 | 0.87 ± 0.00                     | 0.88 ± 0.01                                        | 0.84 ± 0.02                        | 0.88 ± 0.01 | **--1--**          |
| ECFP-16             | 0.87 ± 0.01                 | 0.90 ± 0.01                     | 0.87 ± 0.01                                        | 0.71 ± 0.02                        | 0.84 ± 0.01 | **--1--**          |
| PeptideCLM          | 0.83 ± 0.02                 | 0.88 ± 0.00                     | 0.85 ± 0.01                                        | 0.78 ± 0.01                        | 0.83 ± 0.01 | 2                  |
| ECFP-16 with counts | 0.87 ± 0.01                 | 0.89 ± 0.01                     | 0.86 ± 0.02                                        | 0.65 ± 0.04                        | 0.82 ± 0.01 | 3                  |
| Pepland             | 0.78 ± 0.01                 | 0.85 ± 0.01                     | 0.83 ± 0.01                                        | 0.62 ± 0.02                        | 0.77 ± 0.01 | 3                  |
| PepFuNN             | 0.74 ± 0.02                 | 0.88 ± 0.01                     | 0.73 ± 0.02                                        | 0.44 ± 0.01                        | 0.70 ± 0.02 | 4                  |


## 5.3. Generalisation from canonical to non-canonical

The last subtask measures how well models trained with each of the representations can generalise/extrapolate from a canonical training set to a non-canonical test set.

| Representation      | Protein-peptide binding affinity   | Antiviral   | Antibacterial   | Cell penetration   | Average     | Significant rank   |
|:--------------------|:-----------------------------------|:------------|:----------------|:-------------------|:------------|:-------------------|
| ChemBERTa-2         | 0.15 ± 0.01                        | 0.38 ± 0.02 | 0.27 ± 0.01     | 0.07 ± 0.01        | 0.22 ± 0.01 | **--1--**          |
| ECFP-16             | 0.05 ± 0.01                        | 0.35 ± 0.02 | 0.32 ± 0.01     | 0.10 ± 0.02        | 0.20 ± 0.01 | 2                  |
| PeptideCLM          | 0.32 ± 0.01                        | 0.16 ± 0.01 | 0.23 ± 0.01     | -0.06 ± 0.02       | 0.16 ± 0.01 | 3                  |
| ECFP-16 with counts | 0.06 ± 0.01                        | 0.27 ± 0.02 | 0.32 ± 0.01     | -0.02 ± 0.01       | 0.15 ± 0.01 | 4                  |
| PepFuNN             | -0.17 ± 0.02                       | 0.29 ± 0.01 | 0.38 ± 0.01     | 0.01 ± 0.02        | 0.11 ± 0.02 | 5                  |
| Molformer-XL        | 0.14 ± 0.01                        | 0.11 ± 0.01 | 0.39 ± 0.01     | -0.15 ± 0.02       | 0.11 ± 0.02 | 6                  |
| Pepland             | 0.05 ± 0.01                        | 0.15 ± 0.02 | -0.04 ± 0.01    | 0.20 ± 0.02        | 0.10 ± 0.01 | 7                  |
