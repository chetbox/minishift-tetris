#!/usr/bin/env python

from argparse import ArgumentParser
from minishift import Minishift, MCP2210Interface
from time import sleep
from random import choice
from copy import deepcopy
from numpy import dot, add, subtract, transpose, mean, round
import pygame

class Tetris:
    def __init__(self, height):
        self.height = height
        A = height - 1
        B = height - 2 
        self.new_shapes = [
            {2: [A], 3: [A], 4: [A,B]},
            {2: [A,B], 3: [A], 4: [A]},
            {2: [A], 3: [A], 4: [A], 5: [A]},
            {3: [A,B], 4: [A,B]},
            {3: [A], 4: [A,B], 5: [B]},
            {3: [B], 4: [A,B], 5: [A]},
            {3: [B], 4: [A,B], 5: [B]},
        ]
        self.ms = Minishift(MCP2210Interface(0x04d8, 0xf517), self.height)
        self.canvas = self.ms.canvas
        self.new_shape()
        self.in_play = False
        self.drop_fast = False
        self.score = 0

    def set(self, val, coords):
        for col, rows in coords.items():
            for row in rows:
                self.canvas[row, col] = val

    def new_shape(self):
        self.current_pos = deepcopy(choice(self.new_shapes))
        self.set(1, self.current_pos)
        self.drop_fast = False

    def is_available(self, coords):
        for col, rows in coords.items():
            if col not in range(0, 8):
                return False
            for row in rows:
                if row not in range(0, self.height) or self.canvas[row, col]:
                    return False
        return True

    def move_down(self):
        for col, rows in self.current_pos.items():
            self.current_pos[col] = map(lambda row: row-1, rows)

    def move_horizontally(self, move_by):
        new_pos = dict(map(lambda (col, rows): (col + move_by, rows),
                           self.current_pos.items()))
        if self.is_available(new_pos):
            self.current_pos = new_pos

    def rotate(self):
        current_coords = [(col,row) for col, rows in self.current_pos.items() for row in rows]
        center = round(mean(current_coords, axis=0))
        rotated = add(transpose(dot([[0,-1],[1,0]],
                                    transpose(subtract(current_coords,
                                                       center)))),
                      center)
        new_pos = {}
        for col, row in rotated:
            new_pos[int(col)] = [int(row)] + (new_pos[int(col)] if new_pos.has_key(int(col)) else [])
        cols = new_pos.keys()
        rows = [r for rows in new_pos.values() for r in rows]
        min_col, max_col = (min(*cols), max(*cols)) if len(cols) > 1 else (cols[0], cols[0])
        if min_col < 0:
            self.move_horizontally(0 - min_col)
        if max_col > 7:
            self.move_horizontally(7 - max_col)
        if filter(lambda row: row >= self.height, rows):
            for col, rows in new_pos.items():
                new_pos[col] = map(lambda row: row-1, rows)
        if self.is_available(new_pos):
            self.current_pos = new_pos

    def tick(self):

        def is_resting():
            for col, rows in self.current_pos.items():
                row = min(*rows) if len(rows) > 1 else rows[0]
                if row == 0 or self.canvas[row-1, col]:
                    return True
            return False

        def at_top():
            for col in range(8):
                if self.canvas[self.height-1, col]:
                    return True
            return False

        def remove_complete_rows():
            points = 0
            for row in range(self.height-1, -1, -1):
                if self.canvas[row] == 255:
                    points = points * 4 if points > 0 else 100
                    for row_above in range(row + 1, self.height):
                        self.canvas[row_above - 1] = self.canvas[row_above]
            self.score += points

        if is_resting():
            if at_top():
                # R.I.P.
                self.in_play = False
                return
            remove_complete_rows()
            self.new_shape()
        else:
            self.set(0, self.current_pos)
            self.move_down()
            self.set(1, self.current_pos)
        self.ms.update()

    def process_input_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                self.set(0, self.current_pos)
                if event.key == pygame.K_LEFT:
                    self.move_horizontally(-1)
                if event.key == pygame.K_RIGHT:
                    self.move_horizontally(1)
                if event.key == pygame.K_DOWN:
                    self.drop_fast = True
                if event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                    self.rotate()
                self.set(1, self.current_pos)

    def run(self):
        pygame.init()
        pygame.display.set_mode((100, 100))
        self.in_play = True
        while self.in_play:
            self.process_input_events()
            self.tick()
            sleep(0.01 if self.drop_fast else 0.16)

if __name__ == '__main__':
    arg_parser = ArgumentParser(description='Minishift Tetris')
    arg_parser.add_argument('minishifts', type=int, help='The number of minishifts you have connected')
    args = arg_parser.parse_args()

    tetris = Tetris(8 * args.minishifts)
    tetris.run()
    print(tetris.score)
