# YouTube Channel Tracker

YouTubeチャンネルの統計情報（登録者数、動画数、総再生回数など）を毎日自動的に記録し、可視化するツールです。

## 機能

- GitHub Actionsによる毎日自動データ収集
- YouTube Data API v3を使用
- CSVファイルへのデータ蓄積
- グラフによる可視化（登録者数の推移など）
- GitHub Pagesでの公開

## セットアップ

### 1. YouTube Data APIキーの取得

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」から「YouTube Data API v3」を有効化
4. 「認証情報」→「認証情報を作成」→「APIキー」を選択
5. 作成されたAPIキーをコピー

### 2. GitHubリポジトリの設定

1. このリポジトリをフォークまたはクローン
2. リポジトリの「Settings」→「Secrets and variables」→「Actions」を開く
3. 「New repository secret」をクリック
4. 以下のシークレットを追加：
   - Name: `YOUTUBE_API_KEY`
   - Secret: 取得したYouTube APIキー

### 3. チャンネルIDの設定

`config.json`ファイルを編集して、追跡したいチャンネルのIDを設定します。

```json
{
  "channels": [
    {
      "id": "UCxxxxxxxxxxxxxxxxxxxxxx",
      "name": "チャンネル名"
    }
  ]
}
```

チャンネルIDの確認方法：
- チャンネルページのURL: `https://www.youtube.com/channel/[チャンネルID]`
- または、カスタムURLの場合は、ページのソースから`channelId`を検索

### 4. GitHub Actionsの有効化

1. リポジトリの「Actions」タブを開く
2. ワークフローを有効化

## 使い方

- セットアップ後、毎日日本時間9:00（UTC 0:00）に自動でデータが収集されます
- データは`data/channel_stats.csv`に追記されます
- グラフは`docs/index.html`で確認できます
- GitHub Pagesを有効にすると、公開URLでグラフを閲覧可能

## 手動実行

ローカルでデータ収集を実行する場合：

```bash
# 依存パッケージのインストール
uv pip install -e .

# 環境変数の設定
export YOUTUBE_API_KEY="your-api-key-here"

# データ収集
python scripts/collect_data.py

# グラフ生成
python scripts/visualize.py
```

## ファイル構成

```
YouTube_Channel_Tracker/
├── .github/
│   └── workflows/
│       └── collect_stats.yml  # 自動実行設定
├── scripts/
│   ├── collect_data.py        # データ収集スクリプト
│   └── visualize.py           # グラフ生成スクリプト
├── data/
│   └── channel_stats.csv      # 統計データ（自動生成）
├── docs/
│   └── index.html            # グラフ表示ページ（自動生成）
├── config.json               # チャンネル設定
├── pyproject.toml           # プロジェクト設定
└── README.md
```

## 注意事項

- YouTube Data API v3には1日あたり10,000ユニットのクォータ制限があります
- チャンネル統計の取得は1チャンネルあたり約1ユニット消費します
- APIキーは絶対にGitHubにコミットしないでください（GitHub Secretsを使用）

## ライセンス

MIT License
