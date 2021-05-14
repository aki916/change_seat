import pulp
import random
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
    problem = pulp.LpProblem(name='change seat', sense=pulp.LpMaximize)

    # 変数の宣言
    x = {(sID, h, w) : 
        pulp.LpVariable(name=f'x_{sID}_{h}_{w}', cat='Binary') 
        for sID in range(num_student) for h in range(height) for w in range(width)
        }

    # 目的関数
    problem += pulp.lpSum(x[sID, h, w] for sID in range(num_student) for h in range(height) for w in range(width))

    # 特定の場所の制約
    for sID, (h, w) in specific_constraint.items():
        problem.addConstraint(
            x[sID, h, w]  == 1, f"student{sID}_is_fixed_to_H{h}W{w}"
        )

    # 行の制約
    for sID, row_list in row_constraint.items():
        print(sID, row_list)
        problem.addConstraint(
            pulp.lpSum(x[sID, h, w] for h in row_list for w in range(width)) == 1, f"student{sID}_rowList{row_list}"
        )   

    # 離す制約
    alpha1 = {(i,j) : 
        pulp.LpVariable(name=f'a1_{i}_{j}', cat='Integer', lowBound=0) 
        for i in range(len(far_constraint)) for j in range(2)
        }

    c = 0
    for (sID1, sID2), lb in far_constraint.items():
        height_difference = pulp.lpSum(
            h * (x[sID1, h, w] - x[sID2, h, w]) for h in range(height) for w in range(width)
        )
        width_difference = pulp.lpSum(
            w * (x[sID1, h, w] - x[sID2, h, w]) for h in range(height) for w in range(width)
        )
        problem.addConstraint(-alpha1[c,0] <= height_difference <= alpha1[c,0], f"height_abs_{c}_far") 
        problem.addConstraint(-alpha1[c,1] <= width_difference  <= alpha1[c,1], f"width_abs_{c}_far") 
        problem.addConstraint(alpha1[c,0] + alpha1[c,1] >= lb, f"s{sID1}_s{sID2}_far_lb{lb}")
        c += 1

    # 近づける制約
    alpha2 = {(i,j) : 
        pulp.LpVariable(name=f'a2_{i}_{j}', cat='Integer', lowBound=0) 
        for i in range(len(close_constraint)) for j in range(2)
        }

    c = 0
    for (sID1, sID2), ub in close_constraint.items():
        height_difference = pulp.lpSum(
            h * (x[sID1, h, w] - x[sID2, h, w]) for h in range(height) for w in range(width)
        )
        width_difference = pulp.lpSum(
            w * (x[sID1, h, w] - x[sID2, h, w]) for h in range(height) for w in range(width)
        )
        problem.addConstraint(-alpha2[c,0] <= height_difference <= alpha2[c,0], f"height_abs_{c}_close") 
        problem.addConstraint(-alpha2[c,1] <= width_difference  <= alpha2[c,1], f"width_abs_{c}_close") 
        problem.addConstraint(alpha2[c,0] + alpha2[c,1] <= ub, f"s{sID1}_s{sID2}_close_ub{lb}")
        c += 1

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


    status = problem.solve()
    print(pulp.LpStatus[status])
    # print("目的関数値 = {}".format(pulp.value(problem.objective)))


    # for sID in range(num_student):
    #     for h in range(height):
    #         for w in range(width):
    #             if pulp.value(x[sID, h, w]) > 0:
    #                 print(f'user {sID} seat {h}-{w} : {pulp.value(x[sID, h, w])}')


def main():
    num_student = 80
    # seat = n
    height, width = 8, 10
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
    far_constraint = {(5,7):3, (1,21):2}
    close_constraint = {(12,14):2, (39,31):1}

    #値を入れる
    # for i in range(seat):
    #     for j in range(n):
    #         W[i,j] = random.random()

    # 各行を割合に変換
    # sumbox = W.sum(axis=0, dtype='float') 
    # W /= sumbox

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