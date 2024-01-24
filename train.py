# coding: utf-8

import os
import glob
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.utils.data
import network
import train_data_creator
import game
import evaluate

TURN = 90
RANDOM_CREATE = True   #True:ランダムに着手 False:学習済みのモデルを使用

LR = 0.0001   #学習率(learning rate)
BATCH_GAME_SIZE = 1 #一度に学習する試合数
TEST_GAME_NUMBER = 3    #テスト時に使用する試合数
EPOCH = 5 #1つの訓練データを何回学習させるか

MODEL_PATH = os.path.join(os.path.dirname(__file__), "./output/model.pth")       #モデルの保存パス
BEST_MODEL_PATH = os.path.join(os.path.dirname(__file__), "./output/best_model.pth")       #最善モデルの保存パス
OPTIMIZER_PATH = os.path.join(os.path.dirname(__file__), "./output/optimizer.pth")       #オプティマイザの保存パス
RECORD_LIST_PATH = os.path.join(os.path.dirname(__file__), "./recordlist_train")         #対局データ一覧表（学習用）の保存パス
TEST_RECORD_LIST_PATH = os.path.join(os.path.dirname(__file__), "./recordlist_test") #対局データ一覧表（テスト用）の保存パス

update_times = 0    #モデルの更新回数

def test(model):    #未学習のデータを使って、正しく予測できているのか確認
    '''
    エージェント1について評価する
    '''
    model.eval()    #評価モード

    dataset = train_data_creator.get_dataset(TEST_RECORD_LIST_PATH, TEST_GAME_NUMBER, 0)
    if dataset is None: #学習データがなくなった
        return None

    ds_value_list          = dataset[0]
    ds_own_state_list      = dataset[1]
    ds_opponent_state_list = dataset[2]
    ds_own_point_list      = dataset[3]
    ds_opponent_point_list = dataset[4]
    ds_a1_pos_list         = dataset[5]
    ds_a1_best_move_list   = dataset[7]
    ds_won_list            = dataset[9]

    ds_value_list = ds_value_list.reshape(len(ds_value_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #value
    ds_own_state_list = ds_own_state_list.reshape(len(ds_own_state_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #state
    ds_opponent_state_list = ds_opponent_state_list.reshape(len(ds_opponent_state_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #state
    ds_own_point_list = ds_own_point_list.reshape(len(ds_own_point_list), 1, 1)   #point
    ds_opponent_point_list = ds_opponent_point_list.reshape(len(ds_opponent_point_list), 1, 1)   #point
    ds_a1_pos_list = ds_a1_pos_list.reshape(len(ds_a1_pos_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #agent pos
    ds_a1_best_move_list = ds_a1_best_move_list.reshape(len(ds_a1_best_move_list))   #best move
    ds_won_list = ds_won_list.reshape(len(ds_won_list), 1, 1)   #won

    a1_train_np = []    #入力データのリスト

    for ds_value, ds_own_state, ds_opponent_state, ds_a1_pos in zip(ds_value_list, ds_own_state_list, ds_opponent_state_list, ds_a1_pos_list):
        a1_train_np.append(np.array([ds_value, ds_own_state, ds_opponent_state, ds_a1_pos]))

    a1_train_np = np.array(a1_train_np)
    a1_target_np = np.array(ds_a1_best_move_list)

    test = torch.utils.data.TensorDataset(torch.from_numpy(a1_train_np).float(), torch.from_numpy(a1_target_np).long())
    test_loader = torch.utils.data.DataLoader(test, batch_size=TEST_GAME_NUMBER*TURN, shuffle=True)

    total_loss = 0
    for _, data in enumerate(test_loader):
        '''
        読み込んでいる数とミニバッチのサイズが同じだから、ここは1回しか実行されない
        '''
        inputs, labels = data

        model.train()   #訓練モード
        if torch.cuda.is_available(): #GPUを使える時
            inputs, labels = torch.autograd.Variable(inputs.cuda()), torch.autograd.Variable(labels.cuda())
        else:
            inputs, labels = torch.autograd.Variable(inputs), torch.autograd.Variable(labels)
        optimizer.zero_grad()
        out = model(inputs)

        loss = criterion(out, labels)
        total_loss += loss.item()

    return total_loss


os.makedirs('output', exist_ok=True)  #モデルなどの出力ディレクトリ作成

#モデルが保存されていれば読み込み、なければ新規作成
if os.path.exists(MODEL_PATH):
    fine_tune = True
    model = network.Network()
    model.load_state_dict(torch.load(MODEL_PATH, map_location=lambda storage, loc: storage))
else:
    fine_tune = False
    model = network.Network()

if torch.cuda.is_available(): #GPUが使える場合は、モデルをGPUに転送
    model.cuda()

#オプティマイザが保存されていれば読み込み、なければ新規作成
if os.path.exists(OPTIMIZER_PATH):
    fine_tune = True
    optimizer = optim.Adam(model.parameters(), lr=LR)
    optimizer.load_state_dict(torch.load(OPTIMIZER_PATH, map_location=lambda storage, loc: storage))
else:
    fine_tune = False
    optimizer = optim.Adam(model.parameters(), lr=LR)

criterion = nn.CrossEntropyLoss()   #推論値と理論値の差を計算

max_win_ratio = -1.0    #勝率の最高値

for epoch in range(1, EPOCH+1):   #エポックを回す
    print("epoch:", epoch)          #現在のエポック数（何回目のループか）

    record_index = 0    #読み出す試合データの最初のインデックス

    while True: #全学習データを扱う
        if not torch.cuda.is_available(): #GPUを使えない　Colaboratoryにおける大量表示によるブラウザの不安定化対策
            print("epoch:{0} record:{1}".format(epoch, record_index))

        #バッチサイズ分の訓練データと正解ラベルを取得
        #datasetは、[X_value, X_own_status, X_opponent_status, X_own_points, X_opponent_points, X_a1_poss, X_a2_poss, won]
        #それぞれの要素は、バッチサイズ分の対局の全局面でシャッフルなし
        dataset = train_data_creator.get_dataset(RECORD_LIST_PATH, BATCH_GAME_SIZE, record_index)
        if dataset is None: #学習データがなくなった
            break

        ds_value_list          = dataset[0]
        ds_own_state_list      = dataset[1]
        ds_opponent_state_list = dataset[2]
        ds_own_point_list      = dataset[3]
        ds_opponent_point_list = dataset[4]
        ds_a1_pos_list         = dataset[5]
        ds_a2_pos_list         = dataset[6]
        ds_a1_best_move_list   = dataset[7]
        ds_a2_best_move_list   = dataset[8]
        ds_won_list            = dataset[9]

        # #データ型をndarrayからtorchに変更 float,longにしているのは決まりだから
        # train_torch = torch.from_numpy(train_np).float()
        # target_torch = torch.from_numpy(target_np).long()

        ds_value_list = ds_value_list.reshape(len(ds_value_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #value
        ds_own_state_list = ds_own_state_list.reshape(len(ds_own_state_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #state
        ds_opponent_state_list = ds_opponent_state_list.reshape(len(ds_opponent_state_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #state
        ds_own_point_list = ds_own_point_list.reshape(len(ds_own_point_list), 1, 1)   #point
        ds_opponent_point_list = ds_opponent_point_list.reshape(len(ds_opponent_point_list), 1, 1)   #point
        ds_a1_pos_list = ds_a1_pos_list.reshape(len(ds_a1_pos_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #agent pos
        ds_a2_pos_list = ds_a2_pos_list.reshape(len(ds_a2_pos_list), game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)   #agent pos
        ds_a1_best_move_list = ds_a1_best_move_list.reshape(len(ds_a1_best_move_list))   #best move
        ds_a2_best_move_list = ds_a2_best_move_list.reshape(len(ds_a2_best_move_list))   #best move
        ds_won_list = ds_won_list.reshape(len(ds_won_list), 1, 1)   #won

        a1_train_np = []    #入力データのリスト
        a2_train_np = []

        for ds_value, ds_own_state, ds_opponent_state, ds_a1_pos in zip(ds_value_list, ds_own_state_list, ds_opponent_state_list, ds_a1_pos_list):
            a1_train_np.append(np.array([ds_value, ds_own_state, ds_opponent_state, ds_a1_pos]))

        for ds_value, ds_own_state, ds_opponent_state, ds_a2_pos in zip(ds_value_list, ds_own_state_list, ds_opponent_state_list, ds_a2_pos_list):
            a2_train_np.append(np.array([ds_value, ds_own_state, ds_opponent_state, ds_a2_pos]))

        a1_train_np = np.array(a1_train_np)
        a2_train_np = np.array(a2_train_np)

        a1_target_np = np.array(ds_a1_best_move_list)
        a2_target_np = np.array(ds_a2_best_move_list)

        train_1 = torch.utils.data.TensorDataset(torch.from_numpy(a1_train_np).float(), torch.from_numpy(a1_target_np).long())
        train_2 = torch.utils.data.TensorDataset(torch.from_numpy(a2_train_np).float(), torch.from_numpy(a2_target_np).long())

        train_loader_1 = torch.utils.data.DataLoader(train_1, batch_size=BATCH_GAME_SIZE*TURN, shuffle=True)
        train_loader_2 = torch.utils.data.DataLoader(train_2, batch_size=BATCH_GAME_SIZE*TURN, shuffle=True)

        total_loss = 0
        #エージェント1
        for i, data in enumerate(train_loader_1):
            '''
            読み込んでいる数とミニバッチのサイズが同じだから、ここは1回しか実行されない
            '''
            inputs, labels = data

            model.train()   #訓練モード
            if torch.cuda.is_available(): #GPUを使える時
                inputs, labels = torch.autograd.Variable(inputs.cuda()), torch.autograd.Variable(labels.cuda())
            else:
                inputs, labels = torch.autograd.Variable(inputs), torch.autograd.Variable(labels)
            optimizer.zero_grad()
            out = model(inputs)

            loss = criterion(out, labels)
            total_loss += loss.item()
            loss.backward()
            optimizer.step()

            if (record_index+i)%500 == 0:    #ロスの平均を表示 iは0のままだから、500試合分を処理するごとにロスを表示
                print("[epoch:{0} minibatch:{1} aspect:{2}]".format(epoch, record_index//BATCH_GAME_SIZE, i))
                print("loss", total_loss)

                test_loss = test(model)
                print("test_loss", test_loss)
                total_loss = 0.0

            # print("x:{0} t:{1} y:{2} loss:{3}".format(x, t, y, loss))

            torch.save(model.state_dict(), MODEL_PATH)  #モデルの保存

            model.eval()    #評価モード
            if (record_index+i)%50 == 0:   #学習50回ごとにモデルが最善か確認
                if RANDOM_CREATE is False:
                    max_win_ratio = 0.8 #学習済みモデルに勝ち越せれば、モデルを更新
                ratio = evaluate.evaluate_model(model, 10)  #勝率
                print("played {} games for evaluating".format(10))
                print("win ratio:{}".format(ratio))
                if max_win_ratio <= ratio:  #勝率が今までの最高値より高い
                    print("max update:{0} >= {1}".format(ratio, max_win_ratio))
                    update_times += 1
                    if RANDOM_CREATE is False: print("model updated times", update_times)
                    max_win_ratio = ratio
                    torch.save(model.state_dict(), BEST_MODEL_PATH)  #ベストモデルの保存
                else:
                    print("{0} <= {1}".format(ratio, max_win_ratio))

        #エージェント2
        for i, data in enumerate(train_loader_2):
            '''
            読み込んでいる数とミニバッチのサイズが同じだから、ここは1回しか実行されない
            '''
            inputs, labels = data

            model.train()   #訓練モード
            if torch.cuda.is_available(): #GPUを使える時
                inputs, labels = torch.autograd.Variable(inputs.cuda()), torch.autograd.Variable(labels.cuda())
            else:
                inputs, labels = torch.autograd.Variable(inputs), torch.autograd.Variable(labels)
            optimizer.zero_grad()
            out = model(inputs)

            loss = criterion(out, labels)
            total_loss += loss.item()
            loss.backward()
            optimizer.step()

            if (record_index+i)%500 == 0:    #ロスの平均を表示 iは0のままだから、500試合分を処理するごとにロスを表示
                print("[epoch:{0} minibatch:{1} aspect:{2}]".format(epoch, record_index//BATCH_GAME_SIZE, i))
                print("loss", total_loss)

                test_loss = test(model)
                print("test_loss", test_loss)
                total_loss = 0.0

            # print("x:{0} t:{1} y:{2} loss:{3}".format(x, t, y, loss))

            torch.save(model.state_dict(), MODEL_PATH)  #モデルの保存

            model.eval()    #評価モード
            if (record_index+i)%50 == 0:   #学習50回ごとにモデルが最善か確認
                if RANDOM_CREATE is False:
                    max_win_ratio = 0.8 #学習済みモデルに勝ち越せれば、モデルを更新
                ratio = evaluate.evaluate_model(model, 10)  #勝率
                print("played {} games for evaluating".format(10))
                print("win ratio:{}".format(ratio))
                if max_win_ratio <= ratio:  #勝率が今までの最高値より高い
                    print("max update:{0} >= {1}".format(ratio, max_win_ratio))
                    update_times += 1
                    if RANDOM_CREATE is False: print("model updated times", update_times)
                    max_win_ratio = ratio
                    torch.save(model.state_dict(), BEST_MODEL_PATH)  #ベストモデルの保存
                else:
                    print("{0} <= {1}".format(ratio, max_win_ratio))


        record_index += BATCH_GAME_SIZE

    torch.save(optimizer.state_dict(), OPTIMIZER_PATH)  #オプティマイザの保存

print("Finished Training")