# code to create an envelope and RVE around an inp file for enrichment homogenization


import gmsh
import math
import os
import sys
import re
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilenames
from tkinter.filedialog import askdirectory
from create_model_inp import main_combine


def main(ep, density, dimension, mat_def):
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    files = askopenfilenames(filetypes = [('Input files','*.inp')]) #list or not 
    working_folder = os.path.abspath(os.path.join(files[0],os.pardir))
    os.chdir(working_folder)
    for file in files:
        file = os.path.basename(file)
        name, ext = os.path.splitext(file)
    
        # Create a folder with the same name as the file
        subfolder_name = name
        if not os.path.exists(subfolder_name):
            os.mkdir(subfolder_name)
        # Move the file into the folder
        os.rename(file, os.path.join(subfolder_name, file))
        try:
            name_orient = name + '-orient.dat'
            os.rename(name_orient, os.path.join(subfolder_name,name_orient))
    
        except:
            False
    
        # name_embedded = 'fiber-1'
        name_embedded = 'hexagonal'
        re_number = re.compile(r'(\d*)\s\d*\s\d*\s\d*', re.VERBOSE)
        re_pos_inp = re.compile(r'\s*\d*\,\s*(\S+\.?\d*)\,\s+(\S+\.?\d*)\,\s+(\S+\.?\d*)', re.VERBOSE)  # inpfile
        re_pos_msh = re.compile(r'\d*\s(\S+\.?\d*)\s(\S+\.?\d*)\s(\S+\.?\d*)\s0+?',re.VERBOSE) #mshfile
        re_numset = re.compile(r'(\d+)(?:,)?')
    
        with open(subfolder_name+'//'+file, 'r') as f:
            lines = f.readlines()
    
        x = []
        y = []
        z = []
        indl = 5
        if file.endswith('.inp'):
            pos = re_pos_inp.search(lines[indl])
            while pos != None:
                x.append(float(pos.group(1)))
                y.append(float(pos.group(2)))
                z.append(float(pos.group(3)))
                indl = indl+1
                pos = re_pos_inp.search(lines[indl])
        elif file.endswith('.msh'):
            pos = re_pos_msh.search(lines[indl])
            while pos != None:
                x.append(float(pos.group(1)))
                y.append(float(pos.group(2)))
                z.append(float(pos.group(3)))
                indl = indl+1
                pos = re_pos_msh.search(lines[indl])
        
        gmsh.initialize()
        gmsh.model.add("t18")
    
        # Let's use the OpenCASCADE geometry kernel to build two geometries.
    
        long = max(x)-min(x)
        larg = max(y)-min(y)
        haut = max(z)-min(z)
        indens = density
        outdens = density
    
        # We can log all messages for further processing with:
        gmsh.logger.start()
    
        # We first create two cubes:
        outbox = gmsh.model.occ.addBox(0, 0, 0,
                                       (long+2*ep), (larg+2*ep), (haut+2*ep), 1)
    
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0), outdens)
    
        # To impose that the mesh on surface 2 (the right side of the cube) should
        # match the mesh from surface 1 (the left side), the following periodicity
        # constraint is set:
        translation = [1, 0, 0, long+2*ep,    0, 1, 0, 0,     0, 0, 1, 0,    0, 0, 0, long+2*ep]
        gmsh.model.mesh.setPeriodic(2, [2], [1], translation)
        # The periodicity transform is provided as a 4x4 affine transformation matrix,
        # given by row.
    
        # During mesh generation, the mesh on surface 2 will be created by copying
        # the mesh from surface 1.
    
        # Multiple periodicities can be imposed in the same way:
        gmsh.model.mesh.setPeriodic(2, [4], [3],
                                    [1, 0, 0, 0,   0, 1, 0, larg+2*ep,   0, 0, 1, 0,   0, 0, 0, larg+2*ep])
        gmsh.model.mesh.setPeriodic(2, [6], [5],
                                    [1, 0, 0, 0,   0, 1, 0, 0,   0, 0, 1, haut+2*ep,   0, 0, 0, haut+2*ep])
    
        inbox = gmsh.model.occ.addBox(0, 0, 0, (long), (larg), (haut), 2)
        gmsh.model.occ.translate([(3, 1)], -ep, -ep, -ep)
    
        ov, ovv = gmsh.model.occ.fragment([(3, 2)], [(3, 1)])
        gmsh.model.occ.translate(ov, min(x), min(y), min(z))
        gmsh.model.occ.synchronize()
    
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)
    
        gmsh.model.addPhysicalGroup(3, [0], 1)
        gmsh.model.addPhysicalGroup(3, [1], 2)
    
        # The tag of the cube will change though, so we need to access it
        # programmatically:
    
        # Override this constraint on the points of the five spheres:
        gmsh.model.mesh.setSize(gmsh.model.getBoundary([(3, 2)], False, False, True),
                                indens)
    
        transfinite = True
        transfiniteAuto = True
    
        if transfinite:
            NN = int(10/density)
            inte = 0
            for c in gmsh.model.getEntities(1):
                if inte >= 12:
                    gmsh.model.mesh.setTransfiniteCurve(c[1], NN)
                inte = inte+1
            inte = 0
            for s in gmsh.model.getEntities(2):
                if inte >= 6:
                    gmsh.model.mesh.setTransfiniteSurface(s[1])
                    # gmsh.model.mesh.setRecombine(s[0], s[1])
                    # gmsh.model.mesh.setSmoothing(s[0], s[1], 100)
                inte = inte+1
    
        # gmsh.model.occ.synchronize()
        gmsh.option.setNumber('Mesh.SaveGroupsOfElements', -1001)
        
        gmsh.model.mesh.generate(3)
    
    
    
        filepath_inp = os.path.join(working_folder, subfolder_name, '%s-VER.inp' %(name))
        filepath_txt = os.path.join(working_folder, subfolder_name, '%s.e2a' %(name))
    
        gmsh.write(filepath_inp)
        #gmsh.write('C://temp//%s-VER.msh' %(name))
    
        with open(filepath_txt, 'w') as f:
            #f.writelines('%s.inp' %(name)+ '\n')
            #f.writelines('%s-VER.inp' %(name) + '\n')
            #f.writelines('%s-VER.inp' %(name)) for orient purpose
            f.writelines(str(long)+'\n')
            f.writelines(str(larg)+'\n')
            f.writelines(str(haut)+'\n')
            f.writelines(str(ep)+'\n')
            f.writelines(str(max(x))+'\n')
            f.writelines(str(min(x))+'\n')
            f.writelines(str(max(y))+'\n')
            f.writelines(str(min(y))+'\n')
            f.writelines(str(max(z))+'\n')
            f.writelines(str(min(z))+'\n')
    
        top = []
        bottom = []
        front = []
        back = []
        left = []
        right = []
    
        nodesetname = ['maxy', 'miny', 'minz', 'maxz', 'maxx', 'minx']
    
        maxx = max(x)
        minx = min(x)
        maxy = max(y)
        miny = min(y)
        maxz = max(z)
        minz = min(z)
    
        with open(filepath_inp, "r") as f:
            lines = f.readlines()
            x = []
            y = []
            z = []
            indl = 3
            pos = re_pos_inp.search(lines[indl])
            while pos != None:
                x.append(float(pos.group(1)))
                y.append(float(pos.group(2)))
                z.append(float(pos.group(3)))
    
                if math.isclose(x[-1], minx-ep, rel_tol=1e-8):
                    right.append(indl-2)
                elif math.isclose(x[-1], maxx+ep, rel_tol=1e-8):
                    left.append(indl-2)
                if math.isclose(y[-1], miny-ep, rel_tol=1e-8):
                    bottom.append(indl-2)
                elif math.isclose(y[-1], maxy+ep, rel_tol=1e-8):
                    top.append(indl-2)
                if math.isclose(z[-1], minz-ep, rel_tol=1e-8):
                    front.append(indl-2)
                elif math.isclose(z[-1], maxz+ep, rel_tol=1e-8):
                    back.append(indl-2)
                indl = indl+1
                pos = re_pos_inp.search(lines[indl])
    
        nodelist = [top, bottom, front, back, left, right]
    
        lite = 0
        listite = 0
        lv = 4
        for list in nodelist:
            lines.insert(indl+lite, '*NSET,NSET=N%s\n' % nodesetname[listite])
            for i in range(math.ceil(len(list)/lv)):
                val = str(list[lv*i:min(len(list),lv*(i+1))])
                if val != '[]':
                    lines.insert(indl+lite+1, val[1:len(val)-1]+',\n')
                    lite = lite + 1
            lite = lite + 1
            listite = listite + 1
            
        mat_name = ['Matrix', 'Embedded']
        i=-1
        with open(filepath_inp, "w") as f:
            
            contents = "".join(lines)
            f.write(contents)
            f.writelines('**\n** MATERIALS\n**')
            for key in mat_def.keys():
                i = i+1
                f.writelines('\n*Material, name=%s\n' %mat_name[i])
                if 'Elastic' in key:
                    f.writelines('*Elastic\n')
                elif 'Eng constant' in key:
                    f.writelines('*Elastic, type=ENGINEERING CONSTANTS\n')
                elif 'Orthotropic' in key:
                    f.writelines('*Elastic, type=ORTHOTROPIC\n')
                f.writelines(', '.join(mat_def[key]))
            
            
    
        gmsh.finalize()
        main_combine(os.path.join(subfolder_name, file),filepath_inp)

#ep = float(sys.argv[1])
#density = float(sys.argv[1])
#dimension = sys.argv[2]

# file1 = open('D://1-Maitrise Recherche//Abaqus//rveTEST.msh', 'r')

#for file in files:
#    if '' in file:
#        files.remove(file)
# add a check to remove any file named Job-XX.inp

#main(working_folder,files,ep,density,dimension)