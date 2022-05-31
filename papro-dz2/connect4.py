# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import math
import random
import time
from copy import deepcopy
# from mpi4py import MPI
import sys

import numpy as np

# size = MPI.COMM_WORLD.Get_size()
# rank = MPI.COMM_WORLD.Get_rank()
# name = MPI.Get_processor_name()

BOARD_HEIGHT = 6
BOARD_WIDTH = 7

EMPTY, COMPUTER, PERSON = 0, 1, 2


def write(x):
    sys.stdout.write(x)


class Node:
    def __init__(self):
        a = 0


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


class Connect4:
    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT, depth=2):
        self.board = Board(width, height)
        self.depth = depth

    def play(self):
        player = COMPUTER

        win = False
        print(self.board)

        while not win:
            if player == COMPUTER:
                start_time = time.time()
                print("COMPUTER PLAYING")
                move, score = self.board.minimax(COMPUTER, self.depth)

                end_time = time.time()
                write("Time taken: " + str(end_time - start_time))

                self.board.play(move, COMPUTER)

                print(self.board)
                if self.board.is_win(COMPUTER):
                    print("Computer won")
                    break


                player = PERSON

            elif player == PERSON:
                print("YOU PLAY")
                move = int(input())

                self.board.play(move, PERSON)

                print(self.board)
                if self.board.is_win(PERSON):
                    print("You won")
                    break

                player=COMPUTER

connect4 = Connect4(depth=6)

connect4.play()
#board = Board()
#board.play(0, PERSON)
#board.play(0, PERSON)
#board.play(0, PERSON)
#board.play(0, PERSON)

#print(board.is_win(PERSON))

#print(board)
# board2 = board.__copy__()

# board.play(0, 'P')

# board2.play(0, 'C')

# print("board 2", board2.board)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
