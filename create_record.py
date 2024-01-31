# coding: utf-8

import os, time
import copy
import torch
import numpy as np
import game
import player
import network
import neural_player

DEBUG = False    #デバッグ時はTrue
RANDOM_CREATE = True   #True:ランダムに着手 False:学習済みのモデルを使用RECORD_NUM = 10  #対局データ作成数
RECORD_NUM = 100  #対局データ作成数
TURN = 30   #1試合あたりのターン数
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "record")  #出力ディレクトリ
os.makedirs(OUTPUT_DIR, exist_ok=True)  #出力ディレクトリの作成

MODEL_PATH = os.path.join(os.path.dirname(__file__), "./output/best_model.pth")       #最善モデルの保存パス

if RANDOM_CREATE is False:  #学習済みモデルを使用
    if os.path.exists(MODEL_PATH):
        model = network.Network()
        model.load_state_dict(torch.load(MODEL_PATH, map_location=lambda storage, loc: storage))
    else:
        raise Exception("学習済みモデルがありません")

    players = {
        game.OWN_1: neural_player.DQNPlayer(model),
        game.OWN_2: neural_player.DQNPlayer(model),
        game.OPPONENT_1: neural_player.DQNPlayer(model),
        game.OPPONENT_2: neural_player.DQNPlayer(model)
    }
elif RANDOM_CREATE is True:
    #完全ランダムくん
    players = {
        game.OWN_1: player.RandomUniform(),
        game.OWN_2: player.RandomUniform(),
        game.OPPONENT_1: player.RandomUniform(),
        game.OPPONENT_2: player.RandomUniform()
    }

    #ランダムモンテカルロ木探索くん
    # players = {
    #     game.OWN_1: player.RandomMTS(100, 5),
    #     game.OWN_2: player.RandomMTS(100, 5),
    #     game.OPPONENT_1: player.RandomMTS(100, 5),
    #     game.OPPONENT_2: player.RandomMTS(100, 5)
    # }

def save_record(field, a1_best_moves, a2_best_moves, won):
    if DEBUG is True: return    #デバッグ時はファイル生成をしない
    
    X_value = np.array(field.value).reshape([field.width, field.height])
    X_own_status = np.array(field.own_status).reshape([-1, field.width, field.height])
    X_opponent_status = np.array(field.opponent_status).reshape([-1, field.width, field.height])
    X_own_points = np.array(field.own_points)
    X_opponent_points = np.array(field.opponent_points)
    X_a1_poss = np.array(field.a1_poss).reshape([-1, field.width, field.height])
    X_a2_poss = np.array(field.a2_poss).reshape([-1, field.width, field.height])
    X_a1_best_moves = np.array(a1_best_moves)
    X_a2_best_moves = np.array(a2_best_moves)

    now = int(round(time.time()*1000))
    path = os.path.join(OUTPUT_DIR, "{0}.npz".format(now))  #ファイル名の指定

    np.savez(path,              #対局データの保存
             X_value=X_value,
             X_own_status=X_own_status,
             X_opponent_status=X_opponent_status,
             X_own_points=X_own_points,
             X_opponent_points=X_opponent_points,
             X_a1_poss=X_a1_poss,
             X_a2_poss=X_a2_poss,
             X_a1_best_moves=X_a1_best_moves,
             X_a2_best_moves=X_a2_best_moves,
             won=won)

    try:    #きちんと読み込めるか確認
        np.load(path)
    except:
        os.remove(path)

    if DEBUG is True:   #対局データ中の各種データのサイズを確認
        print("value\n{}".format(len(X_value)))
        print("own status\n{}".format(len(X_own_status)))
        print("opponent status\n{}".format(len(X_opponent_status)))
        print("own points\n{}".format(len(X_own_points)))
        print("opponent points\n{}".format(len(X_opponent_points)))
        print("a1 positions\n{}".format(len(X_a1_poss)))
        print("a2 positions\n{}".format(len(X_a2_poss)))
        print("a1 best moves\n{}".format(len(X_a1_best_moves)))
        print("a2 best moves\n{}".format(len(X_a2_best_moves)))
        print("won\n{}".format(won))

