"""
classify_errors.py
Classifies error samples into three categories:
  - "Gravação inválida"         : recording too short to be valid
  - "Exercício realizado"       : exercise was done but peak detection failed
  - "Exercício não realizado"   : no meaningful movement detected
Outputs: errors_classified.csv
"""

import os
import csv
import json
import statistics as st
from scipy.signal import find_peaks
from helpers import prepare_accelerometer_data

# ── Config ───────────────────────────────────────────────────────────────────
DATA_PATH         = './data'
ERRORS_CSV        = './errors.csv'
OUTPUT_CSV        = './errors_classified.csv'

MIN_VALID_TIME    = 5.0    # seconds — shorter than this is a bad recording
MIN_REP_TIME      = 0.3    # seconds — minimum time between repetitions (permissive)
MIN_PEAKS_DONE    = 3      # minimum peaks to consider exercise "done"

# ── Helpers ──────────────────────────────────────────────────────────────────

def load_accel(sample_id):
    path = os.path.join(DATA_PATH, str(sample_id), 'accelerometer.txt')
    with open(path, 'r') as f:
        lines = f.readlines()
    data = {'accelerometer': []}
    for line in lines[1:]:
        parts = line.split()
        data['accelerometer'].append([eval(parts[0]), [eval(c) for c in parts[1:]]])
    return prepare_accelerometer_data(data)


def permissive_peaks(accel_data, min_rep_time=MIN_REP_TIME):
    """Find peaks with no height threshold — only minimum spacing."""
    mag = accel_data['accel_magnitude']
    experiment_time = accel_data['experiment_time']
    total_time = experiment_time[-1] if len(experiment_time) > 1 else 1.0
    fs = (len(mag) - 1) / total_time if total_time > 0 else 100.0
    min_distance = max(1, int(min_rep_time * fs))
    peaks, props = find_peaks(mag, distance=min_distance, prominence=0.01)
    return peaks, props


def classify(sample_id):
    try:
        accel_data = load_accel(sample_id)
    except Exception as e:
        return 'Erro ao ler ficheiro', str(e), 0, 0

    total_time = accel_data['experiment_time'][-1]

    if total_time < MIN_VALID_TIME:
        return 'Gravação inválida', f'duração={total_time:.1f}s', 0, total_time

    peaks, props = permissive_peaks(accel_data)
    n_peaks = len(peaks)

    mag = accel_data['accel_magnitude']
    mean_mag = st.fmean(mag)

    if n_peaks >= MIN_PEAKS_DONE:
        mean_prominence = float(props['prominences'].mean()) if n_peaks else 0
        label = 'Exercício realizado'
        detail = f'picos_permissivos={n_peaks}, prominence_média={mean_prominence:.4f}'
    else:
        label = 'Exercício não realizado'
        detail = f'picos_permissivos={n_peaks}, mean_magnitude={mean_mag:.3f}'

    return label, detail, n_peaks, total_time


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    error_ids = []
    with open(ERRORS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                error_ids.append(int(row['Sample']))
            except ValueError:
                pass

    results = []
    counts = {'Gravação inválida': 0, 'Exercício realizado': 0, 'Exercício não realizado': 0, 'Erro ao ler ficheiro': 0}

    for sid in error_ids:
        label, detail, n_peaks, total_time = classify(sid)
        counts[label] = counts.get(label, 0) + 1
        results.append({
            'Sample': sid,
            'Classificação': label,
            'Total Time (s)': round(total_time, 2),
            'Picos Permissivos': n_peaks,
            'Detalhe': detail,
        })
        print(f'[{sid:>3}] {label:<30} | {detail}')

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Sample', 'Classificação', 'Total Time (s)', 'Picos Permissivos', 'Detalhe'])
        writer.writeheader()
        writer.writerows(results)

    print(f'\n{"─"*55}')
    print(f'Gravação inválida       : {counts["Gravação inválida"]}')
    print(f'Exercício realizado     : {counts["Exercício realizado"]}')
    print(f'Exercício não realizado : {counts["Exercício não realizado"]}')
    print(f'Total erros analisados  : {len(results)}')
    print(f'\nGuardado em: {OUTPUT_CSV}')


if __name__ == '__main__':
    main()
