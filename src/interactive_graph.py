#!/usr/bin/env python3
"""インタラクティブダッシュボードを表示するスクリプト.

CSVデータを読み込み、期間フィルタや前日比・前週比を確認できるダッシュボードをブラウザで表示する.
ローカル環境での使用を想定.

実行方法:
    uv run streamlit run src/interactive_graph.py
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


@dataclass
class ChannelData:
    """チャンネルデータを格納するクラス."""

    timestamp: list[datetime] = field(default_factory=list)
    subscriber_count: list[int] = field(default_factory=list)
    view_count: list[int] = field(default_factory=list)
    video_count: list[int] = field(default_factory=list)


@dataclass
class ChangeMetrics:
    """変化量を格納するクラス."""

    daily_change: int | None = None
    daily_rate: float | None = None
    weekly_change: int | None = None
    weekly_rate: float | None = None


# ページ設定
st.set_page_config(
    page_title='YouTube Channel Tracker',
    page_icon='📊',
    layout='wide',
)


@st.cache_data
def load_csv_data(csv_path: Path) -> ChannelData:
    """CSVファイルからデータを読み込む.

    Args:
        csv_path: CSVファイルのパス

    Returns:
        チャンネルデータ
    """
    data = ChannelData()

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.timestamp.append(datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'))
            data.subscriber_count.append(int(row['subscriber_count']))
            data.view_count.append(int(row['view_count']))
            data.video_count.append(int(row['video_count']))

    return data


def filter_data_by_period(data: ChannelData, period: str) -> ChannelData:
    """指定期間でデータをフィルタする.

    Args:
        data: 元データ
        period: フィルタ期間

    Returns:
        フィルタ後のデータ
    """
    if period == '全期間' or not data.timestamp:
        return data

    now = datetime.now()
    period_days = {
        '過去7日': 7,
        '過去30日': 30,
        '過去90日': 90,
    }

    days = period_days.get(period, 0)
    if days == 0:
        return data

    cutoff = now - timedelta(days=days)

    filtered = ChannelData()

    for i, ts in enumerate(data.timestamp):
        if ts >= cutoff:
            filtered.timestamp.append(ts)
            filtered.subscriber_count.append(data.subscriber_count[i])
            filtered.view_count.append(data.view_count[i])
            filtered.video_count.append(data.video_count[i])

    return filtered


def calculate_metric_change(values: list[int], offset: int) -> ChangeMetrics:
    """指標の変化量を計算する.

    Args:
        values: 値のリスト
        offset: 比較対象のオフセット (1: 前日, 7: 前週)

    Returns:
        変化量メトリクス
    """
    metrics = ChangeMetrics()

    if len(values) <= offset:
        return metrics

    current = values[-1]
    previous = values[-(offset + 1)]

    change = current - previous
    rate = (change / previous * 100) if previous != 0 else 0.0

    if offset == 1:
        metrics.daily_change = change
        metrics.daily_rate = round(rate, 2)
    else:
        metrics.weekly_change = change
        metrics.weekly_rate = round(rate, 2)

    return metrics


def calculate_changes(data: ChannelData) -> dict[str, ChangeMetrics]:
    """前日比・前週比を計算する.

    Args:
        data: CSVから読み込んだデータ

    Returns:
        各指標の変化量
    """
    result: dict[str, ChangeMetrics] = {}

    for key in ['subscriber_count', 'view_count', 'video_count']:
        values: list[int] = getattr(data, key)

        daily = calculate_metric_change(values, 1)
        weekly = calculate_metric_change(values, 7)

        result[key] = ChangeMetrics(
            daily_change=daily.daily_change,
            daily_rate=daily.daily_rate,
            weekly_change=weekly.weekly_change,
            weekly_rate=weekly.weekly_rate,
        )

    return result


def format_change(change: int | None, rate: float | None) -> str:
    """変化量と変化率をフォーマットする.

    Args:
        change: 変化量
        rate: 変化率

    Returns:
        フォーマット済み文字列
    """
    if change is None:
        return 'データ不足'

    sign = '+' if change >= 0 else ''
    return f'{sign}{change:,} ({sign}{rate}%)'


def create_graph(data: ChannelData, channel_name: str) -> go.Figure:
    """グラフを作成する.

    Args:
        data: CSVから読み込んだデータ
        channel_name: グラフタイトルに表示するチャンネル名

    Returns:
        Plotly Figure オブジェクト
    """
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=('登録者数', '視聴回数', '動画数'),
    )

    timestamps = data.timestamp

    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=data.subscriber_count,
            mode='lines+markers',
            name='登録者数',
            line={'color': '#e74c3c'},
            hovertemplate='%{x}<br>登録者数: %{y:,}<extra></extra>',
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=data.view_count,
            mode='lines+markers',
            name='視聴回数',
            line={'color': '#3498db'},
            hovertemplate='%{x}<br>視聴回数: %{y:,}<extra></extra>',
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=data.video_count,
            mode='lines+markers',
            name='動画数',
            line={'color': '#2ecc71'},
            hovertemplate='%{x}<br>動画数: %{y:,}<extra></extra>',
        ),
        row=3,
        col=1,
    )

    fig.update_layout(
        title=f'{channel_name} - 統計推移',
        height=700,
        showlegend=False,
        hovermode='x unified',
    )

    fig.update_yaxes(tickformat=',', row=1, col=1)
    fig.update_yaxes(tickformat=',', row=2, col=1)
    fig.update_yaxes(tickformat=',', row=3, col=1)

    return fig


def main() -> None:
    """メイン処理を実行する."""
    st.title('📊 YouTube Channel Tracker')

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / 'data'

    csv_files = list(data_dir.glob('*.csv'))

    if not csv_files:
        st.error('CSVファイルが見つからない')
        return

    # サイドバー: 期間フィルタ
    st.sidebar.header('フィルタ設定')
    period = st.sidebar.selectbox(
        '表示期間',
        ['全期間', '過去7日', '過去30日', '過去90日'],
    )

    for csv_path in csv_files:
        channel_id = csv_path.stem

        # データ読み込み
        raw_data = load_csv_data(csv_path)

        if not raw_data.timestamp:
            st.warning(f'{channel_id}: データが空')
            continue

        # 期間フィルタ適用
        data = filter_data_by_period(raw_data, period)

        if not data.timestamp:
            st.warning(f'{channel_id}: 選択期間内にデータがない')
            continue

        # 最新値と変化量
        st.header(f'チャンネル: {channel_id}')

        changes = calculate_changes(raw_data)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label='登録者数',
                value=f'{data.subscriber_count[-1]:,}',
            )
            st.caption(f'前日比: {format_change(changes["subscriber_count"].daily_change, changes["subscriber_count"].daily_rate)}')
            st.caption(f'前週比: {format_change(changes["subscriber_count"].weekly_change, changes["subscriber_count"].weekly_rate)}')

        with col2:
            st.metric(
                label='視聴回数',
                value=f'{data.view_count[-1]:,}',
            )
            st.caption(f'前日比: {format_change(changes["view_count"].daily_change, changes["view_count"].daily_rate)}')
            st.caption(f'前週比: {format_change(changes["view_count"].weekly_change, changes["view_count"].weekly_rate)}')

        with col3:
            st.metric(
                label='動画数',
                value=f'{data.video_count[-1]:,}',
            )
            st.caption(f'前日比: {format_change(changes["video_count"].daily_change, changes["video_count"].daily_rate)}')
            st.caption(f'前週比: {format_change(changes["video_count"].weekly_change, changes["video_count"].weekly_rate)}')

        # グラフ表示
        fig = create_graph(data, channel_id)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()


if __name__ == '__main__':
    main()
