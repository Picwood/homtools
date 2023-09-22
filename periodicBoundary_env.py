# Application de PBC sur un VER creer par abaqus avec iteration d'enrichissement integre

import math
import numpy as np
from connectorBehavior import *
from visualization import *
from sketch import *
from job import *
from optimization import *
from mesh import *
from load import *
from interaction import *
from step import *
from assembly import *
from section import *
from material import *
from part import *
import connectorBehavior
import displayGroupOdbToolset as dgo
from xyPlot import *
import displayGroupMdbToolset as dgm
import regionToolset
import sys
from abaqus import *
from abaqusConstants import *
from math import ceil, fabs, sqrt
import __main__
import random
import numpy as np
import textRepr
import section
import regionToolset
import displayGroupMdbToolset as dgm
import part
import material
import assembly
import step
import interaction
import load
import mesh
import job
import sketch
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
import connectorBehavior
from copy import deepcopy
import os
import re
import csv
from Tkinter import *
import Tkinter, Tkconstants, tkFileDialog

def getCurrentModel():
    vpName = session.currentViewportName
    modelName = session.sessionState[vpName]['modelName']
    return mdb.models[modelName]

def switch(a, b):
    tmp = b
    b = a
    a = tmp

def find(f, seq):
    for item in seq:
        (key, value) = item
        if (value == f):
            return key
    return -1

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#      A class to describe a graph of type tree: without any cycles
#         designed to avoid duplicated DOF in constraint equations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Tree:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, mn):
        self.thetree = []
        self.oldtree = []
        self.keyword = ''
        self.modelname = mn
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def getCurrentGraph(self, keyword):
        self.keyword = keyword
        # mod = getCurrentModel(self.modelname)
        mod = mdb.models[self.modelname]
        conts = mod.constraints
        for i in range(0, len(conts.keys())):
            name = conts.keys()[i]
            if(name.find(keyword) > -1):
                (title, n1, n2, ddl) = name.split('_')
                if(int(ddl) == 1):
                    pos = -1
                    for j in range(0, len(self.thetree)):
                        if(n1 in self.thetree[j]):
                            twig = [n1, n2]
                            self.insertTwigInBranch(twig, self.thetree[j])
                            self.reduceTree(twig, self.thetree[j])
                            pos = j
                            break
                        elif(n2 in self.thetree[j]):
                            twig = [n2, n1]
                            self.insertTwigInBranch(twig, self.thetree[j])
                            self.reduceTree(twig, self.thetree[j])
                            pos = j
                            break
                    if(pos == -1):
                        self.thetree.append([n1, n2])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def insertTwigInBranch(self, twig, branch):
        if(twig[0] not in branch):
            print 'bug in insert twig! twig=', twig, ' branch=', branch
            return False
        ind = branch.index(twig[0])
        if(ind == len(branch)-1):
            branch.append(twig[1])
        elif(ind == 0):
            branch.insert(ind, twig[1])
        else:
            return False
        return True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def reduceTree(self, twig, curbranch):
        k = -1
        for branch in self.thetree:
            k = k+1
            if((branch is not curbranch) and (twig[1] in branch) and (twig[1] in curbranch)):
                ind0 = curbranch.index(twig[1])
                ind1 = branch.index(twig[1])
                if(ind0 == 0 and ind1 == len(branch)-1):
                    for j in range(ind1-1, -1, -1):
                        curbranch.insert(0, branch[j])
                    del self.thetree[k]
                    k = k-1
#                  return True
                elif(ind0 == 0 and ind1 == 0):
                    for j in range(1, len(branch)):
                        curbranch.insert(0, branch[j])
                    del self.thetree[k]
                    k = k-1
#                  return True
                elif(ind0 == len(curbranch)-1 and ind1 == len(branch)-1):
                    for j in range(ind1-1, -1, -1):
                        curbranch.append(branch[j])
                    del self.thetree[k]
                    k = k-1
#                  return True
                elif(ind0 == len(curbranch)-1 and ind1 == 0):
                    for j in range(1, len(branch)):
                        curbranch.append(branch[j])
                    del self.thetree[k]
                    k = k-1
