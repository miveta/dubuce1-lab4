import random
from copy import deepcopy
from mpi4py import MPI
import sys
import time
import numpy as np

BOARD_HEIGHT = 6
BOARD_WIDTH = 7

EMPTY, COMPUTER, PERSON = 0, 1, 2


def write(x):
    sys.stdout.write(x.__str__())
    sys.stdout.write("\n")
    sys.stdout.flush()


class Board:
    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT):
        self.columns = width
        self.rows = height
        self.board = np.zeros((BOARD_HEIGHT, BOARD_WIDTH), int)

    def __copy__(self):
        new = type(self)(self.columns, self.rows)
        new.board = deepcopy(self.board)

        return new

    def __str__(self):
        str = ""
        for r in reversed(range(self.rows)):
            str += "----" * self.columns + "-" + "\n"
            for c in range(self.columns):
                if c == 0:
                    str += '| '

                player = self.board[r, c]
                if player == EMPTY:
                    player = " "

                str += player.__str__() + " | "

            str += "\n"

        str += "----" * self.columns + "-" + "\n"

        return str

    def play(self, column, player):
        if column >= self.columns:
            raise Exception("Column out of range")

        for row in range(self.rows):
            if self.board[row, column] == EMPTY:
                self.board[row, column] = player
                return

        raise Exception("Height out of range")

    def is_win(self, player):
        # check horizontal lines
        for c in range(self.columns - 3):
            for r in range(self.rows):
                if (self.board[r, c] == player and self.board[r, c + 1] == player
                        and self.board[r, c + 2] == player and self.board[r, c + 3] == player):
                    return True

        # check columns
        for c in range(self.columns):
            for r in range(self.rows - 3):
                if (self.board[r, c] == player and self.board[r + 1, c] == player
                        and self.board[r + 2, c] == player and self.board[r + 3, c] == player):
                    return True

        # check rising diagonals
        for c in range(self.columns - 3):
            for r in range(self.rows - 3):
                if (self.board[r, c] == player and self.board[r + 1, c + 1] == player
                        and self.board[r + 2, c + 2] == player and self.board[r + 3, c + 3] == player):
                    return True

        # check falling diagonals
        for c in range(self.columns - 3):
            for r in range(3, self.rows):
                if (self.board[r, c] == player and self.board[r - 1, c + 1] == player
                        and self.board[r - 2, c + 2] == player and self.board[r - 3, c + 3] == player):
                    return True

        return False

    @staticmethod
    def valid_moves(board):
        moves = []

        for c in range(board.columns):
            if board.board[board.rows - 1, c] == EMPTY:
                moves.append(c)

        return moves

    @staticmethod
    def number_of_moves(board):
        moves = 0

        for c in range(board.columns):
            if board.board[board.rows - 1, c] == EMPTY:
                moves += 1

        return moves

    @staticmethod
    def minimax(board, player, depth):
        return board.minimax(player, depth)

    def minimax(self, player, depth):
        if self.is_win(COMPUTER):
            return None, 1
        elif self.is_win(PERSON):
            return None, -1

        valid_moves = Board.valid_moves(self)

        if len(valid_moves) == 0 or depth == 0:
            # nothing left to play, nobody won
            return None, 0

        # Max player - COMPUTER
        if player == COMPUTER:
            value = -1

            best_move = random.choice(valid_moves)

            for move in valid_moves:
                new_board = self.__copy__()
                new_board.play(move, COMPUTER)

                _, new_score = new_board.minimax(PERSON, depth - 1)
                new_score /= len(valid_moves)

                if new_score > value:
                    value = new_score
                    best_move = move

            return best_move, value

        # Min player - PERSON
        if player == PERSON:
            value = 1

            best_move = random.choice(valid_moves)

            for move in valid_moves:
                new_board = self.__copy__()
                new_board.play(move, PERSON)

                _, new_score = new_board.minimax(COMPUTER, depth - 1)
                new_score /= len(valid_moves)

                if new_score < value:
                    value = new_score
                    best_move = move

            return best_move, value

    @staticmethod
    def serialize():
        return

    def deserialize(self, string):
        return


