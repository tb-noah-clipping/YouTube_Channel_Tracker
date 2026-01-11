#!/usr/bin/env python3
"""YouTube Channel Tracker.

指定したYouTubeチャンネルの統計情報を取得し、CSVファイルに記録する.
"""

import csv
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError


def get_api_key() -> str:
    """環境変数からAPIキーを取得する.

    Returns:
        APIキー文字列

    Raises:
        ValueError: 環境変数が設定されていない場合
    """
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        msg = 'YOUTUBE_API_KEY 環境変数が設定されていない.\nローカル実行: set YOUTUBE_API_KEY=your_key\nGitHub Actions: Secretsに登録すること'
        raise ValueError(msg)
    return api_key


def load_channels_config(config_path: Path) -> list[dict[str, Any]]:
    """チャンネル設定ファイルを読み込む.

    Args:
        config_path: 設定ファイルのパス

    Returns:
        チャンネル設定のリスト
    """
    with open(config_path, encoding='utf-8') as f:
        config: dict[str, Any] = json.load(f)
    channels: list[dict[str, Any]] = config.get('channels', [])
    return channels


def get_channel_id_from_handle(youtube: Resource, handle: str) -> str | None:
    """ハンドル名(@username)からチャンネルIDを取得する.

    Args:
        youtube: YouTube API クライアント
        handle: ハンドル名 (例: "@963noah")

    Returns:
        チャンネルID または None
    """
    handle_clean = handle.lstrip('@')

    try:
        request = youtube.channels().list(
            part='id',
            forHandle=handle_clean,
        )
        response: dict[str, Any] = request.execute()

        if response.get('items'):
            channel_id: str = response['items'][0]['id']
            return channel_id

        return None

    except HttpError as e:
        print(f'チャンネルID取得エラー ({handle}): {e}')
        return None


def get_channel_stats(youtube: Resource, channel_id: str) -> dict[str, int | str | bool] | None:
    """チャンネルIDから統計情報を取得する.

    Args:
        youtube: YouTube API クライアント
        channel_id: YouTubeチャンネルID

    Returns:
        統計情報の辞書 または None
    """
    try:
        request = youtube.channels().list(
            part='statistics,snippet',
            id=channel_id,
        )
        response: dict[str, Any] = request.execute()

        if not response.get('items'):
            print(f'チャンネルが見つからない: {channel_id}')
            return None

        item: dict[str, Any] = response['items'][0]
        stats: dict[str, Any] = item['statistics']
        snippet: dict[str, Any] = item['snippet']

        return {
            'channel_id': channel_id,
            'channel_name': snippet.get('title', ''),
            'subscriber_count': int(stats.get('subscriberCount', 0)),
            'view_count': int(stats.get('viewCount', 0)),
            'video_count': int(stats.get('videoCount', 0)),
            'hidden_subscriber_count': stats.get('hiddenSubscriberCount', False),
        }

    except HttpError as e:
        print(f'統計情報取得エラー ({channel_id}): {e}')
        return None


def save_to_csv(data: dict[str, int | str | bool], output_dir: Path) -> None:
    """統計データをCSVファイルに追記する.

    チャンネルごとに別ファイルで管理する.

    Args:
        data: 統計データ
        output_dir: 出力ディレクトリ
    """
    filename = f'{data["channel_id"]}.csv'
    filepath = output_dir / filename

    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')

    row = {
        'timestamp': timestamp,
        'subscriber_count': data['subscriber_count'],
        'view_count': data['view_count'],
        'video_count': data['video_count'],
    }

    file_exists = filepath.exists()

    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['timestamp', 'subscriber_count', 'view_count', 'video_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    print(f'保存完了: {filepath}')


def main() -> None:
    """メイン処理を実行する."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / 'config' / 'channels.json'
    data_dir = project_root / 'data'

    data_dir.mkdir(exist_ok=True)

    api_key = get_api_key()
    youtube: Resource = build('youtube', 'v3', developerKey=api_key)

    channels = load_channels_config(config_path)

    if not channels:
        print('追跡するチャンネルが設定されていない')
        return

    print(f'対象チャンネル数: {len(channels)}')
    print('-' * 50)

    for channel_config in channels:
        handle: str = channel_config.get('handle', '')
        name: str = channel_config.get('name', handle)

        print(f'\n処理中: {name} ({handle})')

        channel_id = get_channel_id_from_handle(youtube, handle)

        if not channel_id:
            print('  -> チャンネルIDの取得に失敗した')
            continue

        print(f'  -> チャンネルID: {channel_id}')

        stats = get_channel_stats(youtube, channel_id)

        if not stats:
            print('  -> 統計情報の取得に失敗した')
            continue

        print(f'  -> 登録者数: {stats["subscriber_count"]:,}')
        print(f'  -> 総視聴回数: {stats["view_count"]:,}')
        print(f'  -> 動画数: {stats["video_count"]:,}')

        save_to_csv(stats, data_dir)

    print('\n' + '-' * 50)
    print('処理完了')


if __name__ == '__main__':
    main()
