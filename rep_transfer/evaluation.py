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
from hestia import HestiaGenerator


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
               df: pd.DataFrame, hdg: HestiaGenerator, seed: int = 1):
    np.random.seed(seed)

    if dataset.split('-')[1] in REGRESSION_TASKS:
        pred_task = 'reg'
    elif dataset.split('-')[1] in CLASSIFICATION_TASKS:
        pred_task = 'class'

    x = np.array(pickle.load(
        open(osp.join('reps', f'{representation}_{dataset}.pickle'), 'rb')))
    y = df.labels.to_numpy()

    for th, partitions in hdg.get_partitions(filter=0.185):
        if th != 'random':
            if (th * 100) % 10 != 0:
                continue

        print("THRESHOLD:", th)

        train_idx = partitions['train']
        train_idx = train_idx + partitions['valid']
        test_idx = partitions['test']

        train_x, train_y = x[train_idx], y[train_idx]
        test_x, test_y = x[test_idx], y[test_idx]

        best_model = hpo(pred_task, model, train_x, train_y, seed)

        results = []
        if pred_task == 'class':
            preds = best_model.predict_proba({'default': test_x})[0]
            preds = preds[:, 1]
        else:
            preds = best_model.predict({'default': test_x})[0]

        result = evaluate(preds, test_y, pred_task=pred_task)
        result['seed'] = seed
        result['threshold'] = th
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
            dataset=dataset,
            model=model,
            representation=representation,
            df=df,
            hdg=hdg,
            seed=i
        )
        results_df = pd.concat([results_df, result_df])
    results_df.to_csv(results_path, index=False)


if __name__ == '__main__':
    typer.run(main)
