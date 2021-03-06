import pyxel
import numpy as np
import random as rd
import itertools as it
import pandas as pd
import os
from datetime import datetime as dt
import chainerrl
import json
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import AomushIAISetting

'''
TODO:
コード整理（特にクラス化）
追加課題：実際の操作に置き換えたときに、
'''

# 定数定義

# 動作方向
MOVE_LEFT = 0
MOVE_DOWN = 1
MOVE_UP = 2
MOVE_RIGHT = 3
NONE = 4

# ゲーム状態
GAME_TITLE = 0
GAME_PLAYING_USER = 1
GAME_RESULT = 2
GAME_RANK = 3
GAME_SETTING = 4
GAME_PLAYING_AI = 5

# 壁サイズ（サイズ分動作領域をシフトする）
WALL_SHIFT = 8

# 移動速度
# 初期値
MOVE_SPEED_DEFAULT = 10
# 最速値
MOVE_SPEED_FAST = 3

# 速度アップ閾値
MOVE_SPEED_UP_TH = 5


# 実行ファイルディレクトリ
FILE_DIR = os.path.dirname(__file__)
RESULT_FILE_PATH = "/data/result.csv"

# Reward Setting
REWARD_GET_FOOD = 1000
REWARD_TIME = 1
REWARD_END = 0
REWARD_NEAR = 1
REWARD_FAR = 1

