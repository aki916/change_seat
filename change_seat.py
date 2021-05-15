import math
import random
from itertools import product

import pulp
import numpy as np


def optimize(
    num_student, 
    height, 
    width, 
    specific_constraint, 
    row_constraint, 
    far_constraint, 
    close_constraint
    ):

    # 問題の宣言
    problem = pulp.LpProblem(name='change_seat', sense=pulp.LpMaximize)

    # 変数の宣言
    x = {(sID, h, w) : 
        pulp.LpVariable(name=f'x_{sID}_{h}_{w}', cat='Binary') 
        for sID in range(num_student) for h in range(height) for w in range(width)
        }

    # 目的関数
    problem += pulp.lpSum(random.random()*x[sID, h, w] for sID in range(num_student) for h in range(height) for w in range(width))

    # 特定の場所の制約
    for sID, (h, w) in specific_constraint.items():
        problem.addConstraint(
            x[sID, h, w]  == 1, f"student{sID}_is_fixed_to_H{h}W{w}"
        )

    # 行の制約
    for sID, row_list in row_constraint.items():
        problem.addConstraint(
            pulp.lpSum(x[sID, h, w] for h in row_list for w in range(width)) == 1, f"student{sID}_rowList{row_list}"
        )   

    # 離す制約
    # for文の回す順番を変えれば高速化できる
    # far_constraint_list = [[],[(sID1, sID2), (sID1, sID2)], [], []]
    for (sID1, sID2), lb in far_constraint.items():
        for (h1, w1) in product(range(height), range(width)):
            for (h2, w2) in product(range(height), range(width)):
                if abs(h2-h1) + abs(w2-w1) <= lb-1:
                    problem.addConstraint(x[sID1,h1,w1]+x[sID2,h2,w2] <= 1, f"cannot_both_{sID1}_{h1}_{w1}to{sID2}_{h2}_{w2}")


    # for (sID1, sID2), lb in far_constraint.items():
    #     for (h1, w1) in product(range(height), range(width)):
    #         for (h2, w2) in product(range(h1, height), range(w1, width)):
    #             if h1==h2 and w1==w2:
    #                 continue
    #             if h2-h1 + w2-w1 <= lb-1:
    #                 problem.addConstraint(x[sID1,h1,w1]+x[sID2,h2,w2]+x[sID1,h2,w2]+x[sID2,h1,w1] <= 1)

    # 近づける制約
    alpha = {(sID1, sID2, i) : 
        pulp.LpVariable(name=f'a2_{sID1}_{sID2}_{i}', cat='Continuous', lowBound=0) 
        for (sID1, sID2) in close_constraint.keys() for i in range(2)
        }
    for (sID1, sID2), ub in close_constraint.items():
        height_difference = pulp.lpSum(
            (h+1) * (x[sID1, h, w] - x[sID2, h, w]) for h in range(height) for w in range(width)
        )
        width_difference = pulp.lpSum(
            (w+1) * (x[sID1, h, w] - x[sID2, h, w]) for h in range(height) for w in range(width)
        )
        problem.addConstraint(-alpha[sID1, sID2, 0] <= height_difference,    f"height_abs_{sID1}_close_1") 
        problem.addConstraint(height_difference     <= alpha[sID1, sID2, 0], f"height_abs_{sID1}_close_2") 
        problem.addConstraint(-alpha[sID1, sID2, 1] <= width_difference,     f"width_abs_{sID1}_close_1") 
        problem.addConstraint(width_difference      <= alpha[sID1, sID2, 1], f"width_abs_{sID1}_close_2") 
        problem.addConstraint(alpha[sID1, sID2,0] + alpha[sID1, sID2,1] <= ub, f"s{sID1}_s{sID2}_close_ub{ub}")

    #一つの席には一人だけ
    for h in range(height):
        for w in range(width):
            problem.addConstraint(
            pulp.lpSum(x[sID, h, w] for sID in range(num_student)) == 1, f"seat_limitation_H{h}W{w}"
            )

    #ユーザーは１つの席のみに入る
    for sID in range(num_student):
        problem.addConstraint(
            pulp.lpSum([x[sID, h, w] for h in range(height) for w in range(width)]) == 1, f"user_limitation_{sID}"
        )

    import time
    solver = pulp.PULP_CBC_CMD(msg=False, threads=1)
    status = problem.solve(solver)
    print(pulp.LpStatus[status])
    problem.writeLP('test.lp')
    # print("目的関数値 = {}".format(pulp.value(problem.objective)))

    # print()
    # for (sID1, sID2), lb in far_constraint.items():
    #     for h in range(height):
    #         for w in range(width):
    #             if math.isclose(x[sID1,h,w].value(), 1) > 0:
    #                 print(f'user {sID1} seat {h}-{w} : {pulp.value(x[sID1, h, w])}')
    #                 h0, w0 = h, w
    #             if math.isclose(x[sID2,h,w].value(), 1)> 0:
    #                 print(f'user {sID2} seat {h}-{w} : {pulp.value(x[sID2, h, w])}')
    #                 h1, w1 = h, w
    #     print(f"lb : {lb}")   

    # print()
    # for (sID1, sID2), ub in close_constraint.items():
    #     for h in range(height):
    #         for w in range(width):
    #             if math.isclose(x[sID1,h,w].value(), 1):
    #                 print(f'user {sID1} seat {h}-{w} : {pulp.value(x[sID1, h, w])}')
    #                 h0, w0 = h, w
    #             if math.isclose(x[sID2,h,w].value(), 1):
    #                 print(f'user {sID2} seat {h}-{w} : {pulp.value(x[sID2, h, w])}')
    #                 h1, w1 = h, w
    #     print(f"ub : {ub}")   
    #     print(alpha[sID1, sID2,0].value(), alpha[sID1, sID2,1].value())

    seat = [[-1 for _ in range(width)] for _ in range(height)]
    for h in range(height):
        for w in range(width):
            for sID in range(num_student):
                if math.isclose(x[sID,h,w].value(), 1):
                    # print(f"{h}-{w} | student : {sID}")
                    seat[h][w] = str(sID).zfill(2)

    from pprint import pprint
    pprint(seat)

def main():
    # ToDo : 柔軟な入力に対応(制約含む)
    # ToDo : Assertionの追加
    # ToDo : 出力の変更
    # ToDo : 乱数で変わる機能

    num_student = 42
    # seat = n
    height, width = 6, 7
    # W = np.zeros([seat,n])
    # key:studentID, value:(height, width)
    specific_constraint = {21:(2,3), 40:(3,5)}


    # key:studentID, value:list of int
    row_constraint = {
        1:[0], 2:[0], 4:[0], 5:[0], 
        6:[0,1], 9:[0,1], 13:[0,1], 15:[0,1],
        10:[4,5], 11:[5], 27:[5], 37:[5]
    }

    # key:tuple of studentID, value:int
    # far_constraint   = {( 5,  7) : 3, ( 1, 21) : 4, ( 5, 21) : 4, ( 7, 21) : 4, ( 8, 32) : 3, ( 32, 21) : 3, ( 8, 40) : 3}
    far_constraint   = {( 5,  7) : 3, ( 1, 21) : 2, ( 5, 21) : 4}
    # far_constraint   = {}
    close_constraint = {(12, 14) : 2, (39, 31) : 6, (15, 21) : 4}
    # close_constraint = {}


    optimize(
        num_student, 
        height, 
        width, 
        specific_constraint, 
        row_constraint, 
        far_constraint, 
        close_constraint
    )



if __name__ == '__main__':
    main()