#                  return True
                else:
                    print 'Tree reduction error! (ind0=', ind0, ' ind1=', ind1, ')', 'branch', branch, 'curbranch', curbranch, 'twig', twig
                    return False
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def addBranch(self, branch):
        n1 = branch[0]
        n2 = branch[1]
        abranch = None
        self.oldtree = deepcopy(self.thetree)
        for curbranch in self.thetree:
            if(n1 in curbranch and n2 in curbranch):
                return False
            elif(n1 in curbranch and abranch == None):
                twig = [n1, n2]
                if(not self.insertTwigInBranch(twig, curbranch)):
                    return False
                self.reduceTree(twig, curbranch)
                abranch = curbranch
                return True
            elif(n2 in curbranch and abranch == None):
                twig = [n2, n1]
                if(not self.insertTwigInBranch(twig, curbranch)):
                    return False
                self.reduceTree(twig, curbranch)
                abranch = curbranch
                return True
        if(abranch == None):
            self.thetree.append(branch)
        return True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def restoreTree(self):
        del self.thetree
        self.thetree = deepcopy(self.oldtree)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def iscycle(self):
        for curbranch in self.thetree:
            for node in curbranch:
                if(curbranch.count(node) > 1):
                    return True
        return False

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PeriodicBoundary:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, mn, RP1=None, RP2=None, RP3=None, set1=None, set2=None, set3=None):
        self.RP1 = RP1
        self.RP2 = RP2
        self.RP3 = RP3
        self.set1 = set1
        self.set2 = set2
        self.set3 = set3
        self.modelname = mn
        #self.modelname = self.getCurrentModel(self.modelname)
        # self.a = a = mdb.models[modelname].rootAssembly
        pass
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def build_set(self, the_set, a, small_dist):
        myModel = mdb.models[self.modelname]
        a = myModel.rootAssembly
        nameset = 'Picked_set'+str(len(a.sets))
        edges = []
        faces = []
        nodes = []
        vert = []
        refpoints = []
        for o in the_set:
            if(type(o).__name__ == 'Edge'):
                i1 = a.instances[o.instanceName]
                edges.append(i1.edges.findAt(o.pointOn))
            elif(type(o).__name__ == 'Face'):
                i1 = a.instances[o.instanceName]
                faces.append(i1.faces.findAt(o.pointOn))
            elif(type(o).__name__ == 'ReferencePoint'):
                refpoints.append(a.referencePoints.findAt(a.getCoordinates(o)))
            elif(type(o).__name__ == 'MeshNode'):
                i1 = a.instances[o.instanceName]
                nodes.append(i1.nodes.getByBoundingSphere(o.coordinates, small_dist))
            elif(type(o).__name__ == 'Vertices'):
                i1 = a.instances[o.instanceName]
                vert.append(i1.vertices.findAt(o.pointOn))
            elif(type(o).__name__ == 'Vertex'):
                i1 = a.instances[o.instanceName]
                vert.append(i1.vertices.findAt(o.pointOn))
            else:
                print 'unknown type ', type(o).__name__

        a.Set(edges=edges, referencePoints=refpoints, faces=faces,
              nodes=nodes, name=nameset, vertices=vert)

        return nameset
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def Periodic(self, Vx, Vy, Vz, is_smallstrain, dim):
        self.Vx = Vx
        self.Vy = Vy
        self.Vz = Vz
        self.carac = 1.e-2
        small = [Vx, Vy, Vz]
        small.sort()
        self.is_small_strain = is_smallstrain
        if(not self.CheckInput()):
            print "Not all the inputs are given !"
            return 0

        # myModel = self.getCurrentModel(self.modelname)
        myModel = mdb.models[self.modelname]
        a = myModel.rootAssembly
        if Vx != 0:
            set1_1 = a.allSets['NMINX'].nodes
            set2_1 = a.allSets['NMAXX'].nodes
        if Vy != 0:
            set1_1 = a.allSets['NMINY'].nodes
            set2_1 = a.allSets['NMAXY'].nodes
        if Vz != 0:
            set1_1 = a.allSets['NMINZ'].nodes
            set2_1 = a.allSets['NMAXZ'].nodes

        nameS3 = ''
        # build all the sets needed
        nameS1 = self.build_set(set1_1, a, small[0]*0.00000001)
        nameS2 = self.build_set(set2_1, a, small[0]*0.00000001)
        if(self.set3 != None):
            nameS3 = self.build_set(self.set3, a, small[0]*0.00000001)
        a.Set(referencePoints=(self.RP1,), name="RefMacro1")
        a.Set(referencePoints=(self.RP2,), name="RefMacro2")
        a.Set(referencePoints=(self.RP3,), name="RefMacro3")

        ###########################################################################
        if Vx != 0:
            nameS1 = 'NMINX'
            nameS2 = 'NMAXX'
        if Vy != 0:
            nameS1 = 'NMINY'
            nameS2 = 'NMAXY'
        if Vz != 0:
            nameS1 = 'NMINZ'
            nameS2 = 'NMAXZ'

        self.MakeNodeSetsandEquations(nameS1, nameS2, nameS3, a, dim)

        self.SuppressPickedSet(a)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def SuppressPickedSet(self, a):
        for key in a.sets.keys():
            if(key.find('Picked_set') != -1):
                del a.sets[key]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def NodeDist(self, n1, n2):
        dist = sqrt((n1.coordinates[0]-n2.coordinates[0])**2
                    + (n1.coordinates[1]-n2.coordinates[1])**2+(n1.coordinates[2]-n2.coordinates[2])**2)
        return dist
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def MakeSingleEquation(self, mod, cname, name1, name2, x1_x2, dim, is_ref):
        if(not self.is_small_strain):
            if(dim == 2):
                mod.Equation(name=cname+'_1', terms=((1.0, name1, 1), (-1.0, name2, 1), (-x1_x2[0], "RefMacro1", 1),
                                                     (-x1_x2[1], "RefMacro1", 2)))
                mod.Equation(name=cname+'_2', terms=((1.0, name1, 2), (-1.0, name2, 2), (-x1_x2[0], "RefMacro2", 1),
                                                     (-x1_x2[1], "RefMacro2", 2)))
            else:
                mod.Equation(name=cname+'_1', terms=((1.0, name1, 1), (-1.0, name2, 1), (-x1_x2[0], "RefMacro1", 1),
                                                     (-x1_x2[1], "RefMacro1", 2), (-x1_x2[2], "RefMacro1", 3)))
                mod.Equation(name=cname+'_2', terms=((1.0, name1, 2), (-1.0, name2, 2), (-x1_x2[0], "RefMacro2", 1),
                                                     (-x1_x2[1], "RefMacro2", 2), (-x1_x2[2], "RefMacro2", 3)))
                mod.Equation(name=cname+'_3', terms=((1.0, name1, 3), (-1.0, name2, 3), (-x1_x2[0], "RefMacro3", 1),
                                                     (-x1_x2[1], "RefMacro3", 2), (-x1_x2[2], "RefMacro3", 3)))
        else:
            if(dim == 2):
                mod.Equation(name=cname+'_1', terms=((1.0, name1, 1), (-1.0, name2, 1), (-x1_x2[1]*0.5, "RefMacro2", 1),
                                                     (-x1_x2[0], "RefMacro1", 1)))
                mod.Equation(name=cname+'_2', terms=((1.0, name1, 2), (-1.0, name2, 2), (-x1_x2[0]*0.5, "RefMacro2", 1),
                                                     (-x1_x2[1], "RefMacro1", 2)))
            else:
                mod.Equation(name=cname+'_1', terms=((1.0, name1, 1), (-1.0, name2, 1), (-x1_x2[0], "RefMacro1", 1),
                                                     (-x1_x2[1]*0.5, "RefMacro2", 1), (-x1_x2[2]*0.5, "RefMacro2", 2)))
                mod.Equation(name=cname+'_2', terms=((1.0, name1, 2), (-1.0, name2, 2), (-x1_x2[0]*0.5, "RefMacro2", 1),
                                                     (-x1_x2[1], "RefMacro1", 2), (-x1_x2[2]*0.5, "RefMacro2", 3)))
                mod.Equation(name=cname+'_3', terms=((1.0, name1, 3), (-1.0, name2, 3), (-x1_x2[0]*0.5, "RefMacro2", 2),
                                                     (-x1_x2[1]*0.5, "RefMacro2", 3), (-x1_x2[2], "RefMacro1", 3)))
        if(is_ref):
            mod.Equation(name=cname+'_6', terms=((1.0, name1, 6), (-1.0, name2, 6)))
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def MakeNodeSetsandEquations(self, s1, s2, s3, a, dim):
        mod = mdb.models[self.modelname]
        nodes1 = a.allSets[s1].nodes
        nodes2 = a.allSets[s2].nodes
        # print 'len nodes1 = ' + str(len(nodes1))
        # print 'len nodes2 = ' + str(len(nodes2)) # mettre un warning si differents

        nodesref1 = () #a.allSets[s1].referencePoints
        nodesref2 = () #a.allSets[s2].referencePoints

        rem = [0.]*len(nodes1)
        nodes2elem = range(len(nodes2))
        if(s3 != ""):
            for n3 in a.allSets[s3].nodes:
                j = 0
                for n1 in nodes1:
                    if(self.NodeDist(n1, n3) < 1.e-8):
                        rem[j] = 1
                    j = j+1

        x1_x2 = [0.]*3
        # mod = self.getCurrentModel(self.modelname)
        mod = mdb.models[self.modelname]
        i = 0

        mytree = Tree(self.modelname)
        mytree.getCurrentGraph('Const_')
        for n1 in nodes1:
            name1 = "Num"+str(n1.label)+n1.instanceName
            if(rem[i] == 0):
                if(a.sets.has_key(name1) == 0):
                    a.Set(nodes=nodes1[i:i+1], name=name1)
                for j in nodes2elem:
                    c2 = (nodes2[j].coordinates[0]-self.Vx, nodes2[j].coordinates[1] -
                          self.Vy, nodes2[j].coordinates[2]-self.Vz)
                    dist = sqrt((n1.coordinates[0]-c2[0])**2 +
                                (n1.coordinates[1]-c2[1])**2+(n1.coordinates[2]-c2[2])**2)
                    if(dist < 0.1*self.carac):
                        name2 = "Num"+str(nodes2[j].label)+nodes2[j].instanceName
                        nname2 = str(nodes2[j].label)+nodes2[j].instanceName
                        a.Set(nodes=nodes2[j:j+1], name=name2)
                        x1_x2[0] = n1.coordinates[0]-nodes2[j].coordinates[0]
                        x1_x2[1] = n1.coordinates[1]-nodes2[j].coordinates[1]
                        x1_x2[2] = n1.coordinates[2]-nodes2[j].coordinates[2]
                        nodes2elem.remove(j)
                        break
                # Tree construction and checking of cycling DOF's
                branch = [str(n1.label)+n1.instanceName, nname2]
                if(mytree.addBranch(branch) and not mytree.iscycle()):
                    cname = 'Const_'+str(n1.label)+n1.instanceName+'_'+str(nname2)
                    self.MakeSingleEquation(mod, cname, name1, name2, x1_x2, dim, False)
                else:
                    mytree.restoreTree()
            i = i+1
        # checking of DOF ordering to avoid undesired DOF suppression...
        self.checkMasterAndSlaves(mytree)

        # Same treatement for RefPoints
        myreftree = Tree(self.modelname)
        myreftree.getCurrentGraph('ConstRef_')
        nodes2elem = range(len(nodesref2))

        for n1 in nodesref1:
            name1 = "Ref_"+str(len(a.sets))
            nname1 = find(n1, a.referencePoints.items())
            n1coord = a.getCoordinates(n1)
            if(a.sets.has_key(name1) == 0):
                a.Set(referencePoints=(n1,), name=name1)
            for j in nodes2elem:
                n2coord = a.getCoordinates(nodesref2[j])
                c2 = (n2coord[0]-self.Vx, n2coord[1]-self.Vy, n2coord[2]-self.Vz)
                dist = sqrt((n1coord[0]-c2[0])**2+(n1coord[1]-c2[1])**2+(n1coord[2]-c2[2])**2)
                if(dist < 0.1*self.carac):
                    name2 = "Ref_"+str(len(a.sets))
                    nname2 = find(nodesref2[j], a.referencePoints.items())
                    a.Set(referencePoints=(nodesref2[j],), name=name2)
                    x1_x2[0] = n1coord[0]-n2coord[0]
                    x1_x2[1] = n1coord[1]-n2coord[1]
                    x1_x2[2] = n1coord[2]-n2coord[2]
                    nodes2elem.remove(j)
                    break
                # Tree construction and checking of cycling DOF's
            branch = [int(nname1), int(nname2)]
            if(myreftree.addBranch(branch) and not myreftree.iscycle()):
                cname = 'ConstRef_'+str(nname1)+'_'+str(nname2)
                self.MakeSingleEquation(mod, cname, name1, name2, x1_x2, dim, True)
            else:
                myreftree.restoreTree()
        self.checkMasterAndSlaves(myreftree)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def checkMasterAndSlaves(self, the_tree):
        # mod = getCurrentModel(self.modelname)
        mod = mdb.models[self.modelname]
        conts = mod.constraints
        constname = conts.keys()
        for branch in the_tree.thetree:
            for i in range(1, len(branch)):
                cname1 = the_tree.keyword+str(branch[i])+'_'+str(branch[i-1])+'_1'
                cname2 = the_tree.keyword+str(branch[i])+'_'+str(branch[i-1])+'_2'
                cname3 = the_tree.keyword+str(branch[i])+'_'+str(branch[i-1])+'_3'
                cname6 = the_tree.keyword+str(branch[i])+'_'+str(branch[i-1])+'_6'

                if(cname1 in constname):
                    theterms = conts[cname1].terms
                    if(len(theterms) == 4):
                        newterms = (theterms[1], theterms[0], theterms[2], theterms[3])
                    elif(len(theterms) > 4):
                        newterms = (theterms[1], theterms[0])+theterms[2:len(theterms)]
                    else:
                        newterms = (theterms[1], theterms[0], theterms[2], theterms[3], theterms[4])
                    conts[cname1].setValues(newterms)
                    conts.changeKey(fromName=cname1, toName=the_tree.keyword +
                                    str(branch[i-1])+'_'+str(branch[i])+'_1')
                if(cname2 in constname):
                    theterms = conts[cname2].terms
                    if(len(theterms) == 4):
                        newterms = (theterms[1], theterms[0], theterms[2], theterms[3])
                    elif(len(theterms) > 4):
                        newterms = (theterms[1], theterms[0])+theterms[2:len(theterms)]
                    else:
                        newterms = (theterms[1], theterms[0], theterms[2], theterms[3], theterms[4])
                    conts[cname2].setValues(newterms)
                    conts.changeKey(fromName=cname2, toName=the_tree.keyword +
                                    str(branch[i-1])+'_'+str(branch[i])+'_2')
                if(cname3 in constname):
                    theterms = conts[cname3].terms
                    if(len(theterms) == 4):
                        newterms = (theterms[1], theterms[0], theterms[2], theterms[3])
                    elif(len(theterms) > 4):
                        newterms = (theterms[1], theterms[0])+theterms[2:len(theterms)]
                    else:
                        newterms = (theterms[1], theterms[0], theterms[2], theterms[3], theterms[4])
                    conts[cname3].setValues(newterms)
                    conts.changeKey(fromName=cname3, toName=the_tree.keyword +
                                    str(branch[i-1])+'_'+str(branch[i])+'_3')
                if(cname6 in constname):
                    theterms = conts[cname6].terms
                    newterms = (theterms[1], theterms[0])
                    conts[cname6].setValues(newterms)
                    conts.changeKey(fromName=cname6, toName=the_tree.keyword +
                                    str(branch[i-1])+'_'+str(branch[i])+'_6')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetCarcLength(self, s1, a):
        small = 1.e8
        el1 = a.allSets[s1].elements
        for el in el1:
            tabed = el.getElemEdges()
            for ed in tabed:
                nds = ed.getNodes()
                x1 = nds[0].coordinates
                x2 = nds[1].coordinates
                dist = sqrt((x1[0]-x2[0])**2.+(x1[1]-x2[1])**2.+(x1[2]-x2[2])**2.)
                if(dist > 0 and small > dist):
                    small = dist
        return small
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def VerifNodeCoord(self, s1, s2, a):
        nodes1 = a.allSets[s1].nodes  # extrait tous les noeuds du set1
        nodes2 = a.allSets[s2].nodes  # pareil pour le set 2
        # trouve la longueur mini d'un segment sur le maillage
        self.carac = self.GetCarcLength(s1, a)
        nodes2elem = range(len(nodes2))
        for n1 in nodes1:
            found = False
            for j in nodes2elem:
                c2 = (nodes2[j].coordinates[0]-self.Vx, nodes2[j].coordinates[1] -
                      self.Vy, nodes2[j].coordinates[2]-self.Vz)
                dist = sqrt((n1.coordinates[0]-c2[0])**2. +
                            (n1.coordinates[1]-c2[1])**2.+(n1.coordinates[2]-c2[2])**2.)
                if(dist < 0.1*self.carac):
                    found = True
                    nodes2elem.remove(j)
                    break
            if(not found):
                print "The mesh periodicity is required nodeCoord"
                return False
        return True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def VerifRefCoord(self, s1, s2, a):
        a = mdb.models[self.modelname].rootAssembly
        nodes1 = a.allSets[s1].referencePoints
        nodes2 = a.allSets[s2].referencePoints
        nodes2elem = range(len(nodes2))

        for n1 in nodes1:
            found = False
            for j in nodes2elem:
                n2coord = a.getCoordinates(nodes2[j])
                n1coord = a.getCoordinates(n1)
                c2 = (n2coord[0]-self.Vx, n2coord[1]-self.Vy, n2coord[2]-self.Vz)
                dist = sqrt((n1coord[0]-c2[0])**2+(n1coord[1]-c2[1])**2+(n1coord[2]-c2[2])**2)
                if(dist < 0.1*self.carac):
                    found = True
                    nodes2elem.remove(j)
                    break
            if(not found):
                print "The mesh periodicity is required refcoord"
                return False
        return True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def CheckInput(self):
        if(self.RP1 == None):
            return False
        elif(self.set1 == None):
            return False
        elif(self.set2 == None):
            return False
        return True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setRefpoint1(self, RP1):
        self.RP1 = RP1
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setRefpoint2(self, RP2):
        self.RP2 = RP2
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def setRefpoint3(self, RP3):
        self.RP3 = RP3
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def setGroup1(self, set1):
        self.set1 = set1
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def setGroup2(self, set2):
        self.set2 = set2
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def setGroup3(self, set3):
        self.set3 = set3
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def getCurrentModel(self):
        vpName = session.currentViewportName
        # modelName = session.sessionState[vpName]['modelName']
        modelName = self.mn
        return mdb.models[modelName]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def getCurrentViewport(self):
        vpName = session.currentViewportName
        return session.viewports[vpName]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class MainFrame():
    
    def setWorkingDir(self,workdir):
        self.workdir = workdir
    def setIte(self,ite):
        self.ite = ite
        
    def __init__(self,workdir=None,ite=None):
        self.workdir = workdir
        self.ite = ite
        pass

