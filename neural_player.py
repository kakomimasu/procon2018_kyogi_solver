# coding: utf-8

import random
import copy
import numpy as np
import torch
import game
import player
import recently_hands

DEBUG = True

a1_recently_hands = recently_hands.Recently_hands()
a2_recently_hands = recently_hands.Recently_hands()

class DQNPlayer(player.Player):
    def __init__(self, model):
        super().__init__()  #親クラスのコンストラクタ
        self.model = model  #評価値生成に用いるモデルを設定
        if torch.cuda.is_available(): #GPUが使える場合は、モデルをGPUに転送
            self.model.cuda()

    def select(self, field, player):
        value = field.value
        own_state = field.own_state
        opponent_state = field.opponent_state
        pos = field.conv_agent_field([field.conv_turn_pos(player)['x'], field.conv_turn_pos(player)['y']])

        #大きさをフィールドの最大値に固定
        value = np.pad(value, [(0, game.MAX_BOARD_SIZE - field.value.shape[0]),(0, game.MAX_BOARD_SIZE - field.value.shape[1])], 'constant')
        own_state = np.pad(own_state, [(0, game.MAX_BOARD_SIZE - field.value.shape[0]),(0, game.MAX_BOARD_SIZE - field.value.shape[1])], 'constant')
        opponent_state = np.pad(opponent_state, [(0, game.MAX_BOARD_SIZE - field.value.shape[0]),(0, game.MAX_BOARD_SIZE - field.value.shape[1])], 'constant')
        pos = np.pad(pos, [(0, game.MAX_BOARD_SIZE - field.value.shape[0]),(0, game.MAX_BOARD_SIZE - field.value.shape[1])], 'constant')

        inputs = np.array([value, own_state, opponent_state, pos]).reshape(1, 4, game.MAX_BOARD_SIZE, game.MAX_BOARD_SIZE)  #入力データを結合させる　サイズは[バッチ, チャンネル, height, width]

        self.model.eval()   #推論モード
        inputs = torch.from_numpy(inputs).float()
        if torch.cuda.is_available(): #GPUを使える時
            inputs = torch.autograd.Variable(inputs.cuda())
        else:
            inputs = torch.autograd.Variable(inputs)

        out = self.model(inputs)
        if DEBUG is True:
            print(out)
        max_sorted = torch.sort(out, descending=True)   #価値が高い順に並べる
        sorted_directions = max_sorted[1][0].tolist()   #移動方向のみのリストを生成
        # print("sorted_direction", sorted_directions)

        for move_direction in sorted_directions:
            hand = field.conv_direction_hand(move_direction, own_state, opponent_state, [field.conv_turn_pos(player)['x'], field.conv_turn_pos(player)['y']])
            
            # 近づかないように
            if hand is not None:
                if player == game.OWN_2:
                    a1_x = field.own_a1['x']
                    a1_y = field.own_a1['y']
                    hand_x = hand[0]['x']
                    hand_y = hand[0]['y']

                    dis_x = hand_x - a1_x
                    dis_y = hand_y - a1_y

                    if dis_x < 2 or dis_y < 2:
                        continue

            # 停留をナシにする
            if move_direction == 0:
                continue

            if DEBUG is True:
                print("dict : ", move_direction, "hand : ", hand)
            if player == game.OWN_1:
                if a1_recently_hands.check(hand, times = 3) is False:
                    # print("continue hand", hand)
                    continue
            elif player == game.OWN_2:
                if a2_recently_hands.check(hand, times = 3) is False:
                    # print("continue hand", hand)
                    continue
            if hand is None: continue   #不可能な手だったら、次点の手について処理する

            if player == game.OWN_1:
                a1_recently_hands.put(hand)
                if DEBUG is True:
                    print("a1_recently_hands.hands", a1_recently_hands.hands)
            elif player == game.OWN_2:
                a2_recently_hands.put(hand)
                if DEBUG is True:
                    print("a2_recently_hands.hands", a2_recently_hands.hands)
            if DEBUG is True:
                print("hand", hand)
            return hand

        if DEBUG is True:
            print("player:", player, " put random hand")
        #continueしすぎて可能な手を全部スキップした（なんで？）
        hands = field.hands(field.own_state, field.opponent_state, player)  #可能な手
        if len(hands) == 0: #手がない
            hand = field.conv_direction_hand(0 , own_state, opponent_state, [field.conv_turn_pos(player)['x'], field.conv_turn_pos(player)['y']])   #停留
        else:
            choice = random.randrange(len(hands))   #ランダムに一つ選択
            hand = hands[choice]
        return hand

# class MinimaxDQNPlayer(player.Player):
#     def __init__(self, model):
#         super().__init__()  #親クラスのコンストラクタ
#         self.model = model  #評価値生成に用いるモデルを設定

#     def select(self, field, player):
#         pass