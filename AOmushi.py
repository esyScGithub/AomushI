# -*- coding=utf-8 -*-

import pyxel
import numpy as np
import random as rd
import itertools as it
import csv
import os

'''
TODO:
スコア保存追加
ランキング閲覧
コード整理（特にクラス化）

'''


# Define Constant Value
STEP = 0.1
STOP = 0.0
MOVE_LEFT = 0
MOVE_DOWN = 1
MOVE_UP = 2
MOVE_RIGHT = 3
NONE = 4

GAME_TITLE = 0
GAME_PLAYING = 1
GAME_RESULT = 2

WALL_SHIFT = 8

FILE_DIR = os.path.dirname(__file__)


class App:

    def __init__(self):
        with open(FILE_DIR + '/data/result.csv') as f:
            resultFile = csv.reader(f)
            for l in resultFile:
                # TODO CSV読み出し作る。ファイルが無いときはファイル作る。できれば、新規作成時はそのメッセージだす。
                pass
        pyxel.init(144, 160, fps=60)
        self.mainInit()
        self.__randBaseList = np.array(
            list(it.product(range(self.__fieldSize), range(self.__fieldSize))))
        self.__gameState = GAME_TITLE
        pyxel.load(FILE_DIR + "/AOmushi.pyxres")
        pyxel.run(self.update, self.draw)

    def update(self):
        if self.__gameState == GAME_TITLE:
            self.gameTitle()
        elif self.__gameState == GAME_PLAYING:
            self.gameMain()
        elif self.__gameState == GAME_RESULT:
            self.gameResult()
        else:
            pass

    def gameTitle(self):
        if pyxel.btnp(pyxel.KEY_ENTER):
            self.__gameState = GAME_PLAYING
            self.mainInit()

    def mainInit(self):
        self.__fieldSize = 16
        self.x = 0
        self.y = 0
        self.__moveStep = 0
        self.__moveX = STOP
        self.__moveY = STOP
        self.__moveState = MOVE_RIGHT
        self.__inputKey = NONE
        self.__moveSpeed = 7
        self.__snakeBody = [[0, 0], ]
        self.__score = 0
        self.__foodPos = [rd.randint(
            0, self.__fieldSize-1), rd.randint(0, self.__fieldSize-1)]

    def gameMain(self):
        self.__moveStep += 1

        # ここで最終入力を記録するが、遷移は更新周期が来てから。
        if pyxel.btnp(pyxel.KEY_LEFT) and self.__moveState != MOVE_RIGHT:
            self.__inputKey = MOVE_LEFT
        elif pyxel.btnp(pyxel.KEY_RIGHT) and self.__moveState != MOVE_LEFT:
            self.__inputKey = MOVE_RIGHT
        elif pyxel.btnp(pyxel.KEY_UP) and self.__moveState != MOVE_DOWN:
            self.__inputKey = MOVE_UP
        elif pyxel.btnp(pyxel.KEY_DOWN) and self.__moveState != MOVE_UP:
            self.__inputKey = MOVE_DOWN

        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.__gameState = GAME_TITLE

        # 更新タイミングの判定、更新する場合は更新処理。
        if (self.__moveStep // self.__moveSpeed) >= 1:
            if self.__inputKey == MOVE_LEFT:
                self.__moveState = MOVE_LEFT
            elif self.__inputKey == MOVE_RIGHT:
                self.__moveState = MOVE_RIGHT
            elif self.__inputKey == MOVE_UP:
                self.__moveState = MOVE_UP
            elif self.__inputKey == MOVE_DOWN:
                self.__moveState = MOVE_DOWN
            else:
                pass
            self.__inputKey = NONE

            if self.__moveState == MOVE_LEFT:
                self.__moveX = -1
                self.__moveY = STOP
            elif self.__moveState == MOVE_RIGHT:
                self.__moveX = 1
                self.__moveY = STOP
            elif self.__moveState == MOVE_UP:
                self.__moveX = STOP
                self.__moveY = -1
            elif self.__moveState == MOVE_DOWN:
                self.__moveX = STOP
                self.__moveY = 1

            self.__moveStep %= self.__moveSpeed
            self.x = (self.x+self.__moveX)
            self.y = (self.y+self.__moveY)

            if (([self.x, self.y] in self.__snakeBody[1:]) or
                (self.x < 0) or (self.x >= self.__fieldSize) or
                    (self.y < 0) or (self.y >= self.__fieldSize)):
                self.__gameState = GAME_RESULT

            self.__snakeBody.append([self.x, self.y])

            # foodPosが2行1列に対して、bodyが1行2列なので、inでTrueにならない
            if self.__snakeBody[-1] == self.__foodPos:
                self.nextFood()
                self.__score += 1
            else:
                self.__snakeBody.pop(0)

        else:
            pass

    def gameResult(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.__gameState = GAME_PLAYING
            self.mainInit()
        elif pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.__gameState = GAME_TITLE

    def draw(self):
        if self.__gameState == GAME_TITLE:
            pyxel.cls(0)
            pyxel.text(pyxel.width/2-12, pyxel.height/2-20, "AOmushi", col=12)
            pyxel.text(pyxel.width/2-63, pyxel.height/2+20,
                       "Snakegame with Machine Learning.", col=10)

        elif self.__gameState == GAME_PLAYING:
            pyxel.cls(1)
            for i in range(self.__fieldSize+2):
                for j in range(self.__fieldSize+2):
                    if (i == 0) or (i == self.__fieldSize+1) or (j == 0) or (j == self.__fieldSize+1):
                        pyxel.blt(i*8, j*8, 0, 8, 0, 8, 8)

            pyxel.bltm(0+WALL_SHIFT, 0+WALL_SHIFT, 0, 0, 0,
                       self.__fieldSize, self.__fieldSize)

            pyxel.blt(self.__snakeBody[-1][0]*8+WALL_SHIFT, self.__snakeBody[-1][1]*8+WALL_SHIFT, 0,8,8, 8,8,0)
            for tempBody in self.__snakeBody[:-1]:
                pyxel.blt(tempBody[0]*8+WALL_SHIFT, tempBody[1]
                          * 8+WALL_SHIFT, 0, 0, 8, 8, 8, 0)

            pyxel.blt(self.__foodPos[0]*8+WALL_SHIFT,
                      self.__foodPos[1]*8+WALL_SHIFT, 0, 0, 16, 8, 8, 0)
            pyxel.text(0, 145, "Score: " + str(self.__score), 6)

        elif self.__gameState == GAME_RESULT:
            pyxel.cls(0)
            pyxel.text(pyxel.width/2-15, pyxel.height/2,
                       "Score: " + str(self.__score), 6)
            pyxel.text(10, pyxel.height/2+30,
                       "Restert: R, Title: BackSpace", 6)

    def nextFood(self):
        # ↓で一致する座標だけTrueにできる
        # numpy.in1d(x.view(dtype='i,i').reshape(x.shape[0]),y.view(dtype='i,i').reshape(y.shape[0]))
        tempSnakeBody = np.array(self.__snakeBody, dtype='int32')
        # 全座標からスネークボディを除く座標を抽出
        tempFoodPos = self.__randBaseList[~np.in1d(self.__randBaseList.view(dtype='i,i').reshape(
            self.__randBaseList.shape[0]), tempSnakeBody.view(dtype='i,i').reshape(tempSnakeBody.shape[0]))]
        tempFoodPosReview = tempFoodPos.view(
            dtype='i,i').reshape(tempFoodPos.shape[0])
        self.__foodPos = list(np.random.choice(tempFoodPosReview))


if __name__ == "__main__":
    App()