player = (game.OWN_1, game.OWN_2, game.OPPONENT_1, game.OPPONENT_2) #エージェント識別用タプル（リストの変更できないヴァージョン）
a1_best_moves = [] #各局面における得点が最高になる手
a2_best_moves = []

for i in range(1, RECORD_NUM+1):
    if i % 50 == 0:
        print("game:", i)
    else:
        print("game:", i, end='\r')

    field = game.field()        #フィールド作成
    field.clear()   #フィールド情報をクリア
    field.create_rand_field()   #乱数で初期化

    for j in range(TURN):   #ターン数まで繰り返す   _はカウンタ変数を使わないという意味
        #全エージェントに一通り行動させる

        #フィールドの状態を確認（デバッグ用）
        if DEBUG is True:
            time.sleep(1)
            print() #一行空ける
            print("turn: {0}".format(j))
            # field.print_field()

        for turn in player: #各エージェントごとに行動させる
            hand = players[turn].select(field, turn)
            if DEBUG is True:
                print("player:{0} hand:{1}".format(turn, hand))
            if hand is not None:    #次の手があれば
                if field.check_team(turn) == game.OWN:
                    field.own_status.append(field.own_state)
                elif field.check_team(turn) == game.OPPONENT:
                    field.opponent_status.append(field.opponent_state)

                #プレーヤーの位置を盤面にして、管理しているリストに入れる
                if field.check_team(turn) == game.OWN:
                    if turn == game.OWN_1:
                        field.a1_poss.append(field.conv_agent_field([field.own_a1['x'], field.own_a1['y']]))
                    if turn == game.OWN_2:
                        field.a2_poss.append(field.conv_agent_field([field.own_a2['x'], field.own_a2['y']]))

                if field.check_team(turn) == game.OWN:
                    field.own_state = copy.deepcopy(field.move(field.own_state, turn, hand, True))    #deepcopyしないと参照渡しみたいになって、ひとつ変えると全部変わる
                elif field.check_team(turn) == game.OPPONENT:
                    field.opponent_state = copy.deepcopy(field.move(field.opponent_state, turn, hand, True))

                #その時点で最も点を得点を得られる手を探索
                best_move = field.best_move(field.own_state, field.opponent_state, turn)
                best_move = field.conv_hand_direction(turn, best_move)  #移動方向を表す数値に変換
                if DEBUG is True:
                    print("best move direction", best_move)
                if best_move is None: best_move = 0 #Noneだったら、とりあえず停留する
                if field.check_team(turn) == game.OWN:
                    if turn == game.OWN_1:
                        a1_best_moves.append(best_move)
                    if turn == game.OWN_2:
                        a2_best_moves.append(best_move)

                if DEBUG is True:
                    print("best move:", best_move)

            if DEBUG is True:
                field.print_field()

        '''
        自陣のエージェント二人の行動が終わった後に、own_stateの更新でいいかも。
        そうしないと、エージェントの位置と陣形で蓄積している局面数が合わない
        opponent_stateも、敵陣について同様。
        '''
        field.own_points.append(field.point(field.own_state))   #得点計算
        field.opponent_points.append(field.point(field.opponent_state)) #得点計算


    w = field.judge(field.own_state, field.opponent_state)      #勝者
    if w == game.OWN:   #勝ち1 負け0に対応させる
        won = 1
    elif w == game.OPPONENT:
        won = 0
    
    #終了時の盤面の保存
    field.own_status.append(field.own_state)
    field.opponent_status.append(field.opponent_state)

    save_record(field, a1_best_moves, a2_best_moves, won)  #対局データの保存
    if DEBUG is True:
        print()
        # print("field.own_status")
        # print(field.own_status)
        # print("field.opponent_status")
        # print(field.opponent_status)
        print("own status len:", len(field.own_status))
        print("opponent status len:", len(field.opponent_status))
        print("own points len", len(field.own_points))
        print("opponent points len", len(field.opponent_points))
        print("a1 best moves len", len(a1_best_moves))
        print("a2 best moves len", len(a2_best_moves))
        print("a1 poss len", len(field.a1_poss))
        print("a2 poss len", len(field.a2_poss))
        print()


print("created {} records".format(RECORD_NUM))