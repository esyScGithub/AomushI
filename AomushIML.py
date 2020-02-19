import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import numpy as np
from matplotlib import pyplot
import pickle
import AomushI as ai
import time
import os
import datetime
import pathlib
import json
import pandas as pd
import AomushIAISetting


'''
TODO 
・agentの保存タイミングを増やす（回数or特定のスコア達成時）
・学習パラメータを自動で調整する

'''

# コンフィグ定義
AGENT_SAVE_STEP = 1000
PRINT_EPISODE_STEP = 50

def AomushILearning(agent, paramDic, currentDir):
    # 実行時間から保存用のディレクトリを作成
    dirPath = currentDir + '/test_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    pathlib.Path(dirPath).mkdir()

    st = time.time()

    # 環境名を指定して、環境インスタンスを作成
    aomushiEnv = ai.SnakeGameCore()
    # # aomushiEnv.run()

    # 環境を初期化（戻り値で、初期状態の観測データobservationが取得できる）
    obs = aomushiEnv.reset()

    # 初期値設定
    rewards = []
    bestReward = -100
    bestData = []
    bestAgent = agent
    saveCount = 0
    tempSumReword = 0
    averageReword = 0

    # パラメータ、エピソード数をJSONに保存
    with open(dirPath + '/param.json', 'w') as f:
        json.dump(paramDic, f)

    for i in range(1, paramDic['n_episodes'] + 1):
        obs = aomushiEnv.reset()
        tempBestData =[]
        tempBestData.append(obs)
        reward = 0
        done = False
        R = 0  # return (sum of rewards)
        t = 0   # time step
        while not done and t < paramDic['max_episode_len']:
            action = agent.act_and_train(obs, reward)
            obs, reward, done = aomushiEnv.step(action)
            R += reward
            t += 1
            # 過程を保存する
            tempBestData.append(obs)

        if i % PRINT_EPISODE_STEP == 0:
            print('episode:', i,
                'R:', R,
                'statistics:', agent.get_statistics())

        agent.stop_episode_and_train(obs, reward, done)

        if bestReward < R:
            bestReward = R
            bestData = tempBestData
            bestAgent = agent

        if i % AGENT_SAVE_STEP == 0:
            agent.save(dirPath + '/' + str(i))
        
        tempSumReword += R

        rewards.append(R)
    # aomushiEnv.render()

    # 最高記録のプレイデータを保存
    with open(dirPath + '/bestPlayData.bin', 'wb') as f:
        pickle.dump(bestData, f)

    # すべての報酬結果を保存
    # with open(dirPath + '/resultReward.bin', 'wb') as f:
    #     pickle.dump(rewards, f)
    pdRewords = pd.Series(rewards)
    pdRewords.to_csv(dirPath + '/resultReward.csv')

    # 平均報酬の算出
    averageReword = tempSumReword / i

    # 最高記録、最終学習のAgentを保存
    bestAgent.save(dirPath + '/bestAgent')
    agent.save(dirPath + '/lastAgent')

    # 報酬をグラフ化
    pyplot.figure()
    pyplot.plot(range(len(rewards)),rewards)
    # pyplot.show()
    pyplot.savefig(dirPath + '/Result.png')

    # 学習結果のサマリを出力
    with open(dirPath + '/summary.txt', 'w') as f:
        f.write(str(paramDic) + '\n')
        f.write(str(bestReward) + '\n')
        f.write(f'ProcessingTime: {time.time()-st}')


    print(f'Finished. {time.time()-st}')

    return bestReward, averageReword, dirPath

if __name__ == "__main__":
    AomushIAISetting.AomushILarningMain()