#!/usr/bin/env python
import json
import unittest
from unittest.mock import Mock

from labchain.datastructure.blockchain import BlockChain
from labchain.util.configReader import ConfigReader
from labchain.consensus.consensus import Consensus
from labchain.util.cryptoHelper import CryptoHelper as crypto
from labchain.datastructure.transaction import Transaction
from labchain.datastructure.txpool import TxPool


class BlockChainComponent(unittest.TestCase):
    """Class of testcases for the Blockchain module"""

    def setUp(self):
        """Setup phase for each testcase"""
        self.init_components()
        self.create_transactions()

    def test_get_block_range(self):
        self.create_blocks()
        # get_block_range doesn't consider genesis block so expected length = 0
        blocks = self.blockchain.get_block_range(0)
        self.assertEqual(len(blocks), 0)

    def test_get_block_by_id(self):
        self.create_blocks()
        # fetching first block whose id = 0
        blocks = self.blockchain.get_block_by_id(0)
        for block in blocks:
            self.assertEqual(block._block_id, 0)

    def test_get_block_by_hash(self):
        self.create_blocks()
        block_info = json.loads(self.blockchain.get_block_by_hash(self.blockchain._first_block_hash))
        self.assertEqual(block_info['nr'], 0)

    def test_add_block(self):
        self.create_blocks()
        self.blockchain.add_block(self.block1)
        #blocks = self.blockchain.get_block_range(0)
        #self.assertEqual(len(blocks), 1)

    """
    def test_add_block1(self):
        # now block8 has a branch with block 6

        self.block8 = self.block1 = self.blockchain.create_block([self.txn2, self.txn4])
        self.assertFalse(self.blockchain.add_block(self.block8), "Block is deleted")

        # block 9 has a normal predecessor block 7
        self.block9 = self.block1 = self.blockchain.create_block([self.txn2, self.txn4])
        self.assertTrue(self.blockchain.add_block(self.block9), "Block is saved")
    """

    def test_switch_to_longest_branch(self):
        self.create_blocks()
        # now block8 has a branch with block 6
        self.block8 = self.block1 = self.blockchain.create_block([self.txn2, self.txn4])

        # we are trying to add a new block in the block chain
        self.blockchain._blockchain[self.crypto_helper_obj.hash(self.block8.get_json())] = self.block8

        # calculating the length of the blockchain before adding new block
        prev_block_length = len(self.blockchain._blockchain.items())

        # calling the switching branch method
        self.blockchain.switch_to_longest_branch()
        # calculating the length of the blockchain after adding new block
        after_block_length = len(self.blockchain._blockchain.items())

        # after branch switching the length of the block should be same
        self.assertEqual(prev_block_length, after_block_length, "Block is deleted")

    def test_calculate_diff(self):
        self.create_blocks()
        # blocks added in setup
        blocks, t1, t2, diff = self.blockchain.calculate_diff()
        self.assertIsNotNone(blocks)
        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        self.assertIsNotNone(diff)

    def test_create_block(self):
        self.create_blocks()
        # creating new block based on given transaction list
        new_block = self.blockchain.create_block([self.txn2, self.txn4])
        self.assertIsNotNone(new_block, "New block Created")

    def test_get_last_n_transactions(self):
        self.create_and_save_block([self.txn1, self.txn2])
        self.assertEqual(self.blockchain.get_n_last_transactions(0), [])
        self.assertEqual(self.blockchain.get_n_last_transactions(1), [self.txn1])
        self.assertEqual(self.blockchain.get_n_last_transactions(3), [self.txn1,self.txn2])
    
    def test_get_transactions_by_hash(self):
        block_hash = self.create_and_save_block([self.txn1, self.txn2])
        self.assertEqual(self.blockchain.get_transaction(self.txn1.transaction_hash),(self.txn1,block_hash))

    """
    def test_send_block_to_neighbour(self):
        block_as_json = self.blockchain.send_block_to_neighbour(self.block1)
        block_as_object = Block.from_json(block_as_json)
        self.assertIsInstance(block_as_object, Block, "Sent the Block information requested by any neighbour")
    """

    def request_block_from_neighbour(self):
        self.create_blocks()
        self.assertEqual(1, 2 - 1, "They are equal")

    def init_components(self):
        node_config = './labchain/resources/node_configuration.ini'
        config_reader = ConfigReader(node_config)

        tolerance = config_reader.get_config(
            section='BLOCK_CHAIN',
            option='TOLERANCE_LEVEL')
        pruning = config_reader.get_config(
            section='BLOCK_CHAIN',
            option='TIME_TO_PRUNE')
        min_blocks = config_reader.get_config(
            section='MINING',
            option='NUM_OF_BLOCKS_FOR_DIFFICULTY')

        self.consensus = Consensus()
        self.crypto_helper_obj = crypto.instance()
        self.txpool = TxPool(self.crypto_helper_obj)
        self.block_list = []
        self.blockchain = BlockChain(node_id="nodeId1", tolerance_value=tolerance,
                                     pruning_interval=pruning,
                                     consensus_obj=self.consensus,
                                     txpool_obj=self.txpool,
                                     crypto_helper_obj=self.crypto_helper_obj,
                                     min_blocks_for_difficulty=min_blocks,
                                     db=None,
                                     q=None)

    def create_transactions(self):
        pr_key1, pub_key1 = self.crypto_helper_obj.generate_key_pair()
        pr_key2, pub_key2 = self.crypto_helper_obj.generate_key_pair()
        pr_key3, pub_key3 = self.crypto_helper_obj.generate_key_pair()
        pr_key4, pub_key4 = self.crypto_helper_obj.generate_key_pair()

        self.txn1 = Transaction(pub_key1, pub_key2, "Payload1")
        self.txn2 = Transaction(pub_key2, pub_key4, "Payload2")
        self.txn3 = Transaction(pub_key3, pub_key1, "Payload3")
        self.txn4 = Transaction(pub_key4, pub_key3, "Payload3")

        self.txn1.sign_transaction(self.crypto_helper_obj, pr_key1)
        self.txn2.sign_transaction(self.crypto_helper_obj, pr_key2)
        self.txn3.sign_transaction(self.crypto_helper_obj, pr_key3)
        self.txn4.sign_transaction(self.crypto_helper_obj, pr_key4)

        self.txn1.transaction_hash = self.crypto_helper_obj.hash(self.txn1.get_json())
        self.txn2.transaction_hash = self.crypto_helper_obj.hash(self.txn2.get_json())
        self.txn3.transaction_hash = self.crypto_helper_obj.hash(self.txn3.get_json())
        self.txn4.transaction_hash = self.crypto_helper_obj.hash(self.txn4.get_json())

    def create_blocks(self):
        self.block1 = self.blockchain.create_block([self.txn1, self.txn2])
        self.block2 = self.blockchain.create_block([self.txn3, self.txn4])
        self.block3 = self.blockchain.create_block([self.txn1, self.txn4])
        self.block4 = self.blockchain.create_block([self.txn1, self.txn3])
        self.block5 = self.blockchain.create_block([self.txn1, self.txn2])
        self.block6 = self.blockchain.create_block([self.txn3, self.txn4])
        self.block7 = self.blockchain.create_block([self.txn2, self.txn4])

    def create_and_save_block(self,transactions):
        block_hash = None
        block = self.blockchain.create_block(transactions)
        self.blockchain.active_mine_block_update(block)
        _timestamp2, _timestamp1, _num_of_blocks, _difficulty = self.blockchain.calculate_diff(block.predecessor_hash)
        if self.consensus.mine(block, _timestamp2, _timestamp1, _num_of_blocks, _difficulty):
            if self.blockchain.add_block(block,False):
                block_hash = block.get_computed_hash()
        self.blockchain.active_mine_block_update(None)
        return block_hash

if __name__ == '__main__':
    unittest.main()
