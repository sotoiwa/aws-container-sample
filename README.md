# コンテナサンプルアプリ

## 参考リンク

- https://github.com/s01t/aws-container-workshop-cdk

## ローカルでの実行

### 事前準備

DynamoDBのテーブルが必要なため、マネジメントコンソールまたはCLIテーブルを作る。テーブル名は`messages`とし、プライマリーキーは文字列型の`uuid`とする。

```shell
aws dynamodb create-table --table-name 'messages' \
  --attribute-definitions '[{"AttributeName":"uuid","AttributeType": "S"}]' \
  --key-schema '[{"AttributeName":"uuid","KeyType": "HASH"}]' \
  --provisioned-throughput '{"ReadCapacityUnits": 1,"WriteCapacityUnits": 1}'
```

### アプリケーションの起動

ローカルからリモートのDynamoDBにアクセスキーを使ってアクセスする場合、DynamoDBにアクセス可能なIAMユーザーのクレデンシャルを`app/.env`ファイルに書く。

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

[http://localhost:5000](http://localhost:5000)からアプリケーションにアクセスする。

### アプリケーションの停止

```shell
docker-compose down
```

## Fargateでの実行

### 準備

DynamoDBはテーブルはCDK内に含めているので既に作成した場合は削除する。

```shell
aws dynamodb delete-table --table-name 'messages'
```

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
docker tag frontend:latest ${frontend_repo}:latest
docker tag backend:latest ${backend_repo}:latest
```

リモートにpushする。

```shell
# $(aws ecr get-login --no-include-email)
aws ecr get-login-password | docker login --username AWS --password-stdin https://${frontend_repo%%/*}
docker push ${frontend_repo}
docker push ${backend_repo}
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
