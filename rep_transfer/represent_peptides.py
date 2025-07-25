import pickle
import os

import numpy as np
import pandas as pd
import typer

from multiprocessing import cpu_count
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map


def protein_data_binding(device: str):
    from autopeptideml.reps.lms import RepEngineLM
    re = RepEngineLM('esm2-8m', average_pooling=True)
    re.move_to_device(device)
    out_path1 = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'binding-c-targets.pickle'
    )
    out_path2 = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'binding-nc-targets.pickle'
    )
    df1 = pd.read_csv(
        os.path.join(os.path.dirname(__file__), '..', 'downstream_data',
                     f'c-binding.csv'))
    df2 = pd.read_csv(
        os.path.join(os.path.dirname(__file__), '..', 'downstream_data',
                     f'nc-binding.csv'))
    fp = re.compute_reps(df1['seq1'], batch_size=64 if re.get_num_params() < 1e8 else 16,
                         verbose=True)
    fp = [f.tolist() for f in fp]
    pickle.dump(fp, open(os.path.join(out_path1), 'wb'))
    fp = re.compute_reps(df2['seq1'], batch_size=64 if re.get_num_params() < 1e8 else 16,
                         verbose=True)
    fp = [f.tolist() for f in fp]
    pickle.dump(fp, open(os.path.join(out_path2), 'wb'))


def calculate_fragfp(dataset: str, radius: int):
    from fragfp import FragFPGenerator

    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'fragfp-{radius}_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    if os.path.exists(out_path):
        return
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    fpgen = FragFPGenerator(
       fpSize=2_048, out_radius=radius
    )
    fps = []
    fps = thread_map(fpgen, df['SMILES'], max_workers=cpu_count())

    # for smiles in tqdm(df['SMILES']):
    #     print("-\n", smiles, "-\n")
    #     fps.append(fpgen(smiles))
    fps = np.stack(fps)
    print(len(fps[fps.sum(1) > 1]))
    fps = fps.tolist()
    pickle.dump(fps, open(os.path.join(out_path), 'wb'))


def calculate_new_esm(dataset: str, model: str, device: str):
    from autopeptideml.reps.lms import RepEngineLM
    from autopeptideml.pipeline import Pipeline
    from autopeptideml.pipeline.smiles import SmilesToSequence
    from autopeptideml.pipeline.sequence import CanonicalCleaner

    pipe = Pipeline(
        elements=[SmilesToSequence(keep_analog=True),
                  CanonicalCleaner(substitution='X')],
        name='pipe',
    )
    re = RepEngineLM(model, average_pooling=True)
    re.move_to_device(device)
    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'new-{model}_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    if os.path.exists(out_path):
        return
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    if 'sequence' in df.columns:
        seqs = df.sequence.tolist()
    else:
        seqs = pipe(df['SMILES'].tolist())
    fp = re.compute_reps(seqs, batch_size=64 if re.get_num_params() < 1e8 else 16,
                         verbose=True)
    fp = [f.tolist() for f in fp]
    pickle.dump(fp, open(os.path.join(out_path), 'wb'))


def calculate_esm(dataset: str, model: str, device: str):
    from autopeptideml.reps.lms import RepEngineLM
    from autopeptideml.pipeline import Pipeline
    from autopeptideml.pipeline.smiles import SmilesToSequence
    from autopeptideml.pipeline.sequence import CanonicalCleaner

    pipe = Pipeline(
        elements=[SmilesToSequence(keep_analog=False),
                  CanonicalCleaner(substitution='X')],
        name='pipe',
    )
    re = RepEngineLM(model, average_pooling=True)
    re.move_to_device(device)
    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'{model}_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    if os.path.exists(out_path):
        return
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    if 'sequence' in df.columns:
        seqs = df.sequence.tolist()
    else:
        seqs = pipe(df['SMILES'].tolist())
    fp = re.compute_reps(seqs, batch_size=64 if re.get_num_params() < 1e8 else 16,
                         verbose=True)
    fp = [f.tolist() for f in fp]
    pickle.dump(fp, open(os.path.join(out_path), 'wb'))


def calculate_ecfp(dataset: str):
    from rdkit import Chem
    from rdkit.Chem import rdFingerprintGenerator

    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'ecfp_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    if os.path.exists(out_path):
        return
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    fpgen = rdFingerprintGenerator.GetMorganGenerator(
        radius=8, fpSize=2_048
    )

    def _get_fp(smile: str):
        mol = Chem.MolFromSmiles(smile)
        fp = fpgen.GetFingerprintAsNumPy(mol).astype(np.int8)
        return fp

    fps = thread_map(
        _get_fp, df['SMILES'], max_workers=8
    )
    fps = np.stack(fps).tolist()
    pickle.dump(fps, open(os.path.join(out_path), 'wb'))


def calculate_ecfp_count(dataset: str):
    from rdkit import Chem
    from rdkit.Chem import rdFingerprintGenerator

    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'ecfp-count_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    if os.path.exists(out_path):
        return
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    fpgen = rdFingerprintGenerator.GetMorganGenerator(
        radius=8, fpSize=2_048, countSimulation=True
    )

    def _get_fp(smile: str):
        mol = Chem.MolFromSmiles(smile)
        fp = fpgen.GetFingerprintAsNumPy(mol).astype(np.int32)
        return fp

    fps = thread_map(
        _get_fp, df['SMILES'], max_workers=8
    )
    fps = np.stack(fps).tolist()
    pickle.dump(fps, open(os.path.join(out_path), 'wb'))