class SnakeGameCore:
    def __init__(self):
        self.rankData_df = pd.DataFrame(
            columns=['rank', 'name', 'score', 'datetime'])

        #カラーローテーション用変数
        self.__colorCycle = 0

        # ランキングページ管理
        # 表示ページ
        self.__rankingPageNum = 0
        # ランキング登録数
        self.__rankingLastNum = len(self.rankData_df)
        # ランキングページに表示中の範囲
        self.__rankingStartNum = 0
        self.__rankingEndNum = 10

        # ゲットエフェクト用
        self.__getEffectList = []

        self.mainInit()
        self.__randBaseList = np.array(
            list(it.product(range(self.__fieldSize), range(self.__fieldSize))))
        self.__gameState = GAME_TITLE
    
    def run(self):
        pyxel.run(self.update, self.draw)

    def update(self):
        if self.__gameState == GAME_TITLE:
            self.gameTitle()
        elif self.__gameState == GAME_PLAYING_USER:
            self.gameMain(mode='user')
        elif self.__gameState == GAME_PLAYING_AI:
            self.gameMain(mode='ai')
        elif self.__gameState == GAME_RESULT:
            self.gameResult()
        elif self.__gameState == GAME_RANK:
            self.gameRank()
        else:
            pass

    def gameTitle(self):
        if pyxel.btnp(pyxel.KEY_ENTER):
            self.__gameState = GAME_PLAYING_USER
            self.mainInit()
        elif pyxel.btnp(pyxel.KEY_R):
            self.__rankingLastNum = len(self.rankData_df)
            self.__gameState = GAME_RANK
        elif pyxel.btnp(pyxel.KEY_A):
            self.__gameState = GAME_PLAYING_AI
            self.mainInit(mode='ai')

    def mainInit(self,mode='user'):
        self.__fieldSize = 16
        self.x = 0
        self.y = 0
        self.__moveStep = 0
        self.__moveX = 0
        self.__moveY = 0
        self.__moveState = MOVE_RIGHT
        self.__inputKey = NONE
        self.__moveSpeed = MOVE_SPEED_DEFAULT
        self.__snakeBody = [[0, 0], ]
        self.__score = 0
        self.__foodPos = [rd.randint(
            1, self.__fieldSize-1), rd.randint(1, self.__fieldSize-1)]
        self.__l1NormSnakeToFood = np.linalg.norm(np.array(self.__snakeBody[-1]) - np.array(self.__foodPos), ord=1)
        self.__l1NormSnakeToFoodBefore = self.__l1NormSnakeToFood
        # 学習用の終了フラグ（未終了で初期化）
        self.__mlDone = False
        self.__mlReward = 0

        if mode == 'ai':
            # 環境設定
            self.agent, paramDic = AomushIAISetting.AomushiModelRead(newModel=False)

    def gameMain(self, mode='user'):
        self.__moveStep += 1
        self.getEffect()

        # ここで最終入力を記録するが、遷移は更新周期が来てから。
        if mode == 'user':
            if pyxel.btnp(pyxel.KEY_LEFT):
                self.__inputKey = MOVE_LEFT
            elif pyxel.btnp(pyxel.KEY_RIGHT):
                self.__inputKey = MOVE_RIGHT
            elif pyxel.btnp(pyxel.KEY_UP):
                self.__inputKey = MOVE_UP
            elif pyxel.btnp(pyxel.KEY_DOWN):
                self.__inputKey = MOVE_DOWN

        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.__gameState = GAME_TITLE

        # 更新タイミングの判定、更新する場合は更新処理。
        if (self.__moveStep // self.__moveSpeed) >= 1:

            # ゲーム状態更新処理の呼び出し
            self.updateGame(mode=mode) #戻り値は使用しない

        else:
            pass

    # def inputKeyboad(self):
    #     # ここで最終入力を記録するが、遷移は更新周期が来てから。
    #     if pyxel.btnp(pyxel.KEY_LEFT):
    #         self.__inputKey = MOVE_LEFT
    #     elif pyxel.btnp(pyxel.KEY_RIGHT):
    #         self.__inputKey = MOVE_RIGHT
    #     elif pyxel.btnp(pyxel.KEY_UP):
    #         self.__inputKey = MOVE_UP
    #     elif pyxel.btnp(pyxel.KEY_DOWN):
    #         self.__inputKey = MOVE_DOWN

    def inputAgent(self):
        #agentからアクションをもらう
        obs = self.makeObs()
        obs = obs[np.newaxis,:,:]
        self.__inputKey= self.agent.act(obs)
        pass

    def updateGame(self, mode="user"):
        '''
        ゲーム状態を更新する。
        学習で、更新フレーム待ちなしでゲーム進行させるため、関数を独立
        '''

        # この行動で得られた報酬を記録するため、0で初期化。
        self.__mlReward = 0

        if mode=='ai':
            self.inputAgent()

        if self.__inputKey == MOVE_LEFT and self.__moveState != MOVE_RIGHT:
            self.__moveState = MOVE_LEFT
        elif self.__inputKey == MOVE_RIGHT and self.__moveState != MOVE_LEFT:
            self.__moveState = MOVE_RIGHT
        elif self.__inputKey == MOVE_UP and self.__moveState != MOVE_DOWN:
            self.__moveState = MOVE_UP
        elif self.__inputKey == MOVE_DOWN and self.__moveState != MOVE_UP:
            self.__moveState = MOVE_DOWN
        else:
            pass
        self.__inputKey = NONE

        if self.__moveState == MOVE_LEFT:
            self.__moveX = -1
            self.__moveY = 0
        elif self.__moveState == MOVE_RIGHT:
            self.__moveX = 1
            self.__moveY = 0
        elif self.__moveState == MOVE_UP:
            self.__moveX = 0
            self.__moveY = -1
        elif self.__moveState == MOVE_DOWN:
            self.__moveX = 0
            self.__moveY = 1

        self.__moveStep %= self.__moveSpeed
        self.x = (self.x+self.__moveX)
        self.y = (self.y+self.__moveY)

        # foodPosが2行1列に対して、bodyが1行2列なので、inでTrueにならない
        if [self.x, self.y] == self.__foodPos:
            # print('Eat'+str(self.__score))
        # if self.__snakeBody[-1] == self.__foodPos:
            self.nextFood()
            self.__score += 1
            self.getEffectAdd(self.__snakeBody[-1][0], self.__snakeBody[-1][1])
            if self.__score % MOVE_SPEED_UP_TH == 0 and self.__moveSpeed > MOVE_SPEED_FAST:
                self.__moveSpeed -= 1
            self.__mlReward += REWARD_GET_FOOD # 最長経路が256マスなので食べたら必ず0以上になるようにする
        else:
            self.__snakeBody.pop(0)
        
        # GameOver条件成立でリザルトへ遷移
        if (([self.x, self.y] in self.__snakeBody[:]) or
            (self.x < 0) or (self.x >= self.__fieldSize) or
                (self.y < 0) or (self.y >= self.__fieldSize)):
            if mode == "user":
                self.__gameState = GAME_RESULT
                # ランキング登録（名前登録画面を実装したら移す）
                self.CreateRanking()
            elif mode == 'ai':
                self.__gameState = GAME_RESULT
            else:
                self.__mlDone = True
                self.__mlReward = -REWARD_END

        self.__snakeBody.append([self.x, self.y])

    def CreateRanking(self):
        tempScore = {'rank': 0, 'name': 'NA', 'score': self.__score,
                     'datetime': dt.now().strftime('%Y-%m-%d %H:%M:%S')}
        self.rankData_df = self.rankData_df.append(
            tempScore, ignore_index=True)
        # スコアが大きい順でランキングを確定してrankに設定する
        _tempRank = self.rankData_df.score.rank(method='min', ascending=False)
        self.rankData_df['rank'] = _tempRank
        self.rankData_df['rank'] = self.rankData_df['rank'].astype('int64')
        # rankで昇順ソート（ここで、ランキング順に並ぶ）
        self.rankData_df = self.rankData_df.sort_values('rank')
        self.rankData_df = self.rankData_df.reset_index(drop=True)
        # 結果を保存
        self.rankData_df.to_csv(FILE_DIR+RESULT_FILE_PATH, index=False)

    def gameResult(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.__gameState = GAME_PLAYING_USER
            self.mainInit()
        elif pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.__gameState = GAME_TITLE
        elif pyxel.btnp(pyxel.KEY_A):
            self.__gameState = GAME_PLAYING_AI
            self.mainInit()

    def gameRank(self):
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.__gameState = GAME_TITLE
        elif pyxel.btnp(pyxel.KEY_LEFT):
            if self.__rankingPageNum > 0:
                self.__rankingPageNum -= 1
        elif pyxel.btnp(pyxel.KEY_RIGHT):
            # ランキングがあるページまで加算できる。（-1は10で割り切れるときに、次ページが出るのを防いでいる）
            if self.__rankingPageNum < ((self.__rankingLastNum-1)//10):
                self.__rankingPageNum += 1
        self.__rankingStartNum = self.__rankingPageNum * 10
        self.__rankingEndNum = self.__rankingStartNum + 10
        if self.__rankingEndNum > self.__rankingLastNum:
            self.__rankingEndNum = self.__rankingLastNum

    def draw(self):
        if self.__gameState == GAME_TITLE:
            pyxel.cls(0)
            pyxel.text(pyxel.width/2-12, pyxel.height/2-20, "AomushI", col=12)
            pyxel.text(pyxel.width/2-63, pyxel.height/2+20,
                       "Snakegame with Machine Learning.", col=10)
            pyxel.text( 10, pyxel.height-20, "HowTo -> Cursor Key: Snake move", col=7)
            pyxel.text( 10, pyxel.height-10, "Enter: GameStart   R: Ranking", col=7)

        elif self.__gameState == GAME_PLAYING_USER or self.__gameState == GAME_PLAYING_AI:
            pyxel.cls(1)
            for i in range(self.__fieldSize+2):
                for j in range(self.__fieldSize+2):
                    if (i == 0) or (i == self.__fieldSize+1) or (j == 0) or (j == self.__fieldSize+1):
                        pyxel.blt(i*8, j*8, 0, 8, 0, 8, 8)

            pyxel.bltm(0+WALL_SHIFT, 0+WALL_SHIFT, 0, 0, 0,
                       self.__fieldSize, self.__fieldSize)

            pyxel.blt(self.__snakeBody[-1][0]*8+WALL_SHIFT,
                      self.__snakeBody[-1][1]*8+WALL_SHIFT, 0, 8, 8, 8, 8, 0)
            for tempBody in self.__snakeBody[:-1]:
                pyxel.blt(tempBody[0]*8+WALL_SHIFT, tempBody[1]
                          * 8+WALL_SHIFT, 0, 0, 8, 8, 8, 0)

            for effect in self.__getEffectList:
                pyxel.circb((effect['x']+1)*8+4, (effect['y']+1)*8+4, effect['r'], effect['col'])
                if effect['r'] != 0:
                    pyxel.circb((effect['x']+1)*8+4, (effect['y']+1)*8+4, effect['r']-1, effect['col'])

            pyxel.blt(self.__foodPos[0]*8+WALL_SHIFT,
                      self.__foodPos[1]*8+WALL_SHIFT, 0, 0, 16, 8, 8, 0)
            pyxel.text(0, 145, "Score: " + str(self.__score), 6)
            pyxel.text(0, 153, "Speed: " + str(11 - self.__moveSpeed), 6)

        elif self.__gameState == GAME_RESULT:
            pyxel.cls(0)
            pyxel.text(pyxel.width/2-15, pyxel.height/2,
                       "Score: " + str(self.__score), 6)
            pyxel.text(30, pyxel.height/2+30,
                       "R: Restert   BS: Title", 6)

        elif self.__gameState == GAME_RANK:
            self.__colorCycle += 1
            if(self.__colorCycle >=16):
                self.__colorCycle=0
            pyxel.cls(0)
            pyxel.text(pyxel.width/2-15, 10, "Ranking", self.__colorCycle)
            pyxel.text(5, 30, 'Rank', 7)
            pyxel.text(30, 30, 'Score', 8)
            pyxel.text(60, 30, 'Date', 9)
            pyxel.text( 10, pyxel.height-10, "<-: Prev   ->: Next   BS: Title", col=7)

            #スコア表示
            for i, data in enumerate(self.rankData_df[self.__rankingStartNum:self.__rankingEndNum].
                iterrows()):
                # iterrows->data dataは(index, Series)のTulpeになっている
                pyxel.text(5, 30+(i+1)*10, str(data[1]['rank']), 6)
                pyxel.text(30, 30+(i+1)*10, str(data[1]['score']), 6)
                pyxel.text(60, 30+(i+1)*10, str(data[1]['datetime']), 6)

    def nextFood(self):
        # ↓で一致する座標だけTrueにできる
        # numpy.in1d(x.view(dtype='i,i').reshape(x.shape[0]),y.view(dtype='i,i').reshape(y.shape[0]))
        tempSnakeBody = np.array(self.__snakeBody, dtype='int32')
        # 全座標からスネークボディを除く座標を抽出
        tempFoodPos = self.__randBaseList[~np.in1d(self.__randBaseList.view(dtype='i,i').reshape(
            self.__randBaseList.shape[0]), tempSnakeBody.view(dtype='i,i').reshape(tempSnakeBody.shape[0]))]
        tempFoodPosReview = tempFoodPos.view(dtype='i,i').reshape(tempFoodPos.shape[0])
        # print(tempFoodPosReview.shape)
        self.__foodPos = list(np.random.choice(tempFoodPosReview))

    def getEffectAdd(self, x, y):
        self.__getEffectList.append({'x':x, 'y':y, 'r':0, 'col':8})

    def getEffect(self):
        for i, effect in enumerate(self.__getEffectList):
            effect['r'] += 1
            if effect['r'] >=50:
                self.__getEffectList.pop(i)

    #
    # 学習用メソッド
    #

    def reset(self):
        self.mainInit()
        self.__mlObs = np.zeros((16,16), dtype=int)
        self.__mlObs[0,0] = 1
        fp = np.array(self.__foodPos).T
        self.__mlObs[fp[0], fp[1]] = 3 # エサの座標を2に設定

        return self.__mlObs

    def step(self, action):
        self.__inputKey = action

        # 報酬の与え方をどう実装するか？
        # 報酬のルール
        '''
        餌をたべた(+++)：
        ゲームオーバーになった(---)：
        近づいた？(+)：
        時間経過(-)：
        '''

        self.updateGame(mode="ml")

        # Obs（状態）作成
        self.__mlObs = self.makeObs()

        self.__l1NormSnakeToFoodBefore = self.__l1NormSnakeToFood
        self.__l1NormSnakeToFood = np.linalg.norm(np.array(self.__snakeBody[-1]) - np.array(self.__foodPos), ord=1)

        # 時間経過による減算
        self.__mlReward -= REWARD_TIME

        # [Reward] 前回距離から今回距離が、近くなっていれば報酬1、離れていれば-1
        if self.__l1NormSnakeToFoodBefore > self.__l1NormSnakeToFood:
            self.__mlReward += REWARD_NEAR
        elif self.__l1NormSnakeToFoodBefore < self.__l1NormSnakeToFood:
            self.__mlReward -= REWARD_FAR

        # print(f'{self.__mlObs}')

        return self.__mlObs, self.__mlReward, self.__mlDone

    def makeObs(self):
        sb = np.array(self.__snakeBody).T
        # print(f'sb:{sb}')
        fp = np.array(self.__foodPos).T
        # print(f'fp:{fp}')
        if self.__mlDone == False:
            obs = np.zeros((16,16), dtype=int)
            obs[sb[0], sb[1]] = 2 # SnakeBodyの座標を2に設定
            obs[self.__snakeBody[-1][0], self.__snakeBody[-1][1]] = 1 # SnakeBodyHeadの座標を1に設定
            obs[fp[0], fp[1]] = 3 # エサの座標を3に設定
        else:
            obs = np.zeros((16,16), dtype=int)

        return obs


    def actionSample(self):
        action = np.array([0,1,2,3])
        return np.random.choice(action)

class SnakeGameApp(SnakeGameCore):

    def __init__(self):
        super().__init__()
        if (os.path.exists(FILE_DIR+RESULT_FILE_PATH)):
            self.rankData_df = pd.read_csv(
                FILE_DIR+RESULT_FILE_PATH, keep_default_na=False)
        else:
            # ランキングデータの空配列を用意
            self.rankData_df = pd.DataFrame(
                columns=['rank', 'name', 'score', 'datetime'])
            pass

        pyxel.init(144, 160, fps=60)
        pyxel.load(FILE_DIR + "/AomushI.pyxres")

if __name__ == "__main__":
    SG = SnakeGameApp()
    SG.run()