def main(workdir, iteration):
    
    working_folder = os.path.abspath(os.path.join(workdir,os.pardir))
    os.chdir(working_folder)
    file = os.path.basename(workdir)
    name, ext = os.path.splitext(file)
    text_file_name = os.path.join(working_folder,name[0:-4]+'.e2a')
    

    homotot = [[(0.1, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)],
               [(0.0, 0.0, 0.0), (0.0, 0.1, 0.0), (0.0, 0.0, 0.0)],
               [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.1)],
               [(0.0, 0.05, 0.0), (0.05, 0.0, 0.0), (0.0, 0.0, 0.0)],
               [(0.0, 0.0, 0.05), (0.0, 0.0, 0.0), (0.05, 0.0, 0.0)],
               [(0.0, 0.0, 0.0), (0.0, 0.0, 0.05), (0.0, 0.05, 0.0)]]


    with open(text_file_name, 'r') as f:
        lines = f.readlines()
    long = float(lines[0])
    larg = float(lines[1])
    haut = float(lines[2])
    ep = float(lines[3])
    maxx = float(lines[4])
    minx = float(lines[5])
    maxy = float(lines[6])
    miny = float(lines[7])
    maxz = float(lines[8])
    minz = float(lines[9])
    # with open('matrix.csv', mode='r') as file:
    #    reader = csv.reader(file)
    #    matrix = [list(map(int, row)) for row in reader]
    # print matrix

    modelname = 'EnvelopeEnrich'
    mdb.ModelFromInputFile(name=modelname, inputFileName=workdir)

    a = mdb.models[modelname].rootAssembly
    session.viewports['Viewport: 1'].setValues(displayedObject=a)
    #mdb.models['Model-1'].parts.changeKey(fromName='PART-1', toName='RVEplus')
    p = mdb.models[modelname].parts['RVEPLUS']
    #mdb.models['Model-1'].rootAssembly.features.changeKey(fromName='PART-1-1',
    #                                                      toName='RVEplus-1')

    asetvolume2 = a.allSets['RVEPLUS-1.VOLUME2'].elements
    asetvolume3 = a.allSets['RVEPLUS-1.VOLUME3'].elements

    rve = p.Set(elements=p.elements[0:len(asetvolume2)], name='RVE')
    envlop = p.Set(elements=p.elements[len(asetvolume2):len(asetvolume2) + len(asetvolume3)], name='ENVELOPE')

    # mdb.Model(name=modelname, modelType=STANDARD_EXPLICIT)

    ###########################################
    # creation of the materials
    ###########################################

    mdb.models[modelname].Material(name='epoxy')
    mdb.models[modelname].materials['epoxy'].Elastic(type=ORTHOTROPIC, table=((
                                                                                  4.815e-10, 2.593e-10, 4.815e-10,
                                                                                  2.594e-10, 2.593e-10, 4.815e-10,
                                                                                  2.222e-10, 2.222e-10, 2.222e-10),))

    mdb.models[modelname].Material(name='enrich')
    mdb.models[modelname].materials['enrich'].Elastic(type=ANISOTROPIC, table=((
                                                                                   4.815, 2.593, 4.815, 2.593, 2.593,
                                                                                   4.815, 0, 0, 0, 2.222, 0, 0, 0, 0,
                                                                                   2.222, 0, 0, 0, 0, 0, 2.222),))
    # mdb.models[modelname].materials['enrich'].Elastic(type=ORTHOTROPIC, table=((
    #     216.594, 0.93, 9.825, 0.93, 0.38, 9.825, 9.444, 15.778, 15.778), ))
    mdb.models[modelname].Material(name='carbone')
    mdb.models[modelname].materials['carbone'].Elastic(type=ORTHOTROPIC, table=((
                                                                                    216.594, 0.93, 9.825, 0.93, 0.38,
                                                                                    9.825, 9.444, 15.778, 15.778),))

    mdb.models[modelname].Material(name='Material-1')
    mdb.models[modelname].materials['Material-1'].Elastic(table=((0.00000001, 0.3),))

    mdb.models[modelname].HomogeneousSolidSection(name='Matrix',
                                                  material='MATRIX', thickness=None)
    mdb.models[modelname].HomogeneousSolidSection(name='enrich',
                                                  material='MATRIX', thickness=None)
    mdb.models[modelname].HomogeneousSolidSection(name='void',
                                                  material='Material-1', thickness=None)
    mdb.models[modelname].HomogeneousSolidSection(name='Embedded',
                                                  material='EMBEDDED', thickness=None)

    ###########################################
    # creation of the VER
    ###########################################

    e = p.elements

    region = p.Set(elements=(e,), name='Set-1')

    dat3 = p.DatumCsysByThreePoints(name='csys-3', coordSysType=CARTESIAN, origin=(
        0.0, 0.0, 0.0), line1=(0.0, 0.0, 1.0), line2=(0.0, 1.0, 0.0))
    orientation = mdb.models[modelname].parts[p.name].datums[dat3.id]
    mdb.models[modelname].parts[p.name].MaterialOrientation(region=region,
                                                            orientationType=SYSTEM, axis=AXIS_1, localCsys=orientation,
                                                            fieldName='', additionalRotationType=ROTATION_NONE,
                                                            angle=0.0,
                                                            additionalRotationField='', stackDirection=STACK_1)

    p.SectionAssignment(region=envlop, sectionName='Matrix', offset=0.0,
                        offsetType=MIDDLE_SURFACE, offsetField='',
                        thicknessAssignment=FROM_SECTION)
    p.SectionAssignment(region=rve, sectionName='Embedded', offset=0.0,
                        offsetType=MIDDLE_SURFACE, offsetField='',
                        thicknessAssignment=FROM_SECTION)

    e = p.edges
    csys = p.DatumCsysByThreePoints(name='Datum csys-1', coordSysType=CARTESIAN, origin=(
        0.0, 0.0, 0.0), line1=(1.0, 0.0, 0.0), line2=(0.0, 1.0, 0.0))

    # region = p.sets['Set-1']
    orientation = mdb.models[modelname].parts[p.name].datums[csys.id]
    mdb.models[modelname].parts[p.name].MaterialOrientation(region=region,
                                                            orientationType=SYSTEM, axis=AXIS_1, localCsys=orientation,
                                                            fieldName='', additionalRotationType=ROTATION_NONE,
                                                            angle=0.0,
                                                            additionalRotationField='', stackDirection=STACK_1)

    ite = 1

    ##############################################
    # partition of the models
    ##############################################

    #RF1 = a.ReferencePoint(point=(minx + (long + 2 * ep) * 1.1, miny, minz))
    #RF2 = a.ReferencePoint(point=(minx + (long + 2 * ep) * 1.2, miny, minz))
    #RF3 = a.ReferencePoint(point=(minx + (long + 2 * ep) * 1.3, miny, minz))

    periodicBoundary = PeriodicBoundary(modelname)

    r1 = a.referencePoints
    f1 = a.instances['RVEPLUS-1'].nodes

    periodicBoundary.setRefpoint1(RP1=r1[5])
    periodicBoundary.setRefpoint2(RP2=r1[6])
    periodicBoundary.setRefpoint3(RP3=r1[7])

    # periodicity in X direction
    periodicBoundary.setGroup1(set1=a.allSets['NMINX'].nodes)
    periodicBoundary.setGroup2(set2=a.allSets['NMAXX'].nodes)

    periodicBoundary.Periodic(is_smallstrain=False, dim=3, Vx=(long + 2 * ep), Vy=0, Vz=0)

    # periodicity in Z direction
    periodicBoundary.setGroup1(set1=a.allSets['NMINZ'].nodes)
    periodicBoundary.setGroup2(set2=a.allSets['NMAXZ'].nodes)

    periodicBoundary.Periodic(is_smallstrain=False, dim=3, Vx=0, Vy=0, Vz=(haut + 2 * ep))

    # periodicity in Y direction
    periodicBoundary.setGroup1(set1=a.allSets['NMINY'].nodes)
    periodicBoundary.setGroup2(set2=a.allSets['NMAXY'].nodes)

    periodicBoundary.Periodic(is_smallstrain=False, dim=3, Vx=0, Vy=(larg + 2 * ep), Vz=0)
    ###########################################

    mdb.models[modelname].StaticStep(name='Step-1', previous='Initial')
    mdb.models[modelname].steps['Step-1'].setValues(maxNumInc=1000, minInc=0.000001, initialInc=0.001,
                                                    matrixSolver=DIRECT, matrixStorage=UNSYMMETRIC, amplitude=STEP)

    mdb.models[modelname].materials['epoxy'].Elastic(type=ORTHOTROPIC, table=((
                                                                                  4.815, 2.593, 4.815, 2.594, 2.593,
                                                                                  4.815, 2.222, 2.222, 2.222),))

    a = mdb.models[modelname].rootAssembly
    ###########################################
    # creation of the embedded elements
    ###########################################

    # p1 = mdb.models[modelname].PartFromInputFile(inputFileName='%s.inp' %str(filename2))
    # p1 = mdb.models[modelname].parts['PART-1']
    #
    # mdb.models[modelname].parts.changeKey(fromName='PART-1', toName='Embedded')
    p1 = mdb.models[modelname].parts['EMBEDDED']

    e1 = p1.elements

    region = p1.Set(elements=(e1,), name='Set-2')

    p1.SectionAssignment(region=region, sectionName='Embedded', offset=0.0,
                         offsetType=MIDDLE_SURFACE, offsetField='',
                         thicknessAssignment=FROM_SECTION)

    dat4 = p1.DatumCsysByThreePoints(name='csys-3', coordSysType=CARTESIAN, origin=(
        0.0, 0.0, 0.0), line1=(0.0, 0.0, 1.0), line2=(0.0, 1.0, 0.0))
    orientation = mdb.models[modelname].parts[p1.name].datums[dat4.id]
    mdb.models[modelname].parts[p1.name].MaterialOrientation(region=region,
                                                             orientationType=SYSTEM, axis=AXIS_1, localCsys=orientation,
                                                             fieldName='', additionalRotationType=ROTATION_NONE,
                                                             angle=0.0,
                                                             additionalRotationField='', stackDirection=STACK_1)

    a.Instance(name='EMBEDDED-1', part=p1, dependent=ON)

    c1 = a.instances['EMBEDDED-1'].cells
    a.Set(cells=c1, name='Set-cells-fiber')

    region1 = a.sets['EMBEDDED-1.Set-2']
    region2 = a.sets['RVEPLUS-1.Set-1']
    mdb.models[modelname].EmbeddedRegion(name='Constraint-1',
                                         embeddedRegion=region1, hostRegion=region2,
                                         weightFactorTolerance=1e-06, absoluteTolerance=0.0,
                                         fractionalTolerance=0.1, toleranceMethod=FRACTIONAL)

    compMat = [[216.594, 0.93, 0.93, 0, 0, 0],
               [0.93, 9.825, 0.38, 0, 0, 0],
               [0.93, 0.38, 9.825, 0, 0, 0],
               [0, 0, 0, 9.444, 0, 0],
               [0, 0, 0, 0, 15.778, 0],
               [0, 0, 0, 0, 0, 15.778]]
    matMat = [[4.815, 2.594, 2.594, 0, 0, 0],
              [2.593, 4.815, 2.594, 0, 0, 0],
              [2.594, 2.594, 4.815, 0, 0, 0],
              [0, 0, 0, 2.222, 0, 0],
              [0, 0, 0, 0, 2.222, 0],
              [0, 0, 0, 0, 0, 2.222]]

    sd = compMat
    for k in range(3):
        for l in range(6):
            sd[k][l] = sd[k][l] - matMat[k][l]
    sd = matMat
    ite_job = 1
    idx = [0, 4, 8, 1, 2, 5]
    for i in range(iteration):
        if i > 0:
            name = 'PBC-%s-%d.dat' % (name[0:-4], i)
            f = open(name, 'r')
            data = f.read()
            splitdata = (data.split())
            floatdata = []
            for uniqueName in splitdata:
                floatdata.append(float(uniqueName))
            sd = np.reshape(floatdata, (6, 6))
            f.close()

        C = []
        CC = [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]

        s11 = sd[0][0]
        s12 = sd[0][1]
        s22 = sd[1][1]
        s13 = sd[0][2]
        s23 = sd[1][2]
        s33 = sd[2][2]
        s14 = sd[0][3]
        s24 = sd[1][3]
        s34 = sd[2][3]
        s44 = sd[3][3]
        s15 = sd[0][4]
        s25 = sd[1][4]
        s35 = sd[2][4]
        s45 = sd[3][4]
        s55 = sd[4][4]
        s16 = sd[0][5]
        s26 = sd[1][5]
        s36 = sd[2][5]
        s46 = sd[3][5]
        s56 = sd[4][5]
        s66 = sd[5][5]

        mdb.models[modelname].materials['enrich'].Elastic(type=ANISOTROPIC, table=((
                                                                                       s11, s12, s22, s13, s23, s33,
                                                                                       s14, s24, s34, s44, s15, s25,
                                                                                       s35, s45, s55, s16, s26, s36,
                                                                                       s46, s56, s66),))

        a = mdb.models[modelname].rootAssembly

        region1 = a.sets['RefMacro1']
        region2 = a.sets['RefMacro2']
        region3 = a.sets['RefMacro3']

        job_namess = []

        for DefMat in homotot:
            mdb.models[modelname].DisplacementBC(name='BC-1', createStepName='Step-1',
                                                 region=region1, u1=DefMat[0][0], u2=DefMat[0][
                    1], u3=DefMat[0][2], ur1=UNSET, ur2=UNSET, ur3=UNSET,
                                                 amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                                                 localCsys=None)

            mdb.models[modelname].DisplacementBC(name='BC-2', createStepName='Step-1',
                                                 region=region2, u1=DefMat[1][0], u2=DefMat[1][
                    1], u3=DefMat[1][2], ur1=UNSET, ur2=UNSET, ur3=UNSET,
                                                 amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                                                 localCsys=None)

            mdb.models[modelname].DisplacementBC(name='BC-3', createStepName='Step-1',
                                                 region=region3, u1=DefMat[2][0], u2=DefMat[2][
                    1], u3=DefMat[2][2], ur1=UNSET, ur2=UNSET, ur3=UNSET,
                                                 amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                                                 localCsys=None)
            mdb.models[modelname].fieldOutputRequests['F-Output-1'].setValues(
                variables=('S', 'U', 'RF', 'IVOL', 'EE', 'SENER'))

            name = 'Job-' + str(ite_job)
            job_namess.append(name)

            mdb.Job(name=name, model=modelname, description='', type=ANALYSIS,
                    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
                    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, numCpus=1,
                    echoPrint=OFF, modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
                    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT,
                    numGPUs=0)  # explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE,
            mdb.jobs[name].submit(consistencyChecking=OFF)
            ite_job = ite_job + 1

        for result in job_namess:
            mdb.jobs[name].waitForCompletion()
            odb = openOdb(result + '.odb')
            lastFrame = odb.steps['Step-1'].frames[-1]
            first_set = odb.rootAssembly.instances['ASSEMBLY']
            allFields = lastFrame.fieldOutputs

            elsetname = 'RVEPLUS-1.VOLUME3'

            phase = odb.rootAssembly.elementSets[elsetname]  # faire l'iteration pour les deux sets de RVE et envelope
            jacobien = lastFrame.fieldOutputs['IVOL']
            jac = jacobien.getSubset(position=INTEGRATION_POINT, region=phase)
            det = jac.values

            b = 0
            for t in det:
                b = b + t.data

            elsetname = 'RVEPLUS-1.VOLUME2'

            phase = odb.rootAssembly.elementSets[elsetname]  # faire l'iteration pour les deux sets de RVE et envelope
            jacobien = lastFrame.fieldOutputs['IVOL']
            jac = jacobien.getSubset(position=INTEGRATION_POINT, region=phase)
            det = jac.values

            for t in det:
                b = b + t.data

            print
            'volume : ' + str(b)

            if (allFields.has_key('RF')):
                ReactionForce = allFields['RF']
                ite = 0
                data = []
                for value in ReactionForce.values:
                    if (value.nodeLabel < 4) and (ite < 3):
                        for val in value.data:
                            data.append(10 * val / b)
                            # data = data + val
                        ite = ite + 1
            sorteddata = []
            for d in range(len(idx)):
                sorteddata.append(data[idx[d]])
            C.append(sorteddata)
            print(C)
            odb.close()

        f = open('PBC-%s-%d.dat' % (name[0:-4], i + 1), 'w')
        for val in C:
            for subval in val:
                f.write(str(subval) + ' ')
            f.write('\n')
        f.close()
        print
        'finished : ' + modelname



### settings for the homogenezation
#filename = ['']
#
#
#root = Tk()
#root.withdraw()
#root.directory = tkFileDialog.askdirectory()
#print(root.directory)
#os.chdir(root.directory)
#
#
#foldernames = os.listdir(root.directory)
#
#iteration = sys.argv[1]
#
#for folder in foldernames:
#    pathfolder = os.path.join(root.directory,folder)
#    os.chdir(pathfolder)
#    filenames = os.listdir(root.directory)
#    i = 0
#    #if '-VER' not in name and name.endswith('.inp'):
#    #file_embed, ext = os.path.splitext(name)
#    file_embed = folder
#    file_RVE = file_embed + '-VER'
#    file_orient = file_embed + '-orient'
#    t = MainFrame(i+1,file_RVE,file_embed, iteration)
#    i = i+1
#