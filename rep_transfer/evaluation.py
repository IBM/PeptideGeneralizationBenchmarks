import json
# import math
import operator
import os
from typing import Callable, Dict

import lightgbm
import numpy as np
import optuna
import pandas as pd
import sklearn.ensemble as ensemble
import sklearn.gaussian_process as gauss
import sklearn.neighbors as knn
import sklearn.svm as svm
import typer
import xgboost
import yaml
import warnings

from hestia import HestiaGenerator, SimArguments
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import (matthews_corrcoef, root_mean_squared_error,
                             accuracy_score, f1_score,
                             precision_score, recall_score, mean_squared_error,
                             mean_absolute_error)
# from represent_peptides import calculate_molformer
from tqdm import tqdm
# from autopeptideml.reps.lms import RepEngineLM


def calculate_chemberta(dataset: str):
    import torch
    import transformers as hf
    device = 'mps'
    batch_size = 32
    out_path = os.path.join(os.path.dirname(__file__),
        '..', 'reps', f'chemberta_{dataset}.json')
    if os.path.exists(out_path):
        return np.array(json.load(open(out_path)))
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    tokenizer = hf.AutoTokenizer.from_pretrained(
        'DeepChem/ChemBERTa-77M-MLM', trust_remote_code=True
    )
    model = hf.AutoModel.from_pretrained('DeepChem/ChemBERTa-77M-MLM',
                                         trust_remote_code=True)
    model.to(device)
    n_params = sum(p.numel() for p in model.parameters())
    if n_params / 1e6 < 1e3:
        print(f'Number of model parameters are: {n_params/1e6:.1f} M')
    else:
        print(f'Number of model parameters are: {n_params/1e9:.1f} B')
    smiles = df['SMILES'].tolist()
    batched = [smiles[i:i+batch_size] for i in
               range(0, len(smiles), batch_size)]
    fps = []
    for batch in tqdm(batched):
        input_ids = tokenizer(batch, return_tensors='pt',
                              padding='longest', truncation=True).to(device)
        with torch.no_grad():
            vector = model(**input_ids).last_hidden_state
            mask = input_ids['attention_mask']
            for i in range(mask.shape[0]):
                length = mask[i].sum()
                fps.append(vector[i, :length].mean(0).detach().cpu().tolist())

    json.dump(fps, open(os.path.join(out_path), 'w'))
    return np.array(fps)


def calculate_molformer(dataset: str):
    import torch
    import transformers as hf
    device = 'mps'
    batch_size = 32
    out_path = os.path.join(os.path.dirname(__file__),
        '..', 'reps', f'molformer_{dataset}.json')
    if os.path.exists(out_path):
        return np.array(json.load(open(out_path)))
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    tokenizer = hf.AutoTokenizer.from_pretrained(
        'ibm/MoLFormer-XL-both-10pct', trust_remote_code=True
    )
    model = hf.AutoModel.from_pretrained('ibm/MoLFormer-XL-both-10pct',
                                         trust_remote_code=True)
    model.to(device)
    n_params = sum(p.numel() for p in model.parameters())
    if n_params / 1e6 < 1e3:
        print(f'Number of model parameters are: {n_params/1e6:.1f} M')
    else:
        print(f'Number of model parameters are: {n_params/1e9:.1f} B')
    smiles = df['SMILES'].tolist()
    batched = [smiles[i:i+batch_size] for i in
               range(0, len(smiles), batch_size)]
    fps = []
    for batch in tqdm(batched):
        input_ids = tokenizer(batch, return_tensors='pt',
                              padding='longest').to(device)
        with torch.no_grad():
            vector = model(**input_ids).last_hidden_state
            mask = input_ids['attention_mask']
            for i in range(mask.shape[0]):
                length = mask[i].sum()
                fps.append(vector[i, :length].mean(0).detach().cpu().tolist())
    json.dump(fps, open(os.path.join(out_path), 'w'))
    return np.array(fps)


def _pcc(preds, truths):
    return pearsonr(preds, truths)[0]


def _spcc(preds, truths):
    return spearmanr(preds, truths)[0]


def _f1_weighted(preds, truths):
    return f1_score(preds, truths, average='weighted')


def _recall(preds, truths):
    return recall_score(preds, truths, zero_division=True)


