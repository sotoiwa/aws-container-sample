# コンテナサンプルアプリ

## 参考リンク

- https://github.com/s01t/aws-container-workshop-cdk

## ローカルでの実行

DynamoDBのテーブルが必要なため、マネージメントコンソールでテーブルを作る。テーブル名は`messages`とし、プライマリーキーは文字列型の`uuid`とする。

DynamoDBにアクセス可能なIAMユーザーのクレデンシャルを`app/.env`ファイルに書く。

```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

イメージのビルドして起動する。

```shell
cd app
docker-compose build
docker-compose up
```

## Fargateでの実行

### イメージのECRへの登録

リポジトリを作成する。

```shell
aws ecr create-repository --repository-name frontend
aws ecr create-repository --repository-name backend
```

リポジトリのURIを取得する。

```shell
frontend_repo=$(aws ecr describe-repositories --repository-names frontend --query 'repositories[0].repositoryUri' --output text)
backend_repo=$(aws ecr describe-repositories --repository-names backend --query 'repositories[0].repositoryUri' --output text)
```

タグ付けする。

```shell
docker tag frontend $frontend_repo
docker tag backend $backend_repo
```

リモートにpushする。

```shell
# $(aws ecr get-login --no-include-email)
aws ecr get-login-password | docker login --username AWS --password-stdin https://${frontend_repo%%/*}
docker push $frontrepo
docker push $backrepo
```

### CDKのインストール

Node.jsのインストールについては省略。

CDKをインストールする。

```shell
npm install -g aws-cdk
```

### CDKでのデプロイ

Pythonのvirtualenvを作成し、必要なモジュールをインストールする。

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

デプロイを実行する。

```shell
cdk deploy *Stack
```
