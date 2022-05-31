from mpi4py import MPI
import numpy as np
from copy import deepcopy

H = 6
W = 7
winLen = 4
playPiece = "P"
compPiece = "C"
emptPiece = "."
maxDepth = 5


class Board:
    def __init__(self, isComputerFirst):
        listaH = []
        for i in range(H):
            listaW = []
            for j in range(W):
                listaW.append(emptPiece)
            listaH.append(listaW)

        self.field = np.array(listaH)

        if isComputerFirst:
            self.nextPiece = compPiece
        else:
            self.nextPiece = playPiece

    def findFirst(self, col):
        for i in range(0, H):
            if self.field[i][col] != emptPiece:
                return i, True

        return H, False

    def checkVertical(self, row, col):
        leng = 0
        for i in range(winLen):
            if row + i >= H:
                return False

            if self.field[row][col] != self.field[row + i][col]:
                return False

            leng += 1
            if leng >= winLen:
                return True

    def checkHorizontal(self, row, col):
        lenL = 0
        lenR = 0
        for i in range(1, winLen):
            if col - i < 0:
                break

            if self.field[row][col] != self.field[row][col - i]:
                break

            lenL += 1

        for i in range(1, winLen):
            if col + i >= W:
                break

            if self.field[row][col] != self.field[row][col + i]:
                break

            lenR += 1

        if lenL + lenR + 1 >= winLen:
            return True

        return False

    def checkFirstDiagonal(self, row, col):  # /
        lenL = 0
        lenR = 0
        for i in range(1, winLen):
            if col - i < 0 or row + i >= H:
                break

            if self.field[row][col] != self.field[row + i][col - i]:
                break

            lenL += 1

        for i in range(1, winLen):
            if col + i >= W or row - i < 0:
                break

            if self.field[row][col] != self.field[row - i][col + i]:
                break

            lenR += 1

        if lenL + lenR + 1 >= winLen:
            return True

        return False

    def checkSecondDiagonal(self, row, col):  # \
        lenL = 0
        lenR = 0
        for i in range(1, winLen):
            if col - i < 0 or row - i < 0:
                break

            if self.field[row][col] != self.field[row - i][col - i]:
                break

            lenL += 1

        for i in range(1, winLen):
            if col + i >= W or row + i >= H:
                break

            if self.field[row][col] != self.field[row + i][col + i]:
                break

            lenR += 1

        if lenL + lenR + 1 >= winLen:
            return True

        return False

    def isFinished(self, col):
        row, _ = self.findFirst(col)

        if self.checkVertical(row, col) or self.checkHorizontal(row, col) or self.checkFirstDiagonal(row,
                                                                                                     col) or self.checkSecondDiagonal(
                row, col):
            return True

        return False

    def calculateScore(self, col):
        if not self.isFinished(col):
            return 0

        row, _ = self.findFirst(col)
        if self.field[row][col] == playPiece:
            return -1

        return 1

    def rotatePiece(self):
        if self.nextPiece == playPiece:
            self.nextPiece = compPiece
        else:
            self.nextPiece = playPiece

    def playTurn(self, col):
        if self.field[0][col] != emptPiece:
            return False, None

        row, _ = self.findFirst(col)
        row -= 1

        self.field[row][col] = self.nextPiece
        self.rotatePiece()
        return True, self.isFinished(col)

    def revertTurn(self, col):
        row, _ = self.findFirst(col)

        self.field[row][col] = emptPiece
        self.rotatePiece()
        return

    def gameSimulation(self, maxDepth=maxDepth):

        bestCol = -1
        maxScore = -2
        for i in range(W):
            result = self.dfs(i, 0, maxDepth)
            if result is not None and result > maxScore:
                bestCol = i
                maxScore = result

        return bestCol, maxScore

    def dfs(self, col, depth, maxDepth=maxDepth):
        # simulate move
        ok, fin = self.playTurn(col)
        if not ok:
            self.revertTurn(col)
            return None
        if fin:
            score = self.calculateScore(col)
            self.revertTurn(col)
            return score

        if (depth == maxDepth - 1):
            score = self.calculateScore(col)
            self.revertTurn(col)
            return score

        # simulate move
        results = []
        for i in range(W):
            result = self.dfs(i, depth + 1, maxDepth)
            if result is not None:
                results.append(result)

        self.revertTurn(col)
        if len(results) == 0:
            return None

        if self.nextPiece == playPiece and contains(results, -1):
            return -1

        if self.nextPiece == compPiece and contains(results, 1):
            return 1

        return sum(results) / len(results)

    def isFull(self):
        for i in range(W):
            if self.field[0][i] == emptPiece:
                return False

        return True


def contains(list, element):
    for el in list:
        if el == element:
            return True

    return False


