#!/usr/bin/env python3
"""静的グラフ画像を生成するスクリプト.

CSVデータを読み込み、登録者数・視聴回数・動画数の推移グラフをPNG画像として出力する.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


def load_csv_data(csv_path: Path) -> dict[str, list[Any]]:
    """CSVファイルからデータを読み込む.

    Args:
        csv_path: CSVファイルのパス

    Returns:
        各カラムのデータを格納した辞書
    """
    data: dict[str, list[Any]] = {
        'timestamp': [],
        'subscriber_count': [],
        'view_count': [],
        'video_count': [],
    }

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data['timestamp'].append(datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'))
            data['subscriber_count'].append(int(row['subscriber_count']))
            data['view_count'].append(int(row['view_count']))
            data['video_count'].append(int(row['video_count']))

    return data


def generate_graph(data: dict[str, list[Any]], output_path: Path, channel_name: str) -> None:
    """グラフ画像を生成する.

    Args:
        data: CSVから読み込んだデータ
        output_path: 出力画像のパス
        channel_name: グラフタイトルに表示するチャンネル名
    """
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    fig.suptitle(f'{channel_name} - Statistics', fontsize=14)

    timestamps = data['timestamp']

    # 登録者数
    axes[0].plot(timestamps, data['subscriber_count'], marker='o', markersize=3, color='#e74c3c')
    axes[0].set_ylabel('Subscribers')
    axes[0].grid(True, alpha=0.3)
    axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

    # 視聴回数
    axes[1].plot(timestamps, data['view_count'], marker='o', markersize=3, color='#3498db')
    axes[1].set_ylabel('Views')
    axes[1].grid(True, alpha=0.3)
    axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

    # 動画数
    axes[2].plot(timestamps, data['video_count'], marker='o', markersize=3, color='#2ecc71')
    axes[2].set_ylabel('Videos')
    axes[2].grid(True, alpha=0.3)
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    axes[2].xaxis.set_major_locator(mdates.AutoDateLocator())

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f'グラフ保存完了: {output_path}')


def main() -> None:
    """メイン処理を実行する."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / 'data'
    graphs_dir = project_root / 'graphs'

    graphs_dir.mkdir(exist_ok=True)

    csv_files = list(data_dir.glob('*.csv'))

    if not csv_files:
        print('CSVファイルが見つからない')
        return

    print(f'処理対象: {len(csv_files)} ファイル')
    print('-' * 50)

    for csv_path in csv_files:
        print(f'\n処理中: {csv_path.name}')

        data = load_csv_data(csv_path)

        if len(data['timestamp']) < 2:
            print('  -> データが2件未満のためスキップ')
            continue

        channel_id = csv_path.stem
        output_path = graphs_dir / f'{channel_id}.png'

        generate_graph(data, output_path, channel_id)

    print('\n' + '-' * 50)
    print('処理完了')


if __name__ == '__main__':
    main()