CLASSIFICATION_METRICS = {
    'mcc': matthews_corrcoef,
    'acc': accuracy_score,
    'f1': f1_score,
    'f1_weighted': _f1_weighted,
    'precision': precision_score,
    'recall': _recall
}

REGRESSION_METRICS = {
    'rmse': root_mean_squared_error,
    'mse': mean_squared_error,
    'mae': mean_absolute_error,
    'pcc': _pcc,
    'spcc': _spcc
}

CLASSIFICATION_MODELS = {
    'svm': svm.SVC,
    'knn': knn.KNeighborsClassifier,
    'gauss': gauss.GaussianProcessClassifier,
    'rf': ensemble.RandomForestClassifier,
    'xgboost': xgboost.XGBClassifier,
    'lightgbm': lightgbm.LGBMClassifier
}

REGRESSION_MODELS = {
    'svm': svm.SVR,
    'knn': knn.KNeighborsRegressor,
    'gauss': gauss.GaussianProcessRegressor,
    'rf': ensemble.RandomForestRegressor,
    'xgboost': xgboost.XGBRegressor,
    'lightgbm': lightgbm.LGBMRegressor
}


REGRESSION_TASKS = ['c-binding', 'nc-binding']
CLASSIFICATION_TASKS = ['nc-cpp', 'c-cpp', 'c-sol', 'nc-antibacterial',
                        'c-antibacterial','c-antiviral', 'nc-antiviral']
TASKS = CLASSIFICATION_TASKS + REGRESSION_TASKS


class EarlyStoppingCallback(object):
    """Early stopping callback for Optuna."""
    def __init__(self, early_stopping_rounds: int,
                 direction: str = "minimize") -> None:
        self.early_stopping_rounds = early_stopping_rounds

        self._iter = 0

        if direction == "minimize":
            self._operator = operator.lt
            self._score = np.inf
        elif direction == "maximize":
            self._operator = operator.gt
            self._score = -np.inf
        else:
            ValueError(f"invalid direction: {direction}")

    def __call__(self, study: optuna.Study, trial: optuna.Trial) -> None:
        """Do early stopping."""
        if self._operator(study.best_value, self._score):
            self._iter = 0
            self._score = study.best_value
        else:
            self._iter += 1

        if self._iter >= self.early_stopping_rounds:
            study.stop()


def evaluate(preds, truth, pred_task) -> Dict[str, float]:
    result = {}
    if pred_task == 'reg':
        metrics = REGRESSION_METRICS
    else:
        metrics = CLASSIFICATION_METRICS

    for key, value in metrics.items():
        result[key] = value(preds, truth)
    return result


def define_hpspace(model: Callable, pred_task: str,
                   trial: optuna.Trial) -> dict:
    cwd = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(cwd, 'h_param_search',
                        f'{model}_{pred_task}.yml')
    hpspace = {}
    config = yaml.load(open(path), yaml.Loader)

    for key, item in config.items():
        if 'fixed' in item['type']:
            if item['type'].split('-')[1] == 'float':
                hpspace[key] = float(item['value'])
            elif item['type'].split('-')[1] == 'int':
                hpspace[key] = int(item['value'])
            else:
                hpspace[key] = item['value']
        elif item['type'] == 'bool':
            hpspace[key] = trial.suggest_categorical(
                key, choices=[True, False]
            )
        elif item['type'] == 'float':
            hpspace[key] = trial.suggest_float(
                key, low=float(item['min']),
                high=float(item['max']),
                log=bool(item['log'])
            )
        elif item['type'] == 'int':
            hpspace[key] = trial.suggest_int(
                key, low=int(item['min']),
                high=int(item['max']),
                log=bool(item['log'])
            )
        elif item['type'] == 'categorical':
            hpspace[key] = trial.suggest_categorical(
                key, choices=item['values']
            )
            if key == 'kernel':
                for name, value in item['extra_parameters'].items():
                    if name == hpspace[key]:
                        for subkey, subitem in value.items():
                            if subitem['type'] == 'fixed':
                                if subitem['type'].split('-')[1] == 'float':
                                    hpspace[subkey] = float(subitem['value'])
                                elif subitem['type'].split('-')[1] == 'int':
                                    hpspace[subkey] = int(subitem['value'])
                                else:
                                    hpspace[subkey] = subitem['value']
                            elif subitem['type'] == 'float':
                                hpspace[subkey] = trial.suggest_float(
                                    subkey, low=float(subitem['min']),
                                    high=float(subitem['max']),
                                    log=bool(subitem['log'])
                                )
                            elif subitem['type'] == 'int':
                                hpspace[subkey] = trial.suggest_int(
                                    subkey, low=int(subitem['min']),
                                    high=int(subitem['max']),
                                    log=bool(subitem['log'])
                                )
                            elif subitem['type'] == 'categorical':
                                hpspace[subkey] = trial.suggest_categorical(
                                    subkey, choices=subitem['values']
                                )
                            else:
                                raise ValueError("Subitem type: " +
                                                 f"{subitem['type']} " +
                                                 "does not exit.")

        else:
            raise ValueError(f"Item type: {item['type']} does not exit.")
    return hpspace


