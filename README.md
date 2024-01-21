# procon2018_kyogi_solver
ソルバー | 高専プロコン第29回課題部門

全国高等専門学校プログラミングコンテスト 第29回阿南大会（2018）の競技部門で使用したソルバーです。


全国高専プロコン　http://www.procon.gr.jp/  
第29回阿南大会　　http://www.procon.gr.jp/?page_id=64541

## 構成
* 言語 Python
* ライブラリ PyTorch

## 使用方法
本リポジトリをcloneし、以下の手順で実行すると動作します。  
ソルバーとして動作させるには、事前に[GUI](https://github.com/nnct-jo-ken/procon2018_kyogi_GUI)を起動させておいてください。  
`colaboratory.ipynb`を使用すると、Colaboratoryを利用して対局データの生成と学習を行うことができます。

```
conda create --name procon2018 python=3.10
pip install torch numpy fastapi uvicorn python-multipart
git submodule init
```

```
# 対局データの生成
python create_record.py

# 対局データのファイルパスを、訓練用とテスト用に振り分け
python make_record_list.py

# 学習
python train.py

# GUIと接続し、ソルバーとして動作
python main.py
```
