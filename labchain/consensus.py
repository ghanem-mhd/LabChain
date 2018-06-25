import json
import math
import sys
import time
import logging
from random import randint
from labchain.dashboardDB import DashBoardDB

from labchain.cryptoHelper import CryptoHelper


class Consensus:

    def __init__(self):

        self.crypto_helper = CryptoHelper.instance()
        self.max_diff = 5  # Threshold to be defined
        self.kill_mine = 0
        self.last_mine_time_sec = time.time()
        self.min_mining_time = time.time()
        self.max_mining_time = 0
        self.avg_mining_time = 0
        self.dash_board_db = DashBoardDB.instance()
        self.avg_helper = 0
        self.num_of_mined_blocks = 0
        self.num_of_transactions = 0

    def __getitem__(self, item):
        pass

    def __setitem__(self, key, value):
        pass

    def __iter__(self):
        pass

    def calculate_difficulty(self, latest_timestamp, earliest_timestamp, num_of_blocks):
        difficulty = int(((latest_timestamp - earliest_timestamp) / num_of_blocks))

        if difficulty >= self.max_diff:
            difficulty = self.max_diff - 1
        self.dash_board_db.change_current_diff(self.max_diff - difficulty)
        self.dash_board_db.retrieve_status_from_db()
        return self.max_diff - difficulty

        # global difficulty should not be updated, instead return difficulty,
        # because if validate is called during mining, it would update difficulty

    def validate(self, block, latest_timestamp, earliest_timestamp, num_of_blocks):
        difficulty = self.calculate_difficulty(latest_timestamp, earliest_timestamp, num_of_blocks)

        logging.debug('#INFO: validate Difficulty: ' + str(difficulty))
        zeros_array = "0" * difficulty
        data = {'index': str(block.block_id), 'tree_hash': str(block.merkle_tree_root), 'pre_hash':
                str(block.predecessor_hash), 'creator': str(block.block_creator_id), 'nonce': str(block.nonce)}
        message = json.dumps(data)
        block_hash = self.crypto_helper.hash(message)  # Assumed that hash is str
        logging.debug('#INFO:Consensus-> Block: ' + str(block.block_id) + ' is validated with result ' + str(
            block_hash[:difficulty] == zeros_array) + ' with hash: ' + str(block_hash))
        return block_hash[:difficulty] == zeros_array

    def update_db(self):
        self.dash_board_db.change_min_mining_time((int)(self.min_mining_time))
        self.dash_board_db.change_max_mining_time((int)(self.max_mining_time))
        self.dash_board_db.change_avg_mining_time((int)(self.avg_mining_time))
        self.dash_board_db.change_num_of_blocks(self.num_of_mined_blocks)
        self.dash_board_db.change_num_of_transactions(self.num_of_transactions)
        self.dash_board_db.retrieve_status_from_db()


    def mine(self, block, latest_timestamp, earliest_timestamp, num_of_blocks):
        difficulty = self.calculate_difficulty(latest_timestamp, earliest_timestamp, num_of_blocks)

        logging.debug('#INFO: mine Difficulty: ' + str(difficulty))

        start_time = time.time()
        zeros_array = "0" * difficulty
        data = {'index': str(block.block_id), 'tree_hash': str(block.merkle_tree_root), 'pre_hash':
                str(block.predecessor_hash), 'creator': str(block.block_creator_id), 'nonce': str(block.nonce)}
        message = json.dumps(data)
        block_hash = self.crypto_helper.hash(message)  # nonce is zero (we need to check that)
        counter = 0
        block.nonce = randint(0, sys.maxsize)
        while block_hash[:difficulty] != zeros_array:
            if self.kill_mine == 1:
                self.kill_mine = 0
                # need a boolean return to check if mine got killed
                logging.debug('#INFO:Consensus-> Block: ' + str(block.block_id) + ' mining process has been killed')
                return False
            block.nonce += 1
            counter = counter + 1
            if counter % 10000 == 0:
                logging.debug('#INFO:Consensus-> Block: ' + str(block.block_id) + ' is in mining process')
            data = {'index': str(block.block_id), 'tree_hash': str(block.merkle_tree_root), 'pre_hash':
                    str(block.predecessor_hash), 'creator': str(block.block_creator_id), 'nonce': str(block.nonce)}
            message = json.dumps(data)
            block_hash = self.crypto_helper.hash(message)
        block.timestamp = time.time()
        self.last_mine_time_sec = start_time
        time_diff = time.time() - start_time
        if time_diff < self.min_mining_time:
            self.min_mining_time = time_diff
        if time_diff > self.max_mining_time:
            self.max_mining_time = time_diff
        self.num_of_mined_blocks = self.num_of_mined_blocks + 1
        self.num_of_transactions = self.num_of_transactions + len(block.transactions)
        self.avg_mining_time = (self.avg_helper + time_diff) / self.num_of_mined_blocks
        self.avg_helper = self.avg_helper + time_diff
        self.update_db()
        self.dash_board_db.add_block(block)
        logging.debug('#INFO:Consensus-> Block: ' + str(block.block_id) + ' is mined successfully')
        # need a boolean return to check if mine got killed
        return True

    #    Code for updating the difficulty to be implemented by Blockchain component
    #    if self.blocks_counter % self.blocks_threshold  == 0 & self.recalculate == 1:
    #        self.blocks_counter = 0
    #        self.recalculate = 0;
    #        self.difficulty = self.calculate_difficulty(time.time())
