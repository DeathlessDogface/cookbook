#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
create a object that can save,search,change,remove tree-data
"""
import getopt
import json
from copy import deepcopy

from pickle_cache import PickleCache


class ReCode():
    SUCCESS = 0  # The function run successfully
    ERROR = 1  # Something unexpected happened

    def __getattr__(self, item):
        return self.__getattr__(item.upper())

    def translate(self, code):
        for name in dir(self):
            if self.__getattr__(name) == code:
                return name
        return "Unknown code:%s" % code


class Node():
    def __init__(self, father_id, node_id):
        self.father_id = father_id
        self.node_id = node_id
        self.children = set()

    def __str__(self):
        output = []
        for k in dir(self):
            if k.startswith('_'):
                continue
            if k in ['father_id', 'node_id']:
                continue
            if callable(getattr(self, k)):
                continue
            output.append("%s: %s" % (k, getattr(self, k)))
        output.sort()
        output.insert(0, "father_id: %s" % self.father_id)
        output.insert(0, "node_id: %s" % self.node_id)
        return "<Node::%s>" % (",".join(output))

    @classmethod
    def from_dict(cls, **node_dict):
        father_id = node_dict.pop('father_id')
        node_id = node_dict.pop('node_id')
        obj = cls(father_id, node_id)
        obj.update_dict(**node_dict)
        return obj

    def update_dict(self, **node_dict):
        for key, val in node_dict.items():
            if key in ["children"]:
                setattr(self, key, set(val))
            else:
                setattr(self, key, val)

    def add_child(self, *child_id):
        self.children = self.children.union(set(child_id))


class TreeData(object):
    def __init__(self):
        self.node_stone = dict()  # the key is node id ,the value is node_obj
        self.node_stone[-1] = Node(None, -1)  # it is the root of all node
        self.node_stone[-1].update_dict(tpye='root')
        pass

    def _next_id(self):
        return len(self.node_stone)

    def check_has_node_by_id(self, node_id):
        """
        if the tree is larger then memory,it will be a must.
        if the node is not in the tree ,assert an error
        """
        assert node_id in self.node_stone, "The node:%s is not in the tree." % node_id

    def get_roots(self):
        return self.get_children(-1)

    def get_node_by_id(self, node_id):
        self.check_has_node_by_id(node_id)
        return deepcopy(self.node_stone[node_id])

    def _pop_node_by_id(self, node_id):
        self.check_has_node_by_id(node_id)
        if node_id == -1:
            return deepcopy(self.node_stone[-1])
        return self.node_stone.pop(node_id)

    def get_tree_by_id(self, node_id, delete_tree=False):
        if delete_tree:
            node_obj = self._pop_node_by_id(node_id)
        else:
            node_obj = self.get_node_by_id(node_id)
        children_id = node_obj.children
        node_dict = node_obj.__dict__
        node_dict['children'] = []
        for child_id in children_id:
            node_dict['children'].append(self.get_tree_by_id(child_id, delete_tree=delete_tree))
        return node_dict

    def get_children(self, node_id):
        children = []
        node_obj = self.get_node_by_id(node_id)
        for child_id in node_obj.children:
            try:
                children.append(self.get_node_by_id(child_id))  # if child not exist,will get an assert error
                self.node_stone[child_id].update_dict(father_id=node_obj.node_id)
            except AssertionError:
                self.node_stone[node_id].children.remove(child_id)
        return children

    def get_father(self, node_id):
        node_obj = self.get_node_by_id(node_id)
        try:
            father_obj = self.get_node_by_id(node_obj.father_id)  # if child not exist,will get an assert error
            self.node_stone[node_obj.father_id].add_child(node_id)
            return father_obj  # the deep copy of it's father node
        except AssertionError:
            self.node_stone[node_id].update_dict(father_id=-1)
            self.node_stone[-1].add_child(node_id)
            return self.get_node_by_id(-1)

    def insert_with_node_dict_safe(self, **node_dict):
        """
        the function will not recover other node
        :param node_dict: a dict of node that has the key named father_id
        :return: ReCode value
        """
        try:
            self.check_has_node_by_id(int(node_dict["node_id"]))
            raise RuntimeError("the node has existed in the tree!")
        except (AssertionError, KeyError):
            return self.insert_with_node_dict(**node_dict)

    def insert_with_node_dict(self, **node_dict):
        """
        add nodes to the tree and this must be passed
        if the node has existed ,replace it
        :param node_dict: a dict of node that has the key named father_id
        :return:ReCode value
        """
        assert node_dict.has_key('father_id'), "The father id is a must"
        father_id = int(node_dict['father_id'])
        self.check_has_node_by_id(father_id)
        if node_dict.has_key('node_id'):
            node_id = int(node_dict['node_id'])
            assert node_id > -1  # node id must > -1,because -1 is the root of all node
        else:
            node_id = self._next_id()
        node_dict['node_id'] = node_id
        node_dict['father_id'] = father_id
        self.node_stone[node_id] = Node.from_dict(**node_dict)
        self.node_stone[father_id].children.add(node_id)
        return ReCode.SUCCESS

    def insert_with_node_list(self, node_list):
        pass

    def insert_with_node_tree(self, node_tree):
        pass

    def delete_branch_by_node_id(self, node_id):
        return self.get_tree_by_id(node_id, delete_tree=True)

    def delete_node_with_inherit(self, node_id, inherit="father"):
        """
        delete a node and save its children
        :param node_id:
        :param inherit: "father" or "root"/-1
        :return:
        """
        node_obj = self._pop_node_by_id(node_id)

        for child_id in node_obj.children:
            if inherit in ["root", -1]:
                self.node_stone[child_id].update_dict(father_id=-1)
            else:
                try:
                    self.check_has_node_by_id(node_obj.father_id)
                    self.node_stone[child_id].update_dict(father_id=node_obj.father_id)
                except AssertionError:
                    self.node_stone[child_id].update_dict(father_id=-1)

    def update_node_by_id(self, node_id, **kwargs):
        """

        :param node_id:
        :param kwargs:#NULL <=> delete attribute
        :return:
        """
        pass


def __test__():
    print "test insert_with_node_dict ============"
    print "test insert_with_node_dict_safe ======="
    print "test safe----------------------"
    print "test unsafe--------------------"
    print "test check_has_node_by_id ============="
    print "test update_node_by_id ================"
    print "test get_node_by_id ==================="
    print "test get_father ======================="
    print "test get_children ====================="
    print "test get_roots ========================"
    print "test get_tree_by_id ==================="
    print "test delete_node_with_inherit ========="
    print "test delete_branch_by_node_id ========="


if __name__ == "__main__":
    """
    -f      --father_id         int
    -d      --attribute_dict    dict
    -l      --attribute_list    list
    """
    __test__()
    while False:
        orders = raw_input("order:function arg1 arg2 ...\t").split()
        if orders:
            function = orders[0]
            if len(orders) > 1:
                options, args = getopt.getopt(orders[1:], 'f:d:l:',
                                              ['father_id=', 'attribute_dict=', 'attribute_list='])
            else:
                options, args = [], []
            kwargs = {}
            args = []
            for name, value in options:
                if name in ['-d', '--attribute_dict']:
                    kwargs = json.loads(value)
                elif name in ['-l', '--attribute_list']:
                    args = json.loads(value)
        else:
            function = False
            kwargs = False
        with PickleCache('tree_data_cache') as cache:
            cache, old = cache
            if isinstance(old, TreeData):
                tree = old
            else:
                tree = TreeData()
            if function and kwargs:
                print tree.__getattribute__(function)(**kwargs)
            cache(tree)
        print json.dumps(tree.get_tree_by_id(-1), sort_keys=True, indent=4)