def calculate_chemberta(dataset: str, device: str):
    from autopeptideml.reps.lms import RepEngineLM

    re = RepEngineLM('chemberta-2', average_pooling=True)
    re.move_to_device(device)
    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'chemberta_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    if os.path.exists(out_path):
        return
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    fp = re.compute_reps(df['SMILES'], batch_size=64 if re.get_num_params() < 1e8 else 16,
                         verbose=True)
    fp = [f.tolist() for f in fp]
    pickle.dump(fp, open(os.path.join(out_path), 'wb'))
    return fp


def calculate_molformer(dataset: str, device: str):
    from autopeptideml.reps.lms import RepEngineLM

    re = RepEngineLM('molformer-xl', average_pooling=True)
    re.move_to_device(device)
    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'molformer_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    if os.path.exists(out_path):
        return
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    fp = re.compute_reps(df['SMILES'], batch_size=64 if re.get_num_params() < 1e8 else 16,
                         verbose=True)
    fp = [f.tolist() for f in fp]
    pickle.dump(fp, open(os.path.join(out_path), 'wb'))
    return fp


def calculate_pepclm(dataset: str):
    from utils.pepclm_tokenizer import SMILES_SPE_Tokenizer
    import transformers as hf
    import torch

    device = 'mps'
    batch_size = 8
    out_path = os.path.join(os.path.dirname(__file__),
        '..', 'reps', f'pepclm_{dataset}.pickle')
    if os.path.exists(out_path):
        return
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    tokenizer = SMILES_SPE_Tokenizer(
        os.path.join(os.path.dirname(__file__), 'utils',
                     'tokenizer', 'new_vocab.txt'),
        os.path.join(os.path.dirname(__file__), 'utils',
                     'tokenizer', 'new_splits.txt')
    )
    model = hf.AutoModel.from_pretrained('aaronfeller/PeptideCLM-23M-all',
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
    pickle.dump(fps, open(os.path.join(out_path), 'wb'))


def calculate_pepfunnfp(dataset: str):
    from pepfunn.similarity import monomerFP

    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'pepfunn_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    if os.path.exists(out_path):
        return
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))
    n_bits = 2048

    def _get_fp(smile: str):
        try:
            fp, dict_fp = monomerFP(smile, radius=2, nBits=n_bits,
                                    add_freq=True,
                                    property_lib='property_ext.txt')
        except ValueError:
            if 'X' in smile:
                smile = smile.replace('X', 'G')
                fp = _get_fp(smile)
            else:
                print(smile)
                return np.zeros((n_bits,))
        except TypeError:
            return np.zeros((n_bits,))
        return np.array(fp)

    fps = thread_map(
        _get_fp, df['BILN'], max_workers=8
    )
    counter = len([a for a in fps if a.sum() == 0])
    print('Faulty Pepfunn: ', counter)
    # fps = [np.zeros((2048,)) if a is None else a for a in fps]
    fps = np.stack(fps).tolist()
    pickle.dump(fps, open(os.path.join(out_path), 'wb'))


def calculate_pepland(dataset: str):
    from utils.pepland_utils.inference import run

    out_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'reps', f'pepland_{dataset}.pickle'
    )
    os.makedirs((os.path.join(
        os.path.dirname(__file__),
        '..', 'reps')), exist_ok=True)
    df = pd.read_csv(os.path.join(
        os.path.dirname(__file__),
        '..', 'downstream_data', f'{dataset}.csv'
    ))

    embds = run(df.SMILES.tolist(), 1)
    embds = embds.tolist()
    pickle.dump(embds, open(out_path, 'w'))


def main(dataset: str, rep: str, device: str = 'mps'):
    if dataset == 'binding-targets':
        protein_data_binding(device)
        return
    if rep == 'ecfp':
        print('Calculating ECFP representations...')
        calculate_ecfp(dataset)
    elif rep == 'ecfp-count':
        print('Calculating ECFP count representations...')
        calculate_ecfp_count(dataset)
    elif rep == 'molformer':
        print('Calculating MolFormer-XL representations...')
        calculate_molformer(dataset, device)
    elif rep == 'chemberta':
        print('Calculating ChemBERTa-2 77M MLM representations')
        calculate_chemberta(dataset, device)
    elif rep == 'pepclm':
        print('Calculating PeptideCLM representations...')
        calculate_pepclm(dataset)
    elif rep == 'pepland':
        print('Calculating Pepland representations...')
        calculate_pepland(dataset)
    elif rep == 'pepfunn':
        print('Calculating pepfunn fingerprint...')
        calculate_pepfunnfp(dataset)
    elif 'new-esm' in rep or 'new-prot' in rep or 'new-prost' in rep:
        print(f'Calculating {rep.upper()} representations...')
        calculate_new_esm(dataset, rep.replace('new-', ''), device)
    elif 'esm' in rep or 'prot' in rep or 'prost' in rep:
        print(f'Calculating {rep.upper()} representations...')
        calculate_esm(dataset, rep, device)
    elif 'fragfp' in rep:
        print('Calculating FragFP representations...')
        calculate_fragfp(dataset, int(rep.split('-')[1]))


if __name__ == '__main__':
    typer.run(main)
