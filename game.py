# coding: utf-8

from enum import Enum
import numpy as np
import random
import copy
import load_field_file

DEBUG = False    #デバッグ時はTrue

class Team(Enum):
    OWN = 0
    OPPONENT = 1

class TileStatus(Enum):
    EMPTY = 0
    FILL = 1
    WALL = 2

OWN = 3         #自チーム
OPPONENT = -3   #敵チーム
OWN_1 = 1       #自チームのエージェント１
OWN_2 = 2
OPPONENT_1 = -1 #敵チームのエージェント１
OPPONENT_2 = -2

EXISTENCE = 1   #プレーヤーがいる
EMPTY = 0       #空のマス

MAX_BOARD_SIZE = 10

class field:
    def clear(self):    #フィールド情報をクリア
        self.width = 0   #縦
        self.height = 0  #横

        # 敵味方合わせた、陣地情報
        # 　フィールドのサイズに合わせて、どのフィールドが敵なのか、味方なのか、空なのかを保存
        # エージェントがどこにいるのかの位置情報も、フィールドの形に合わせて保存する
        # 各エージェントの位置をリストで保持する（不定形なので学習データには使用しない）
        # 　これは、まあ個別に保持するしかない
        # 個別のエージェントごとのエリアは必要か？？というか、そもそもそんな概念は無さそう

        self.own_a1, self.own_a2, self.opponent_a1, self.opponent_a2 = {'x':0, 'y':0}, {'x':0, 'y':0}, {'x':0, 'y':0}, {'x':0, 'y':0}   #エージェントの位置
        self.value = np.zeros([self.width, self.height], dtype=int)    #タイルの得点
        self.own_state = np.zeros([self.width, self.height], dtype=int)    #味方の陣形
        self.opponent_state = np.zeros([self.width, self.height], dtype=int)    #敵の陣形
        # ↑ここまで入

        self.own_status = [] #味方のターンごとの陣形を管理
        self.opponent_status = [] #敵のターンごとの陣形を管理
        self.a1_poss = []   #エージェント1の座標を管理
        self.a2_poss = []   #エージェント2の座標を管理
        self.own_points = []    #味方のターンごとに獲得した点数
        self.opponent_points = []   #敵のターンごとに獲得した点数

    def create_rand_field(self):    #フィールドを生成し、タイルに適当な点数を割り振る
        # sum_tile = random.randint(80, 88)  #タイルの数
        # self.width = random.randint(7, 12)  #縦の大きさをランダムに決定 80//12=7より、7が一辺の最小サイズ
        # while sum_tile // self.width > 12:  #heightが13以上だとルールに反しているから、12以下になるまで乱数生成
        #     self.width = random.randint(7, 12)
        # self.height = sum_tile // self.width    #横の大きさをランダムに決定 上のループで、ルールに適合するはず
        self.width = 10
        self.height = 10
        self.value = np.resize(self.value, (self.width, self.height))
        self.own_state = np.resize(self.own_state, (self.width, self.height))
        self.opponent_state = np.resize(self.opponent_state, (self.width, self.height))

        # 初期位置はランダム
        all_pos = []
        for x in range(self.width):
            for y in range(self.height):
                all_pos.append((x, y))
        random.shuffle(all_pos)

        a = all_pos.pop()
        self.own_a1['x'] = a[0]
        self.own_a1['y'] = a[1]

        a = all_pos.pop()
        self.own_a2['x'] = a[0]
        self.own_a2['y'] = a[1]

        a = all_pos.pop()
        self.opponent_a1['x'] = a[0]
        self.opponent_a1['y'] = a[1]

        a = all_pos.pop()
        self.opponent_a2['x'] = a[0]
        self.opponent_a2['y'] = a[1]    

        # bunkatsu = 0 #0:水平垂直 1:水平 2:垂直

        # #エージェントの位置を線対称にする
        # if bunkatsu == 0 or bunkatsu == 1:  #水平に線対称
        #     self.own_a2['x'] = self.width - self.own_a1['x'] - 1
        #     self.opponent_a2['x'] = self.width - self.opponent_a1['x'] - 1
        # if bunkatsu == 0 or bunkatsu == 2:  #垂直に線対称
        #     self.own_a2['y'] = self.height - self.own_a1['y'] - 1
        #     self.opponent_a2['y'] = self.height - self.opponent_a1['y'] - 1

        #エージェントの位置をstateに反映
        self.own_state[self.own_a1['x']][self.own_a1['y']] = EXISTENCE
        self.own_state[self.own_a2['x']][self.own_a2['y']] = EXISTENCE
        self.opponent_state[self.opponent_a1['x']][self.opponent_a1['y']] = EXISTENCE
        self.opponent_state[self.opponent_a2['x']][self.opponent_a2['y']] = EXISTENCE

        # 囲みマス
        self.value = np.array([
            [12, 3, 5, 3, 1, 1, 3, 5, 3,12],
            [ 3, 5, 7, 5, 3, 3, 5, 7, 5, 3],
            [ 5, 7,10, 7, 5, 5, 7,10, 7, 5],
            [ 3, 5, 7, 5, 3, 3, 5, 7, 5, 3],
            [ 1, 3, 5, 3,12,12, 3, 5, 3, 1],
            [ 1, 3, 5, 3,12,12, 3, 5, 3, 1],
            [ 3, 5, 7, 5, 3, 3, 5, 7, 5, 3],
            [ 5, 7,10, 7, 5, 5, 7,10, 7, 5],
            [ 3, 5, 7, 5, 3, 3, 5, 7, 5, 3],
            [12, 3, 5, 3, 1, 1, 3, 5, 3,12]
        ])

        # for i in range(0, self.width):
        #     for j in range(0, self.height):

        #         rand_value = random.randint(-10, 10*18)  #マイナスの点数を5%くらいに抑えるため
        #         if rand_value > 0:
        #             rand_value //= 18   #正の点数は、範囲に収まるように、9で割った商を代入

        #         self.value[i][j] = rand_value

        #         if bunkatsu == 0 or bunkatsu == 1:  #水平に線対称
        #             if self.width % 2 == 0:   #偶数
        #                 if i > self.width / 2 - 1:   #下半分
        #                     self.value[i][j] = self.value[self.width-i-1][j]
        #             else:
        #                 if i > self.width / 2:
        #                     self.value[i][j] = self.value[self.width-i-1][j]
        #         if bunkatsu == 0 or bunkatsu == 2:    #垂直に線対称
        #             if self.height % 2 == 0:  #偶数
        #                 if j > self.height / 2 - 1:  #右半分
        #                     self.value[i][j] = self.value[i][self.height-j-1]
        #             else:
        #                 if j > self.height / 2:
        #                     self.value[i][j] = self.value[i][self.height-j-1]

    def create_from_file(self, path):
        self.width, self.height, self.value, self.own_a1, self.own_a2 = load_field_file.load_field_file(path)
        self.own_state = np.resize(self.own_state, (self.width, self.height))
        self.opponent_state = np.resize(self.opponent_state, (self.width, self.height))
        self.own_state[self.own_a1['x']][self.own_a1['y']] = EXISTENCE
        self.own_state[self.own_a2['x']][self.own_a2['y']] = EXISTENCE

    def create_from_gui(self, value_nums, state_nums):
        self.clear()    #データをリセット

        self.width = int(value_nums[0][0].decode('ascii'))
        self.height = int(value_nums[0][1].decode('ascii'))

        self.value = np.resize(self.value, (self.width, self.height))
        self.own_state = np.resize(self.own_state, (self.width, self.height))
        self.opponent_state = np.resize(self.opponent_state, (self.width, self.height))

        for i in range(1, self.width+1):  #最初はフィールドサイズが入っているから、とばす
            for j in range(0, self.height):
                self.value[i-1][j] = int(value_nums[i][j].decode('ascii'))
                if int(state_nums[i][j].decode('ascii')) == 1:
                    self.own_state[i-1][j] = EXISTENCE
                elif int(state_nums[i][j].decode('ascii')) == 2:
                    self.opponent_state[i-1][j] = EXISTENCE

        #GUIとsolverで座標軸の扱い方が逆
        self.own_a1['x'] = int(value_nums[self.width+1][1].decode('ascii'))
        self.own_a1['y'] = int(value_nums[self.width+1][0].decode('ascii'))
        self.own_a2['x'] = int(value_nums[self.width+2][1].decode('ascii'))
        self.own_a2['y'] = int(value_nums[self.width+2][0].decode('ascii'))
        self.opponent_a1['x'] = int(value_nums[self.width+3][1].decode('ascii'))
        self.opponent_a1['y'] = int(value_nums[self.width+3][0].decode('ascii'))
        self.opponent_a2['x'] = int(value_nums[self.width+4][1].decode('ascii'))
        self.opponent_a2['y'] = int(value_nums[self.width+4][0].decode('ascii'))

    def print_field(self):
        print(" width:{0}\n height:{1}\n own_a1:{2}\n own_a2:{3}\n opponent_a1:{4}\n opponent_a2:{5}" \
            .format(self.width, self.height, self.own_a1, self.own_a2, self.opponent_a1, self.opponent_a2))
        print("value\n{0}".format(self.value))
        print("own state\n{0}".format(self.own_state))
        print("opponent state\n{0}".format(self.opponent_state))

    def can_move_pos(self, pos):    #その座標は操作可能か（範囲内か） posはリスト [x, y]
        if pos[0] < 0 or pos[0] >= self.width or pos[1] < 0 or pos[1] >= self.height:   #範囲外
            return False
        else:
            return True

    def player_exist(self, pos): #その座標にプレーヤがいるか posはリスト [x, y]
        x = pos[0]
        y = pos[1]

        if (x == self.own_a1['x'] and y == self.own_a1['y']) \
            or (x == self.own_a2['x'] and y == self.own_a2['y']) \
            or (x == self.opponent_a1['x'] and y == self.opponent_a1['y']) \
            or (x == self.opponent_a2['x'] and y == self.opponent_a2['y']):
            return True
        else:
            return False

    def can_move(self, **player):    #エージェントが移動可能か否か
        if player is None:
            return field.can_move(self.own_a1) or field.can_move(self.own_a2) \
                    or field.can_move(self.opponent_a1) or field.can_move(self.opponent_a2) #誰かがTrueならTrue

        for i in range(-1, 2):  #width -1から1
            for j in range(-1, 2):  #height -1から1
                if self.can_move_pos([player['x'] + i, player['y'] + j]) is False:    #範囲外
                    continue
                return True
        return False

    def hands(self, own_state, opponent_state, player):  #可能な手を一覧 移動可能な位置と、タイルをひっくり返す
        #playerは、一番上にあるエージェントの識別定数でくる conv_turn_posで座標に変換
        hands = []  #可能な移動位置
        #hand = [座標, ひっくり返すか（Trueならひっくり返す Falseなら移動）]　というデータ形式

        x = self.conv_turn_pos(player)['x'] #座標に変換
        y = self.conv_turn_pos(player)['y']

        for i in range(-1, 2):  #width -1から1
            for j in range(-1, 2):  #height -1から1
                #print("x+i:{} y+j:{}".format(x+i, y+j))
                if self.can_move_pos([x + i, y + j]) is False:  #範囲外
                    continue
                elif own_state[x + i][y + j] == EMPTY and opponent_state[x + i][y + j] == EMPTY:  #どちらの陣でもない
                    hands.append([{'x':x+i, 'y':y+j}, False])    #移動
                else:   #どちらかの陣地
                    if i == 0 and j == 0:   #自分のいる場所
                        hands.append([{'x':x+i, 'y':y+j} , False]) #移動
                    else:   #隣り合った場所
                        if self.player_exist([x + i, y + j]) is True:  #他のプレーヤーがいる
                            continue
                        else:   #プレーヤーがいない
                            hands.append([{'x':x+i, 'y':y+j} , False]) #移動
                            if (player == OWN_1 or player == OWN_2) and self.value[x+i][y+j] < 0: #自陣で、タイル得点がマイナス
                                hands.append([{'x':x+i, 'y':y+j} , True]) #ひっくり返す
        
        if DEBUG is True:
            print("player:{0} hands:{1}".format(player, hands))

        return hands

    def conv_turn_pos(self, turn):  #ターン（エージェント）が入力されると、座標が辞書で返る
        if   turn == OWN_1: return self.own_a1
        elif turn == OWN_2: return self.own_a2
        elif turn == OPPONENT_1: return self.opponent_a1
        elif turn == OPPONENT_2: return self.opponent_a2

    def move(self, state, player, hand, overwrite = False):   #handはリスト hand[0]は辞書 overwriteがFalseなら、破壊的操作をしない
        hand_x = hand[0]['x']
        hand_y = hand[0]['y']
        player_x = self.conv_turn_pos(player)['x']
        player_y = self.conv_turn_pos(player)['y']

        my_state = copy.deepcopy(state)

        if self.can_move_pos([hand_x, hand_y]) is False: #範囲内か確認
            raise Exception("Can't move!")
        #停留なら、何もしない
        if hand_x == player_x and hand_y == player_y:
            return my_state
        if hand[1] is False:    #移動なら
            if overwrite is False:  #書き換えない
                my_state[hand_x][hand_y] = EXISTENCE  #移動先にタイルを置く
            if overwrite is True:   #実際に移動
                state[hand_x][hand_y] = EXISTENCE  #移動先にタイルを置く
                self.conv_turn_pos(player)['x'] = hand_x  #エージェントの移動
                self.conv_turn_pos(player)['y'] = hand_y
        else:
            if overwrite is False:  #書き換えない
                my_state[hand_x][hand_y] = EMPTY   #タイルを除去
            else:   #書き換え
                state[hand_x][hand_y] = EMPTY   #タイルを除去

        if overwrite is False:  #書き換えない
            return my_state
        else:
            return state

    def area_score(self, state):
        score = 0   #領域ポイント
        # height個の要素のリストがwidth個入ったリストができる
        is_searched = [[False for i in range(self.height)] for j in range(self.width)]  #探索済みか
        is_end = [[False for i in range(self.height)] for j in range(self.width)]   #端か

        #端の部分はTrueを代入
        for x in range(self.width):
            for y in range(self.height):
                if x == 0 or y == 0 or x == self.width-1 or y == self.height-1:
                    is_end[x][y] = True

        for x in range(self.width):
            for y in range(self.height):
                if state[x][y] == EMPTY:    #自チームのタイルではない
                    if is_searched[x][y] is False:  #未探索
                        _reach_end = False  #まだ探索が終了していない
                        sscore = 0
                        sscore, _reach_end = self.count_area_score(state, [x, y], is_searched, is_end, _reach_end, sscore)
                        if _reach_end is False:
                            score += sscore

        return score

    def count_area_score(self, state, pos, is_searched, is_end, _reach_end, sscore): #posは[x, y]
        x = pos[0]
        y = pos[1]

        if state[x][y] == EXISTENCE or is_searched[x][y] == True: #自陣 or すでに探索済み
            return sscore, _reach_end
        is_searched[x][y] = True    #探索済みにする
        sscore += abs(self.value[x][y])   #タイルポイントの絶対値を代入
        if is_end[x][y] is True:    #端まで達したら、探索終了
            _reach_end = True

        if x > 0:
            s, r = self.count_area_score(state, [x-1,y], is_searched, is_end, _reach_end, sscore)
            sscore = s
            _reach_end = r
        if x < self.width-1:
            s,r = self.count_area_score(state, [x+1,y], is_searched, is_end, _reach_end, sscore)
            sscore = s
            _reach_end = r
        if y > 0:
            s, r = self.count_area_score(state, [x,y-1], is_searched, is_end, _reach_end, sscore)
            sscore = s
            _reach_end = r
        if y < self.height-1:
            s, r = self.count_area_score(state, [x,y+1], is_searched, is_end, _reach_end, sscore)
            sscore = s
            _reach_end = r

        return sscore, _reach_end

    def judge(self, own_state, opponent_state):
        own_tile, own_territory = 0, 0
        opponent_tile, opponent_territory = 0, 0

        for i in range(0, self.width):
            for j in range(0, self.height):
                if own_state[i][j] == EXISTENCE: own_tile += self.value[i][j]    #塗りつぶし済みのタイルの点数を集計
                if opponent_state[i][j] == EXISTENCE: opponent_tile += self.value[i][j]

        own_territory = self.area_score(own_state)
        opponent_territory = self.area_score(opponent_state)

        if own_tile + own_territory > opponent_tile + opponent_territory:
            return OWN
        else:
            return OPPONENT

    def point(self, state): #タイルポイントと領域ポイントの合算を返す
        tile, territory = 0, 0

        for i in range(0, self.width):
            for j in range(0, self.height):
                if state[i][j] == EXISTENCE: tile += self.value[i][j]    #塗りつぶし済みのタイルの点数を集計

        territory = self.area_score(state)

        return tile + territory

    def check_team(self, player):   #エージェントが属すチームを返す
        if player > 0:
            return OWN
        if player < 0:
            return OPPONENT

    def conv_agent_field(self, pos): #エージェントの位置を盤面で表す pos リスト[x,y]
        x = pos[0]
        y = pos[1]

        pos_field = np.zeros([self.width, self.height], dtype=int)  #全部0の盤面
        pos_field[x][y] = EXISTENCE

        return pos_field

    def best_move(self, own_state, opponent_state, player): #その時点で最も点を得られる手を出力
        move_point = {} #手とその時の得点を管理する辞書
        hands = self.hands(own_state, opponent_state, player) #可能な手を全てリストアップ

        for hand in hands:
            #元の盤面が書き換わるのを防ぐ
            my_own_state = copy.deepcopy(own_state)
            my_opponent_state = copy.deepcopy(opponent_state)

            if self.check_team(player) == OWN:
                my_own_state = self.move(my_own_state, player, hand, False)
                move_point[tuple(hand[0].items())] = self.point(my_own_state) #得点計算
            elif self.check_team(player) == OPPONENT:
                my_opponent_state = self.move(my_opponent_state, player, hand, False)
                move_point[tuple(hand[0].items())] = self.point(my_opponent_state)

        max_sorted = sorted(move_point.items(), key=lambda x: x[1], reverse=True) #リストに変換して得点の降順にソート
        return [dict(max_sorted[0][0]), max_sorted[0][1]] #得られる得点が最大の手 辞書型に変換済み

    def conv_hand_direction(self, turn, hand):    #エージェントの位置と手から、移動方向を番号で表す
        agent_x = self.conv_turn_pos(turn)['x'] #座標に変換
        agent_y = self.conv_turn_pos(turn)['y']

        hand_x = hand[0]['x']
        hand_y = hand[0]['y']

        dis_x = hand_x - agent_x
        dis_y = hand_y - agent_y

        if dis_x == 0 and dis_y == 0:       #停留
            return 0
        elif dis_x == -1 and dis_y == 0:    #上
            return 1
        elif dis_x == -1 and dis_y == 1:    #右上
            return 2
        elif dis_x == 0 and dis_y == 1:     #右
            return 3
        elif dis_x == 1 and dis_y == 1:     #右下
            return 4
        elif dis_x == 1 and dis_y == 0:     #下
            return 5
        elif dis_x == 1 and dis_y == -1:    #左下
            return 6
        elif dis_x == 0 and dis_y == -1:    #左
            return 7
        elif dis_x == -1 and dis_y == -1:   #左上
            return 8
        else:                               #異常値
            if DEBUG is True:
                print("conv hand to bad direction")
            return None

    def conv_direction_hand(self, direction, own_state, opponent_state, agent_pos):
        '''
        移動方向の番号から、その方向に対して可能な手を抽出
        1つなら、そのまま返す
        複数なら、自陣ならひっくり返しではなく移動を選ぶ
        '''
        hands = []  #着手可能な手

        x = agent_pos[0]
        y = agent_pos[1]

        if direction == 0:      #停留
            dis_x = 0
            dis_y = 0
        elif direction == 1:    #上
            dis_x = -1
            dis_y = 0
        elif direction == 2:    #右上
            dis_x = -1
            dis_y = 1
        elif direction == 3:    #右
            dis_x = 0
            dis_y = 1
        elif direction == 4:    #右下
            dis_x = 1
            dis_y = 1
        elif direction == 5:    #下
            dis_x = 1
            dis_y = 0
        elif direction == 6:    #左下
            dis_x = 1
            dis_y = -1
        elif direction == 7:    #左
            dis_x = 0
            dis_y = -1
        elif direction == 8:    #左上
            dis_x = -1
            dis_y = -1

        target_x = x + dis_x
        target_y = y + dis_y

        if self.can_move_pos([target_x, target_y]) is False: #範囲内か確認
            return None
        elif direction != 0:    #停留でないとき
            if self.player_exist([target_x, target_y]) is True: #すでにプレーヤーがいる
                return None
        if own_state[target_x][target_y] == EMPTY and opponent_state[target_x][target_y] == EMPTY:    #空
            hands.append([{'x': target_x, 'y':target_y}, False])    #目的の位置に移動
        elif own_state[target_x][target_y] == EMPTY and opponent_state[target_x][target_y] == EXISTENCE:    #敵の陣地
            hands.append([{'x': target_x, 'y':target_y}, True])    #除去
        elif own_state[target_x][target_y] == EXISTENCE and opponent_state[target_x][target_y] == EMPTY:    #味方の陣地
            hands.append([{'x': target_x, 'y':target_y}, False])    #移動
            hands.append([{'x': target_x, 'y':target_y}, True])    #除去 もはや入れる必要はないが、一応
        else:   #異常値
            if DEBUG is True:
                print("conv direction to bad hand")
            return None

        return hands[0]

'''
# for check
field = field()
field.create_rand_field()
field.print_field()
'''
'''
# for check
field = field()
field.create_from_file("shape_info.txt")
field.print_field()
'''