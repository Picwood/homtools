#-----------------------------------------------------------------------
#     Plugin for periodic condition on the boundary
#-----------------------------------------------------------------------
#     Authors: Stephane Lejeunes,  Stephane Bourgeois, Florian Vazeille
#     Institute: LMA UPR7051, CNRS, LABSFCA, Polytechnique Montreal
#     Date: 26/07/2023
#
#-----------------------------------------------------------------------
from abaqusGui import *
from kernelAccess import mdb, session
import i18n
########################################################################
# Class definition
########################################################################
class PeriodicForm(AFXForm):
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, owner):

        AFXForm.__init__(self, owner)
                
        self.cmd = AFXGuiCommand(self, 'Periodic', 'periodicBoundary_e')
        #self.dim=AFXIntKeyword(self.cmd, 'dim',3)
        self.thickness = AFXFloatKeyword(self.cmd, 'Thickness', TRUE,1.0)
        self.density = AFXFloatKeyword(self.cmd, 'Density', TRUE,1.0)
        #self.inputPart = AFXFloatKeyword(self.cmd, 'Inputpart',AFXBoolKeyword.TRUE_FALSE, TRUE,TRUE)
        self.owner=owner
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getFirstDialog(self):
        vpName = session.currentViewportName
        modelName = session.sessionState[vpName]['modelName']
        m=mdb.models[modelName]
        a = m.rootAssembly
        #self.dim.setValue(3)
            
        #if(a.getMassProperties()['volume']==None): 
        #    self.dim.setValue(2)  # adapter la methode au cas 2D ensuite
        #    self.presentPart.setValue(False)
        db = PeriodicDB(self)
        return db

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PeriodicDB(AFXDataDialog):
    [
        createRVE,
        homo
    ] = range(AFXDataDialog.ID_LAST, AFXDataDialog.ID_LAST+2)
    def __init__(self, form):
        sendCommand("periodicBoundary_e.__init__()")
        
        self.step2=None
        AFXDataDialog.__init__(self, form, 'Periodic conditions on the boundary', self.OK|self.CANCEL)
                      
        vf = FXVerticalFrame(self,  LAYOUT_FILL_Y|LAYOUT_FILL_X)

        gb = FXGroupBox(vf, 'Input microstructure', LAYOUT_FILL_X|FRAME_GROOVE)
        gb1 = FXGroupBox(vf, 'Envelope Parameter', LAYOUT_FILL_X|FRAME_GROOVE)
        hf = FXMatrix(gb, 2,opts=MATRIX_BY_COLUMNS|LAYOUT_FILL_X|LAYOUT_FILL_Y)
        FXLabel(hf,'test',opts=JUSTIFY_LEFT|LAYOUT_FILL_X|LAYOUT_FILL_COLUMN)
    
        hf2 = FXMatrix(gb1, 2,opts=MATRIX_BY_COLUMNS|LAYOUT_FILL_X|LAYOUT_FILL_Y)        
        FXLabel(hf2,'Create the enveloped RVE',opts=JUSTIFY_LEFT|LAYOUT_FILL_X|LAYOUT_FILL_COLUMN)
        FXButton(hf2, 'Go',None,self,self.createRVE,opts=LAYOUT_RIGHT|BUTTON_NORMAL)
        FXLabel(hf2, 'Homogenized',opts=JUSTIFY_LEFT|LAYOUT_FILL_X|LAYOUT_FILL_COLUMN)
        FXButton(hf2, 'Go',None,self,self.homo,opts=LAYOUT_RIGHT|BUTTON_NORMAL)


        FXMAPFUNC(self,SEL_COMMAND,self.createRVE,PeriodicDB.onCmdRVEE)
        FXMAPFUNC(self,SEL_COMMAND,self.homo,PeriodicDB.onCmdHomo)
        
        self.form=form
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def onCmdRVEE(self,sender,sel,ptr):
        self.step2=createRVE(self.form.owner)
        self.step2.activate()
        return 1
    def onCmdHomo(self,sender,sel,ptr):
        self.step2=createRVE(self.form.owner)
        self.step2.activate()
        return 1
    
class createRVE(AFXProcedure):
    def __init__(self,  owner):
        AFXProcedure.__init__(self, owner=owner)
        self.cmd = AFXGuiCommand(self, 'createRVE', 'periodicBoundary_e')
    def getFirstStep(self):
        return True

#class homogenize(AFXProcedure):
#    def __init__(self,  owner):
#        AFXProcedure.__init__(self, owner=owner)
#        self.cmd = AFXGuiCommand(self, 'homo', 'periodicBoundary_e')
        
import os
absPath = os.path.abspath(__file__)
absDir  = os.path.dirname(absPath)
helpUrl = os.path.join(absDir, 'www.lma.cnrs-mrs.fr')

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()

# Register a GUI plug-in in the Plug-ins menu.
#
toolset.registerGuiMenuButton(
    object=PeriodicForm(toolset), buttonText=i18n.tr('HHomtools|PBC envelope'),
    kernelInitString='import periodicBoundary_e; periodicBoundary_e=periodicBoundary_e.PeriodicBoundary_e()',
    version='1.0', author='S. Lejeunes & S. Bourgeois (LMA-CNRS UPR7051) & F. Vazeille',
    applicableModules = ['Part','Interaction'],
    description='A simple Gui to define periodic Boundary Conditions '
                "This plug-in's files may be copied from " + absDir,
    helpUrl=helpUrl
)