def sequential(board):
    # create WxW tasks
    tasks = []
    for i in range(W):
        for j in range(W):
            tasks.append((i, j))

    while True:
        results = dict()

        copyBoard = deepcopy(board)

        for task in tasks:

            board = deepcopy(copyBoard)

            for move in task:
                ok, fin = board.playTurn(move)
                if not ok:
                    results[task] = None
                    break

                if fin:
                    results[task] = board.calculateScore(move)
                    comm.send(("result", rank, tasks, "success",), 0)
                    break

            column, score = board.gameSimulation()

            results[task] = score

        board = deepcopy(copyBoard)

        results_root = []
        for i in range(W):
            results_i = []
            for j in range(W):
                if results[(i, j)] is not None:
                    results_i.append(results[(i, j)])

            if contains(results_i, -1):
                results_root.append(-1)
            elif len(results_i) == 0:
                results_root.append(None)
            else:
                results_root.append(sum(results_i) / len(results_i))

        # if end of the game
        noneCnt = 0
        for el in results_root:
            if el is None:
                noneCnt += 1

        if noneCnt == len(results_root):
            print("Game over, no winner")
            break

        bestCol = -1
        maxScore = -2
        for i in range(W):
            if results_root[i] is not None and results_root[i] > maxScore:
                maxScore = results_root[i]
                bestCol = i

        # print("Dobrota: ", results_root)
        board.playTurn(bestCol)
        print(board.field)

        if board.isFinished(bestCol):
            print("Game over, computer wins")
            break

        if board.isFull():
            print("Game over")
            if maxScore == 1:
                print("Computer wins")
            elif maxScore == -1:
                print("Player wins")
            break

        print("Next player move:")
        col_player = int(input())
        board.playTurn(col_player)
        print(board.field)

        if board.isFinished(col_player):
            print("Game over, player wins")
            break


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    print("Enter field height:")
    H = int(input())

    print("Enter field width:")
    W = int(input())

    print("Who plays first (C or P):")
    firstMove = input()

    board = Board(firstMove == "C")

    if firstMove == "P":
        print(board.field)
        print("Next player move:")
        col_player = int(input())
        board.playTurn(col_player)
        print(board.field)

    if size == 1:
        sequential(board)
    else:

        # create WxW tasks
        tasks = []
        for i in range(W):
            for j in range(W):
                tasks.append((i, j))

        readyWorkers = []

        while True:
            results = dict()
            taskIndex = 0

            for i in range(len(readyWorkers)):
                comm.send(("task", tasks[taskIndex], board), readyWorkers[i])
                taskIndex += 1

            readyWorkers = []

            while len(readyWorkers) < size - 1:
                data = comm.recv(source=MPI.ANY_SOURCE)

                if data[0] == "ready":
                    if taskIndex == W * W:
                        readyWorkers.append(data[1])
                    else:
                        comm.send(("task", tasks[taskIndex], board), data[1])
                        taskIndex += 1

                if data[0] == "result":
                    if data[2] == "error":
                        results[data[2]] = data[3]
                    else:
                        results[data[2]] = data[4]

            # print(results)

            results_root = []
            for i in range(W):
                results_i = []
                for j in range(W):
                    if results[(i, j)] is not None:
                        results_i.append(results[(i, j)])

                if contains(results_i, -1):
                    results_root.append(-1)
                elif len(results_i) == 0:
                    results_root.append(None)
                else:
                    results_root.append(sum(results_i) / len(results_i))

            # if end of the game
            noneCnt = 0
            for el in results_root:
                if el is None:
                    noneCnt += 1

            if noneCnt == len(results_root):
                print("Game over, no winner")
                break

            bestCol = -1
            maxScore = -2
            for i in range(W):
                if results_root[i] is not None and results_root[i] > maxScore:
                    maxScore = results_root[i]
                    bestCol = i

            # print("Dobrota: ", results_root)
            board.playTurn(bestCol)
            print(board.field)

            if board.isFinished(bestCol):
                print("Game over, computer wins")
                break

            if board.isFull():
                print("Game over")
                if maxScore == 1:
                    print("Computer wins")
                elif maxScore == -1:
                    print("Player wins")
                break

            print("Next player move:")
            col_player = int(input())
            board.playTurn(col_player)
            print(board.field)

            if board.isFinished(col_player):
                print("Game over, player wins")
                break

        # release workers
        for worker in readyWorkers:
            comm.send("stop", worker)



else:
    while True:
        continueWhile = False

        comm.send(("ready", rank), 0)
        data = comm.recv(source=0)
        if data[0] == "task":
            _, tasks, board = data

            for move in tasks:
                ok, fin = board.playTurn(move)
                if not ok:
                    comm.send(("result", rank, "error", None), 0)
                    continueWhile = True
                    break

                if fin:
                    comm.send(("result", rank, tasks, "success", board.calculateScore(move)), 0)
                    continueWhile = True
                    break

            if continueWhile:
                continue

            column, score = board.gameSimulation()

            comm.send(("result", rank, tasks, "success", score), 0)

        else:
            break
