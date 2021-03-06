import sys
import os
from PIL import Image
from pythonds.graphs import PriorityQueue
def simpleQuant(imageFile, rq = 36, gq = 42, bq = 42):
    im = Image.open(imageFile)
    w, h = im.size
    for row in range(h):
        for col in range(w):
            r, g, b = im.getpixel((col, row))
            r = r//rq * rq
            g = g//gq * gq
            b = b//bq * bq
            im.putpixel((col, row), (r,g,b))
    im.show()


def buildAndDisplay(imageFile):
    im = Image.open(imageFile)
    w, h = im.size
    ot = OctTree()
    for row in range(h):
        for col in range(w):
            r, g, b = im.getpixel((col, row))
            #print(f'Inserting {r}_{g}_{b}')
            ot.insert(r, g, b)
    ot.reduce(256)

    for row in range(h):
        for col in range(w):
            r, g, b = im.getpixel((col, row))
            nr, ng, nb = ot.find(r, g, b)
            im.putpixel((col, row), (nr, ng, nb))
    im.show()

def buildAndDisplay1(imageFile, maxCubes = 256, method = "individual"):
    ot = OctTree()
    ot.openImage(imageFile)
    ot.buildTree()
    ot.quantize(maxCubes, method )

class OctTree:
    def __init__(self):
        self.root = None
        self.maxLevel = 5
        self.numLeaves = 0
        self.leafList = []
        self.leafQueue = PriorityQueue()
        self.image = None
    def openImage(self, imageFile):
        self.image = Image.open(imageFile)
        self.image.show()
    def writeImage(self, imageFile):
        self.image.save(imageFile)
    def buildTree(self):
        w, h = self.image.size
        for row in range(h):
            for col in range(w):
                r, g, b = self.image.getpixel((col, row))
                self.insert(r, g, b)
    def quantize(self, maxCubes, method = "total"):
        self.reduce(maxCubes = maxCubes, method = method)
        w, h = self.image.size
        for row in range(h):
            for col in range(w):
                r, g, b = self.image.getpixel((col, row))
                nr, ng, nb = self.find(r, g, b)
                self.image.putpixel((col, row), (nr, ng, nb))
        self.image.show()
    def insert(self, r, g, b):
        if not self.root:
            self.root = self.otNode(outer = self)
        self.root.insert(r, g, b, 0, self)
    def find(self, r, g, b):
        if self.root:
            return self.root.find(r, g, b, 0)
    def reduce(self, maxCubes, method = "total"):
        while len(self.leafList) > maxCubes:
            smallest = self.findMinCube(method)
            smallest.parent.merge()
            self.leafList.append(smallest.parent)
            self.leafQueue.add((smallest.parent.count, smallest.parent))
            self.numLeaves += 1
    def findMinCube(self, method = "total"):
        if method != "individual":
            minCount = sys.maxsize
            maxLev = 0
            minCube = None
            i = self.leafQueue.delMin()
            minCube = i
            minCount = i.count
            maxLev = i.level
            self.leafQueue.add((i.count, i))
            #for i in self.leafList:
            #    if i.count <= minCount and i.level >= maxLev:
            #        minCube = i
            #        minCount = i.count
            #        maxLev = i.level
            return minCube
        else:
            tempDic = {}
            for i in self.leafList:
                if not i.parent in tempDic:
                    tempDic[i.parent] = i.count
                else:
                    tempDic[i.parent] += i.count
            minCount = sys.maxsize
            minKey = None
            for c in tempDic.keys():
                if tempDic[c] < minCount:
                    minCount = tempDic[c]
                    minKey = c
            for i in range(8):
                if minKey.children[i]:
                    return minKey.children[i]


    ####
    # Inner class otNode
    ####
    class otNode:
        def __init__(self, parent = None, level = 0, outer = None):
            self.red = 0
            self.green = 0
            self.blue = 0
            self.count = 0
            self.parent = parent
            self.level = level
            self.oTree = outer
            self.children = [None]*8
        def insert(self, r, g, b, level, outer):
            if level < self.oTree.maxLevel:
                idx = self.computeIndex(r, g, b, level)
                if self.children[idx] == None:
                    self.children[idx] = outer.otNode(parent = self, \
                                                      level = level + 1,\
                                                      outer = outer)
                self.children[idx].insert(r, g, b, level + 1, outer)
            else:
                if self.count == 0:
                    self.oTree.numLeaves += 1
                    self.oTree.leafList.append(self)
                    self.oTree.leafQueue.add((self.count, self))
                self.red += r
                self.green += g
                self.blue += b
                self.count += 1
                self.oTree.leafQueue.decreaseKey(self, self.count)

        def find(self, r, g, b, level):
            if level < self.oTree.maxLevel:
                idx = self.computeIndex(r, g, b, level)
                if self.children[idx]:
                    return self.children[idx].find(r, g, b, level + 1)
                elif self.count > 0:
                    return ((self.red // self.count, self.green // self.count, self.blue// self.count))
                else:
                    raise KeyError("No leaf node for this color")
            else:
                return ((self.red // self.count, self.green // self.count, self.blue// self.count))

        def merge(self):
            for i in self.children:
                if i:
                    if i.count > 0:
                        self.oTree.leafList.remove(i)
                        self.oTree.leafQueue.decreaseKey(i, -1 * (sys.maxsize))
                        self.oTree.leafQueue.delMin()
                        self.oTree.numLeaves -= 1
                    else:
                        print("Recursively Merging non-leaf...")
                        i.merge()
                    self.count += i.count
                    self.red += i.red
                    self.green += i.green
                    self.blue += i.blue
            for i in range(8):
                self.children[i] = None
        def computeIndex(self ,r, g, b, level):
            shift = 8 - level
            rc = (r >> (shift - 2)) & 0x4
            gc = (g >> (shift - 1)) & 0x2
            bc = (b >> (shift)) & 0x1
            return (rc|gc|bc)
