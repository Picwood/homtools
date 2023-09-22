import re
import os
import sys

class MeshData:
    def __init__(self):
        self.nodes = {}
        self.elements = []
        self.nodeSets = {}
        self.elemsets = {}
        self.minpos = [float('inf')] * 3  # Initialized to a very large value
        self.maxpos = [float('-inf')] * 3

    def add_node(self, node_id, coordinates):
        self.nodes[node_id] = coordinates
        coord = list(coordinates)
        for i in range(3):
            # Update minpos for each coordinate
            if self.minpos[i] > coord[i]:
                self.minpos[i] = coord[i]
            # Update maxpos for each coordinate
            if self.maxpos[i] < coord[i]:
                self.maxpos[i] = coord[i]
                
    def get_minmax_coordinates(self):
        return self.minpos, self.maxpos
        
    def add_element(self, element_id, element_type, support_nodes,elset):
        self.elements.append({
            'element_id': element_id,
            'element_type': element_type,
            'support_nodes': support_nodes
        })
        if elset != '':
            self.add_elements_to_elemset(elset,element_id)
        
    def get_elements_by_type(self, element_type):
        return [element for element in self.elements if element['element_type'] == element_type]
    
    def add_nodeSet(self, name, nodeSet_data):
        if name not in self.nodeSets:
            self.nodeSets[name] = []
        try:
            self.nodeSets[name].extend(nodeSet_data)
        except:
            self.nodeSets[name].append(nodeSet_data)
        
    def add_elements_to_elemset(self, name, elements):
        if name not in self.elemsets:
            self.elemsets[name] = []
        try:
            self.elemsets[name].extend(elements)
        except:
            self.elemsets[name].append(elements)
        
    def get_elem_from_set(self,elemset_name):
        return self.elemsets.get(elemset_name, [])


class ElemSet:
    def __init__(self, name):
        self.name = name
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)

    def get_elements(self):
        return self.elements

def nameSet(line):
    re_nameSet = re.compile(r'(?:\*ELEMENT\,\stype\=\w*)(?:,\ ELSET=([\w]*))?')
    res = re_nameSet.search(line).group(1)
    return res

def parse_file(filename):
    re_type_elem = re.compile(r'\*ELEMENT\,\stype\=(\w*)')
    re_nodeSet_name = re.compile(r'\*NSET\,NSET\=(\w*)')
    mesh = MeshData()
    material = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        element_type = ''
        is_node_section = False
        is_nodeset_section = False
        is_element_section = False
        is_material_section = False
        for line in lines:
            if "*Node" in line or "*NODE" in line:
                is_node_section = True
                is_nodeset_section = False
                is_element_section = False
                is_material_section = False
            elif "*NSET" in line:
                nodeSet_name = re_nodeSet_name.search(line).group(1)
                is_node_section = False
                is_nodeset_section = True
                is_element_section = False
                is_material_section = False
            elif "*ELEMENT" in line:
                element_type = findElemType(line)
                if nameSet(line) != None:
                    elset = nameSet(line)
                else:
                    elset = ''
                is_node_section = False
                is_nodeset_section = False
                is_element_section = True
                is_material_section = False
            elif "** MATERIALS" in line:
                is_node_section = False
                is_nodeset_section = False
                is_element_section = False
                is_material_section = True
            elif "*" in line and '*Material' not in line and '*Elastic' not in line:  # Any other section
                is_node_section = False
                is_element_section = False
            elif is_node_section:
                parts = line.strip().split(',')
                node_id = int(parts[0])
                coords = tuple(map(float, parts[1:]))
                mesh.add_node(node_id, coords)
            elif is_nodeset_section:
                parts = line.strip().split(',')
                parts.remove('')
                nodes_in_set = list(map(int, parts))
                mesh.add_nodeSet(nodeSet_name,nodes_in_set)
            elif is_element_section:
                parts = line.strip().split(',')
                element_id = int(parts[0])
                support_nodes = list(map(int, parts[1:]))
                mesh.add_element(element_id, element_type, support_nodes,elset)
            elif is_material_section:
                material.append(line)
    return mesh, material