def hpo(pred_task: str, learning_algorithm: Callable,
        model_name: str,
        study: optuna.Study, train_x: np.ndarray,
        train_y: np.ndarray, valid_x: np.ndarray,
        valid_y: np.ndarray, n_trials: int,
        seed: int) -> dict:
    global best_model
    if pred_task == 'class':
        best_model = {'result': {'mcc': float('-inf')}}
    else:
        best_model = {'result': {'mse': float('inf')}}

    def hpo_objective(trial: optuna.Trial) -> float:
        global best_model
        hpspace = define_hpspace(model_name, pred_task,
                                 trial)
        if (not (model_name == 'svm' and pred_task == 'reg') and
           model_name != 'knn'):
            hpspace['random_state'] = seed
        model = learning_algorithm(**hpspace)
        model.fit(train_x, train_y)
        preds = model.predict(valid_x)
        result = evaluate(preds, valid_y, pred_task)
        if pred_task == 'class':
            if result['mcc'] > best_model['result']['mcc']:
                best_model = {
                    'model': model,
                    'config': hpspace,
                    'result': result
                }
            return result['mcc']
        else:
            if result['mse'] < best_model['result']['mse']:
                best_model = {
                    'model': model,
                    'config': hpspace,
                    'result': result
                }
            return -result['mse']
    study.optimize(hpo_objective, n_trials,
                   callbacks=[EarlyStoppingCallback(20, direction='maximize')],
                   show_progress_bar=True, gc_after_trial=False, n_jobs=10)
    return best_model


def define_hestia_generator(
    dataset: str,
    df: pd.DataFrame,
    similarity_metric: str,
    fp: str,
    radius: int
) -> HestiaGenerator:
    if 'peptides' in similarity_metric or 'mmseqs' in similarity_metric or 'needle' in similarity_metric:
        if 'sequence' not in df.columns:
            df['sequence'] = df['BILN'].map(lambda x: ''.join(x.split('-')))
        sim_args = SimArguments(
            data_type='sequence', alignment_algorithm=similarity_metric.replace('+prefilter', ''),
            field_name='sequence', denominator='longest', verbose=3,
            prefilter='+prefilter' in similarity_metric
        )
        print(sim_args)
    elif 'molformer' in similarity_metric:
        sim_args = SimArguments(
            data_type='embedding', sim_function='euclidean',
            query_embds=calculate_molformer(df.name.unique().item()),
            verbose=3
        )
    elif 'esm' in similarity_metric or 'prot' in similarity_metric:
        re = RepEngineLM(similarity_metric)
        re.move_to_device('mps')
        sim_args = SimArguments(
            data_type='embedding', sim_function='euclidean',
            query_embds=np.array(re.compute_reps(df.sequence.tolist(),
                                                 batch_size=32)),
            verbose=3
        )  
    elif 'chemberta' in similarity_metric:
        sim_args = SimArguments(
            data_type='embedding', sim_function='euclidean',
            query_embds=calculate_chemberta(df.name.unique().item()),
            verbose=3
        )
    elif 'mordred' in similarity_metric:
        from mordred import Calculator, descriptors
        from rdkit import Chem

        m_calc = Calculator(descriptors, ignore_3D=True)
        def calc(smiles: str) -> np.ndarray:
            mol = Chem.MolFromSmiles(smiles)
            return [i for i in m_calc(mol)]

        sim_args = SimArguments(
            data_type='embedding', sim_function='euclidean',
            verbose=3, query_embds=np.array([calc(a) for a in tqdm(df.SMILES)])

        )
    elif 'lipinski' in similarity_metric:
        sim_args = SimArguments(
            data_type='small molecules', sim_function='canberra',
            fingerprint='lipinski', field_name='SMILES', verbose=3
        )
    else:
        sim_args = SimArguments(
            data_type='small molecule', fingerprint=fp,
            field_name='SMILES', min_threshold=0.,
            threads=8, bits=2_048, radius=radius,
            sim_function=similarity_metric, verbose=3
        )
    hdg = HestiaGenerator(df)
    hdg.calculate_partitions(
        label_name='labels' if dataset not in REGRESSION_TASKS else None,
        min_threshold=0., sim_args=sim_args, threshold_step=0.1
        )
    return hdg


