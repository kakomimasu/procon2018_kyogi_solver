# coding: utf-8

import random
import game
import neural_player
import player as basic_player
import network

import os
import torch
import torch.nn as nn

NEURAL_PLAYER = True    #True:機械学習 False:モンテカルロ木探索

def solve(field):
    '''
    今は、ランダムで返しているだけ
    各プレーヤーの移動方向を、相対座標で出力
    '''

    MODEL_PATH = './output/best_model.pth'
    if os.path.exists(MODEL_PATH):
        model = network.Network()
        model.load_state_dict(torch.load(MODEL_PATH, map_location=lambda storage, loc: storage))

    if NEURAL_PLAYER is True:   #機械学習
        player = neural_player.DQNPlayer(model)   # ***後で、きちんと書く！***
    elif NEURAL_PLAYER is False:    #モンテカルロ木探索
        player = basic_player.RandomMTS(100, 5)
    print("***************************************************************")
    own_a1_hand = player.select(field, game.OWN_1)
    own_a2_hand = player.select(field, game.OWN_2)

    # print("hands history")
    # print(len(neural_player.a1_recently_hands.hands))
    # print(neural_player.a1_recently_hands.hands)
    # print(len(neural_player.a2_recently_hands.hands))
    # print(neural_player.a2_recently_hands.hands)
    print("own_a1_hand", own_a1_hand)
    print("own_a2_hand", own_a2_hand)
    print("***************************************************************")

    # GUIとsolverで座標軸の扱い方が異なるから、逆にする

    buf = ""
    buf += str(own_a1_hand[0]["y"] - field.own_a1["y"])
    buf += ' '
    buf += str(own_a1_hand[0]["x"] - field.own_a1["x"])
    buf += ':'
    if own_a1_hand[1] is True:
        buf += '1'
    else:
        buf += '0'
    buf += ':'

    buf += str(own_a2_hand[0]["y"] - field.own_a2["y"])
    buf += ' '
    buf += str(own_a2_hand[0]["x"] - field.own_a2["x"])
    buf += ':'
    if own_a2_hand[1] is True:
        buf += '1'
    else:
        buf += '0'
    buf += ':'

    # buf = ""
    # num = 0
    # while num < 2:
    #     buf += str(random.randint(-1, 1))
    #     buf += ' '
    #     buf += str(random.randint(-1, 1))
    #     buf += ':'
    #     buf += '0'
    #     buf += ':'
    #     num += 1
    return buf

def solve2(field):
    '''
    今は、ランダムで返しているだけ
    各プレーヤーの移動方向を、相対座標で出力
    '''

    MODEL_PATH = './output/best_model.pth'
    if os.path.exists(MODEL_PATH):
        model = network.Network()
        model.load_state_dict(torch.load(MODEL_PATH, map_location=lambda storage, loc: storage))

    if NEURAL_PLAYER is True:   #機械学習
        player = neural_player.DQNPlayer(model)   # ***後で、きちんと書く！***
    elif NEURAL_PLAYER is False:    #モンテカルロ木探索
        player = basic_player.RandomMTS(100, 5)
    print("***************************************************************")
    own_a1_hand = player.select(field, game.OWN_1)
    own_a2_hand = player.select(field, game.OWN_2)
    
    print("★own_a1_hand", own_a1_hand)
    print("★own_a2_hand", own_a2_hand)

    hands = [None, None]
    if own_a1_hand is not None:
        hands[0] = {
            "x": own_a1_hand[0]["x"],
            "y": own_a1_hand[0]["y"]
        }
    if own_a2_hand is not None:
        hands[1] = {
            "x": own_a2_hand[0]["x"],
            "y": own_a2_hand[0]["y"]
        }
        
    return hands