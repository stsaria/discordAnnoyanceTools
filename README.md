# Discordの荒らし等のツール
https://github.com/user-attachments/assets/a0d6f460-142b-4e97-bf82-c616b433ee61


※このプログラムは、私が勉強用として作ったものですので、これで荒らしして特定とかされても責任を負うことはないですよ〜
ちなみにLinuxはあんまりちゃんと動かないです
## ツールリスト
- Nuke (名前の通り、荒らしツール)
- SelfBotNuke (上は管理者が認証してBotを入れる必要があるが、これはユーザーとして参加するから、ロールなど以外は管理者認証が不要)
- Grabbr(何らかのツール（チート・荒らしとか）だと思ってTOKENを入力したら、送信されてしまう)
## 使用ポート
- 8080 : 通常のツール用Flaskポート
- 8081 : セルフボット用Flaskポート
## 実行方法
- ダウンロード
```
git clone https://github.com/stsaria/discordAnnoyanceTools
```
- 実行
```
start.bat
```
※なんだかんだLinuxとかではrootじゃないと動かない