def experiment(dataset: str, model: str, representation: str,
               hdg: HestiaGenerator, df: pd.DataFrame,
               n_trials: int = 100, seed: int = 1):
    global best_model

    np.random.seed(seed)
    if dataset in REGRESSION_TASKS:
        pred_task = 'reg'
        learning_algorithm = REGRESSION_MODELS[model]
    elif dataset in CLASSIFICATION_TASKS:
        pred_task = 'class'
        learning_algorithm = CLASSIFICATION_MODELS[model]
    else:
        raise ValueError(
            f"Dataset: {dataset} not in tasks: {', '.join(TASKS)}")

    x = np.array(json.load(open(
        os.path.join('reps', f'{representation}_{dataset}.json'))))
    y = df.labels.to_numpy()
    results = []
    for th, partitions in hdg.get_partitions(filter=0.185):
        if th != 'random':
            if (th * 100) % 10 != 0:
                continue

        print("THRESHOLD:", th)

        train_idx = partitions['train']
        valid_idx = partitions['valid']
        test_idx = partitions['test']

        train_x, train_y = x[train_idx], y[train_idx]
        valid_x, valid_y = x[valid_idx], y[valid_idx]
        test_x, test_y = x[test_idx], y[test_idx]

        study = optuna.create_study(direction='maximize')
        best_model = hpo(pred_task, learning_algorithm, model, study,
                         train_x, train_y, valid_x, valid_y, n_trials,
                         seed)
        preds = best_model['model'].predict(test_x)
        result = evaluate(preds, test_y, pred_task)
        result.update({f"{key}_val": val for key, val in
                       best_model['result'].items()})
        result.update({'threshold': th, 'seed': seed})
        results.append(result)
    result_df = pd.DataFrame(results)
    return result_df


def main(dataset: str, model: str, representation: str,
         n_trials: int = 200, n_seeds: int = 5):

    part_dir = os.path.join(
        os.path.dirname(__file__), '..', 'partitions'
    )
    data_path = os.path.join(
        os.path.dirname(__file__), '..', 'downstream_data'
    )
    part_path = os.path.join(
        part_dir, f"{dataset}.gz"
    )
    os.makedirs(part_dir, exist_ok=True)

    df = pd.read_csv(os.path.join(data_path, f'{dataset}.csv'))
    df['name'] = dataset

    if os.path.exists(part_path):
        hdg = HestiaGenerator(df)
        hdg.from_precalculated(part_path)
    else:
        raise NotImplementedError("Please make sure you have downloaded the official partitions.")

    warnings.filterwarnings('ignore')
    optuna.logging.set_verbosity(optuna.logging.CRITICAL)
    results_dir = os.path.join(
        os.path.dirname(__file__), '..',
        'Results', 'no-generalisation',
    )
    results_path = os.path.join(
        results_dir,
        f"{dataset}_{model}_pre_0.0_post_0.0_{representation}.csv"
    )
    os.makedirs(results_dir, exist_ok=True)

    results_df = pd.DataFrame()
    for i in range(n_seeds):
        print("SEED:", i)
        result_df = experiment(
            dataset, model, representation, hdg, df,
            n_trials, i
        )
        results_df = pd.concat([results_df, result_df])
    results_df.to_csv(results_path, index=False)


if __name__ == '__main__':
    typer.run(main)
