import pickle
import yaml
import os
import os.path as osp

from typing import Tuple

import numpy as np
import optuna
import pandas as pd
import typer

from autopeptideml.train import (OptunaTrainer, evaluate)
from autopeptideml.utils import format_numbers

REGRESSION_TASKS = ['binding']
CLASSIFICATION_TASKS = ['cpp', 'antibacterial', 'antiviral']
TASKS = REGRESSION_TASKS + CLASSIFICATION_TASKS


def define_hpspace(model: str, pred_task: str) -> Tuple[dict, dict]:
    cwd = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(cwd, 'h_param_search',
                        f'{model}_{pred_task}.yml')

    config = yaml.load(open(path), yaml.Loader)
    config = format_numbers(config)
    hpspace = {
        'models': {
            'type': 'fixed',
            'elements': {
                model: config
            },
        },
        'representations': ['default']
    }
    optim_strategy = {'task': pred_task, 'direction': 'maximize',
                      'metric': 'mcc' if pred_task == 'class' else 'spcc',
                      'patience': 20, 'n_steps': 100, 'n_jobs': 10}
    return hpspace, optim_strategy


def hpo(pred_task: str, model_name: str, train_x: np.ndarray,
        train_y: np.ndarray, seed: int) -> dict:
    hpspace, optim_strategy = define_hpspace(model_name, pred_task)
    trainer = OptunaTrainer(task=pred_task)
    trainer.hpo(
        x={'default': train_x},
        y=train_y,
        models=[model_name],
        n_folds=5,
        n_trials=100,
        n_jobs=10,
        random_state=seed,
        verbose=3,
        custom_hpspace=hpspace
    )
    return trainer.best_model


def experiment(dataset: str, model: str, representation: str,
               train_set: str, df_c: pd.DataFrame, df_nc: pd.DataFrame,
               seed: int = 1):
    np.random.seed(seed)

    if dataset in REGRESSION_TASKS:
        pred_task = 'reg'
    elif dataset in CLASSIFICATION_TASKS:
        pred_task = 'class'
    else:
        raise ValueError(
            f"Dataset: {dataset} not in tasks: {', '.join(TASKS)}")

    x_type = {}
    for s in ['c', 'nc']:
        x_type[s] = []
        for idx, rep in enumerate(representation.split(',')):
            t_x = pickle.load(open(osp.join(osp.dirname(__file__),
                                          '..', 'reps', f'{rep}_{s}-{dataset}.pickle'), 'rb'))
            t_x = np.array(t_x)
            if idx == 0:
                x = t_x
            else:
                x = np.concatenate([x, t_x], axis=1)

        x_type[s] = x

    if dataset == 'binding':
        x_type['c'] = np.concatenate([x_type['c'], np.stack(pickle.load(
            open(osp.join(osp.dirname(__file__), '..', 'reps', 'binding-c-targets.pickle'), 'rb')
        ))], axis=1)
        x_type['nc'] = np.concatenate([x_type['nc'], np.stack(pickle.load(
            open(osp.join(osp.dirname(__file__), '..', 'reps', 'binding-nc-targets.pickle'), 'rb')
        ))], axis=1)

    y_c = df_c.labels.to_numpy()
    y_nc = df_nc.labels.to_numpy()
    c_train_x, c_train_y = x_type['c'], y_c
    nc_train_x, nc_train_y = x_type['nc'], y_nc

    if train_set == 'standard':
        train_x, train_y = c_train_x, c_train_y
        test_x, test_y = nc_train_x, nc_train_y
    elif train_set == 'modified':
        train_x, train_y = nc_train_x, nc_train_y
        test_x, test_y = c_train_x, c_train_y
    else:
        print(f"Type does not exist: {train_set}")

    best_model = hpo(pred_task, model, train_x, train_y, seed)

    results = []
    for idx, model in enumerate(best_model.models):
        if pred_task == 'class':
            preds = model.predict_proba(test_x)
            preds = preds[:, 1]
        else:
            preds = model.predict(test_x)
        result = evaluate(preds, test_y, pred_task=pred_task)
        result['seed'] = seed + idx
        results.append(result)

    result_df = pd.DataFrame(results)
    return result_df


def main(dataset: str, model: str, representation: str,
         train_set: str = 'standard', n_seeds: int = 25):

    data_path = os.path.join(
        os.path.dirname(__file__), '..', 'downstream_data'
    )
    df_c = pd.read_csv(osp.join(data_path, f'c-{dataset}.csv'))
    df_nc = pd.read_csv(osp.join(data_path, f'nc-{dataset}.csv'))
    df_c['name'] = dataset
    df_nc['name'] = dataset

    optuna.logging.set_verbosity(optuna.logging.CRITICAL)
    results_dir = os.path.join(
        os.path.dirname(__file__), '..',
        'Results', train_set
    )
    results_path = os.path.join(
        results_dir,
        f'{dataset}_{model}_{representation}.csv'
    )
    os.makedirs(results_dir, exist_ok=True)

    results_df = pd.DataFrame()
    for i in range(n_seeds):
        print("SEED:", i)
        result_df = experiment(
            dataset, model, representation,
            train_set, df_c, df_nc, i
        )
        results_df = pd.concat([results_df, result_df])
    results_df.to_csv(results_path, index=False)
    print(results_df.head())

if __name__ == '__main__':
    typer.run(main)