def linetype(line,re_node,re_elem,re_type_elem):
    
    if re_node.search(line) != None:
        return 'data'
    if re_elem.search(line) != None:
        return 'data'
    if re_type_elem.search(line) != None:
        return 'elemType'
    
def find_line_number(filename, pattern):
    with open(filename, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if re.search(pattern, line):
                return line_num
            return None
def findElemType(line):
    re_elemType = re.compile(r'(\*ELEMENT\,\stype\=\w*)(?:,\ ([\w,=]*))?')
    res = re_elemType.search(line).group(1)
    return res
def main_combine(file1,file2):
    inp_data1, material1 = parse_file(file1)
    inp_data2, material2 = parse_file(file2)
    
    re_number = re.compile(r'(\d*)\s\d*\s\d*\s\d*', re.VERBOSE)
    re_node = re.compile(r'^\s*\d*\,\s*(\S+\.?\d*)\,\s+(\S+\.?\d*)\,\s+(\S+\.\d*)', re.VERBOSE) # inpfile
    re_elem = re.compile(r'(\d+(?:,\s*\d+)+)', re.VERBOSE)
    re_numset = re.compile(r'(\d+)(?:,)?')
    re_type_elem = re.compile(r'\*ELEMENT\,\stype\=(\w*)')
    
    
    heading = "*Heading\n** PARTS\n**\n*Part, name=Embedded \n*Node \n" #modify
    
    node1 = []
    elem1 = []
    elset1 = []
    elset2 = []
          
    ############################################################
    # writing file
    ############################################################
    working_folder = os.path.abspath(os.path.join(file1,os.pardir))
    file = os.path.basename(file1)
    name, ext = os.path.splitext(file)
    subfolder_name = name
    filepath_env = os.path.join(working_folder, '%s-env.inp' %(name))
    print(filepath_env)
    with open(filepath_env, 'w') as f:
        f.writelines("*Heading\n** Job name: Job-40 Model name: Model-1\n** Generated by: Abaqus/CAE 2022\n**\n** PARTS\n**\n*Part, name=Embedded\n*Node\n")
        
        # Example: Printing out the parsed data
        for node_id, coords in inp_data1.nodes.items():
            f.writelines(str(node_id) + ', ' + ', '.join(map(str, coords))+'\n')            
        elemtype = inp_data1.elements[0]['element_type']
        f.writelines(elemtype+'\n')
        for elem in inp_data1.elements:
            if elem['element_type'] != elemtype:
                f.writelines(elem['element_type'])
            f.writelines(str(elem['element_id'])+ ', ' + ', '.join(map(str, elem['support_nodes'] ))+'\n')
            
        #for nameSet in list(inp_data1.elemsets.keys()):
        #    f.writelines('*Elset, elset=%s, generate\n' %(nameSet))
        #    elem_from_set = list(inp_data1.elemsets[nameSet])
        #    for i in range(0, len(elem_from_set), 4):
        #        row_elements = elem_from_set[i:i+4]
        #        f.writelines(', '.join(map(str, row_elements))+'\n')
            
            
        f.writelines('*End Part\n**\n*Part, name=RVEplus\n*Node\n')
        for node_id, coords in inp_data2.nodes.items():
            f.writelines(str(node_id) + ', ' + ', '.join(map(str, coords))+'\n')
        elemtype = inp_data2.elements[0]['element_type']
        f.writelines(elemtype+'\n')
        for elem in inp_data2.elements:
            if elem['element_type'] != elemtype:
                f.writelines(elem['element_type'])
            f.writelines(str(elem['element_id'])+ ', ' + ', '.join(map(str, elem['support_nodes'] ))+'\n')
        for nameSet in list(inp_data2.elemsets.keys()):
            f.writelines('*Elset, elset=%s\n' %(nameSet))
            elem_from_set = list(inp_data2.elemsets[nameSet])
            for i in range(0, len(elem_from_set), 4):
                row_elements = elem_from_set[i:i+4]
                f.writelines(', '.join(map(str, row_elements))+'\n')
        #f.writelines('** Section: matrice\n*Solid Section, elset=RVE, orientation=Ori-2, stack direction=1, material=epopo\n')
        #f.writelines('** Section: enrich\n*Solid Section, elset=ENVELOPE, orientation=Ori-2, stack direction=1, material=enrich\n')
        f.writelines('*End Part\n**\n**\n** ASSEMBLY\n**\n*Assembly, name=Assembly\n**\n*Instance, name=RVEplus-1, part=RVEplus\n*End Instance\n**\n*Instance, name=Embedded-1, part=Embedded\n')
#add step for translation (check the coordinates)..
        f.writelines('*End Instance\n**\n')
        long = inp_data1.maxpos[0]-inp_data1.minpos[0]
        f.writelines('*Node\n1, %f, %f, %f\n' %(inp_data1.minpos[0]+1.2*long,inp_data1.minpos[1],inp_data1.minpos[2]))
        f.writelines('*Node\n2, %f, %f, %f\n' %(inp_data1.minpos[0]+1.4*long,inp_data1.minpos[1],inp_data1.minpos[2]))
        f.writelines('*Node\n3, %f, %f, %f\n' %(inp_data1.minpos[0]+1.6*long,inp_data1.minpos[1],inp_data1.minpos[2]))
        
        #add ref points according to the dimensions
        
        for nodeSet in inp_data2.nodeSets:
            f.writelines('*Nset, nset=%s, instance=RVEplus-1\n' %nodeSet)
            node_from_set = list(inp_data2.nodeSets[nodeSet])
            for i in range(0, len(node_from_set), 16):
                row_elements = node_from_set[i:i+16]
                f.writelines(', '.join(map(str, row_elements))+'\n')
        f.writelines('*Nset, nset=RefMacro1\n1,\n*Nset, nset=RefMacro2\n2,\n*Nset, nset=RefMacro3\n3,\n')
        f.writelines('*Elset, elset=VOLUME2, instance=RVEplus-1\n')
        elemVol2 = inp_data2.get_elem_from_set('Volume2')
        f.writelines(str(min(elemVol2)) + ', ' + str(max(elemVol2)) + ', 1\n')
        f.writelines('*Elset, elset=VOLUME3, instance=RVEplus-1\n')
        elemVol3 = inp_data2.get_elem_from_set('Volume3')
        f.writelines(str(min(elemVol3)) + ', ' + str(max(elemVol3)) + ', 1\n')
        #f.writelines('*Elset, elset=Set-1\n')
        #f.writelines(str(min(elemVol2)) + ', ' + str(max(elemVol3)) + ', 1\n')
        #f.writelines('** Constraint: Constraint-1\n*Embedded Element, host elset=RVEplus-1.Set-1, exterior tolerance=0.1\nEmbedded-1.Set-2\n')
        f.writelines('*End Assembly\n**\n')
        for line in material2:
            f.writelines(line)
        
        #f.writelines('** ----------------------------------------------------------------\n**\n** STEP: Step-1\n**\n')
        #f.writelines('*Step, name=Step-1, nlgeom=NO, amplitude=STEP, inc=1000, unsymm=YES\n*Static\n**\n')
        #f.writelines('**\n** OUTPUT REQUESTS\n**\n*Restart, write, frequency=0\n**\n** FIELD OUTPUT: F-Output-1\n**\n*Output, field\n*Node Output\n**\n')
        #f.writelines('*Output, field\n*Node Output\nRF, U\n*Element Output, directions=YES\n**\n** HISTORY OUTPUT: H-Output-1\n**\n*Output, history, variable=PRESELECT\n*End Step')
        
        
        
#file1 = 'C:/temp/fiber-9.inp'
#file2 = 'C:/temp/fiber-9-VER.inp'

# Usage


#main_combine(file1,file2)