class Connect4MPI:
    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT, depth=2):
        self.board = None
        self.width, self.height, self.depth = width, height, depth
        self.comm = MPI.COMM_WORLD
        self.size = self.comm.Get_size()
        self.rank = self.comm.Get_rank()

        self.num_tasks = self.width * self.width
        self.tasks = []
        self.results = {}

    def run(self):
        if self.rank == 0:
            self.do_master()
        else:
            self.do_worker()

    def get_tasks(self):
        tasks = []
        results = {}

        for i in range(self.width):
            for j in range(self.width):
                move = (i, j)

                task = {"computer_move": i, "person_move": j, "type": "minimax", "board": self.board.__copy__()}

                tasks.append(task)
                results[move] = -1

        return tasks, {}

    def do_master(self):
        self.board = Board(width=self.width, height=self.height)

        self.play()

        self.notify_workers({"type": "end"})

        return

    def notify_workers(self, msg):
        for i in range(1, self.size):
            self.comm.send(msg, dest=i, tag=0)

    def do_worker(self):
        while True:
            request = {"type": "request", "rank": self.rank}

            self.comm.send(request, dest=0, tag=0)

            task = self.comm.recv(source=0, tag=0)

            if task["type"] == "end":
                break
            elif task["type"] == "minimax":
                board = task["board"]

                move_computer = task["computer_move"]
                move_person = task["person_move"]

                valid = True

                if move_computer in Board.valid_moves(board):
                    board.play(move_computer, COMPUTER)
                else:
                    valid = False

                if move_person in Board.valid_moves(board) and valid:
                    board.play(move_person, PERSON)
                else:
                    valid = False

                if valid:
                    move, score = board.minimax(depth=self.depth, player=COMPUTER)

                    result = {"type": "result", "best_move": move, "score": score,
                              "computer_move": task["computer_move"],
                              "person_move": task["person_move"]}
                else:
                    result = {"type": "result", "best_move": None, "score": -1,
                              "computer_move": task["computer_move"],
                              "person_move": task["person_move"]}

                self.comm.send(result, dest=0, tag=0)
        return

    def aggregate_results(self, results, board):
        aggregated = {}

        valid_moves = Board.valid_moves(board)

        for valid_move in valid_moves:
            score_sum = 0
            valid_moves_sum = 0

            for result in results:
                if result[0] == valid_move:
                    score_sum += results.get(result)
                    valid_moves_sum += 1

            if valid_moves_sum > 0:
                score_sum /= valid_moves_sum

                aggregated[valid_move] = score_sum

        return aggregated

    def play(self):
        win = False
        write(self.board.__str__())

        while not win:
            write("COMPUTER PLAYING")

            start_time = time.time()
            tasks, results = self.get_tasks()

            while len(tasks) > 0:
                msg = self.comm.recv()

                if msg["type"] == "request":
                    task = tasks.pop()
                    self.comm.send(task, dest=msg["rank"])
                elif msg["type"] == "result":
                    #write(msg)
                    move = (msg["computer_move"], msg["person_move"])

                    results[move] = msg["score"]

            aggregated = self.aggregate_results(results, self.board)

            write(str(aggregated))
            best_move = max(aggregated, key=aggregated.get)
            write(str(best_move))

            end_time = time.time()
            write("Time taken: " + str(end_time - start_time))
            
            self.board.play(best_move, COMPUTER)

            write(self.board.__str__())
            if self.board.is_win(COMPUTER):
                write("Computer won")
                break

            write("YOU PLAY")
            move = int(input())

            while move not in Board.valid_moves(self.board):
                write("Invalid move")
                move = int(input())

            self.board.play(move, PERSON)

            write(self.board.__str__())
            if self.board.is_win(PERSON):
                write("You won")
                break


connect4 = Connect4MPI(depth=4)

connect4.run()
