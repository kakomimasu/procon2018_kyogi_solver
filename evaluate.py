# coding: utf-8

import os
import copy
import torch
import game
import player
import network
import neural_player

DEBUG = False
RANDOM_CREATE = True   #True:ランダムに着手 False:学習済みのモデルを使用

TURN = 60

MODEL_PATH = os.path.join(os.path.dirname(__file__), "./output/best_model.pth")       #最善モデルの保存パス

if RANDOM_CREATE is False:  #学習済みモデルを使用
    if os.path.exists(MODEL_PATH):
        model = network.Network()
        model.load_state_dict(torch.load(MODEL_PATH, map_location=lambda storage, loc: storage))
    else:
        raise Exception("学習済みモデルがありません")

def play(target, opponent, play_num):
    #入力
    #   * target:評価するプレーヤ（学習済みのモデルで評価値を推定する）
    #   * opponent:targetと対戦する相手
    #   * playnum:対戦回数

    # global game #このやり方だと、2回目で死ぬ

    #こうしないと、gameをローカル変数だと見なされてしまう
    #なんか書き方が汚いけれど、仕方がなかったんや...
    #直せそうなら直す
    import game

    players = {
        game.OWN_1: target,
        game.OWN_2: target,
        game.OPPONENT_1: opponent,
        game.OPPONENT_2: opponent
    }

    wons = 0    #勝利数

    player = (game.OWN_1, game.OWN_2, game.OPPONENT_1, game.OPPONENT_2) #エージェント識別用タプル（リストの変更できないヴァージョン）

    field = game.field()        #フィールド作成

    for i in range(play_num):   #{play_num}回対局を繰り返す
        print("game:", i, end='\r')

        field.clear()   #フィールド情報をクリア
        field.create_rand_field()   #乱数で初期化

        for _ in range(TURN):    #1試合あたり{TURN}ターンで打ち切る

            for turn in player: #各エージェントごとに行動させる
                hand = players[turn].select(field, turn)
                if DEBUG is True:
                    print("player:{0} hand:{1}".format(turn, hand))
                if hand is not None:    #次の手があれば
                    #陣形を、管理しているリストに入れる
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

                    #移動させる
                    if field.check_team(turn) == game.OWN:
                        field.own_state = field.move(field.own_state, turn, hand, True)
                        field.own_points.append(field.point(field.own_state))   #得点計算
                    elif field.check_team(turn) == game.OPPONENT:
                        field.opponent_state = field.move(field.opponent_state, turn, hand, True)
                        field.opponent_points.append(field.point(field.opponent_state)) #得点計算

        won = field.judge(field.own_state, field.opponent_state)      #勝者
        if won == game.OWN: wons += 1   #自陣の勝ちなら、勝ち数を1つ増やす

    return wons / play_num  #勝率

def evaluate_model(model, play_num):
    target = neural_player.DQNPlayer(model)
    if RANDOM_CREATE is False:
        opponent =  neural_player.DQNPlayer(model)
    elif RANDOM_CREATE is True:
        opponent = player.RandomUniform()   #本当はランダム打ちのモンテカルロ木探索にしたい
    return play(target, opponent, play_num)
