from __main__ import vtk, qt, ctk, slicer

import numpy
import SimpleITK as sitk
from math import *

from slicer.ScriptedLoadableModule import *

import os


class AnglePlanes(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Angle Planes"
        parent.categories = ["Shape Analysis"]
        parent.dependencies = []
        parent.contributors = ["Julia Lopinto"]
        parent.helpText = """
            This Module is used to calculate the angle between two planes by using the normals.
            The user gets the choice to use two planes which are already implemented on Slicer
            or they can define a plane by using landmarks (at least 3 landmarks).
            Plane can also be saved to be reused for other models.
            This is an alpha version of the module.
            It can't be used for the moment.
            """
        
        parent.acknowledgementText = """
            This work was supported by the National
            Institutes of Dental and Craniofacial Research
            and Biomedical Imaging and Bioengineering of
            the National Institutes of Health under Award
            Number R01DE024450.
            """
        
        self.parent = parent


class AnglePlanesWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.moduleName = "AnglePlanes"
        self.i = 0
        self.logic = AnglePlanesLogic()
        # self.logic.initializePlane()
        
        self.n_vector = numpy.matrix([[0], [0], [1], [1]])
        
        self.interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        #Definition of the 2 planes

        # Collapsible button -- Scene Description
        self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
        self.loadCollapsibleButton.text = "Scene"
        self.layout.addWidget(self.loadCollapsibleButton)

        # Layout within the laplace collapsible button
        self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

        #--------------------------- List of Models --------------------------#

        treeView = slicer.qMRMLTreeView()
        treeView.setMRMLScene(slicer.app.mrmlScene())
        treeView.setSceneModelType('Displayable')
        treeView.sceneModel().setHorizontalHeaderLabels(["Models"])
        treeView.sortFilterProxyModel().nodeTypes = ['vtkMRMLModelNode']
        header = treeView.header()
        header.setResizeMode(0, qt.QHeaderView.Stretch)
        header.setVisible(True)
        self.loadFormLayout.addWidget(treeView)

        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        for i in range (3,numNodes):
            self.elements = slicer.mrmlScene.GetNthNodeByClass(i,"vtkMRMLModelNode" )
            print self.elements.GetName()

        # Add vertical spacer
        self.layout.addStretch(1)
        #------------------------ Compute Bounding Box ----------------------#
        buttonFrameBox = qt.QFrame(self.parent)
        buttonFrameBox.setLayout(qt.QHBoxLayout())
        self.loadFormLayout.addWidget(buttonFrameBox)

        self.computeBox = qt.QPushButton("Compute Bounding Box around all models")
        buttonFrameBox.layout().addWidget(self.computeBox)
        self.computeBox.connect('clicked()', self.onComputeBox)


        self.CollapsibleButton = ctk.ctkCollapsibleButton()
        self.CollapsibleButton.text = "Place Landmarks to define plane"
        self.layout.addWidget(self.CollapsibleButton)
        sampleFormLayout = qt.QFormLayout(self.CollapsibleButton)
        self.CollapsibleButton.checked = False

        # Collapsible button

        landmarkFrame = qt.QFrame()
        landmarkFrame.setLayout(qt.QHBoxLayout())
        landmarkLabel = qt.QLabel('Add Landmarks ')
        self.addLandMark = qt.QPushButton(qt.QIcon(":/Icons/MarkupsAddFiducial.png"), " ")
        self.addLandMark.setFixedSize(50,25)
        self.addLandMark.connect('clicked()', self.addLandMarkClicked)
        self.addLandMark.setEnabled(True)
        landmarkFrame.layout().addWidget(landmarkLabel)
        landmarkFrame.layout().addWidget(self.addLandMark)

        # MIDPOINT PART

        # labelLandmark = qt.QLabel('Choose 3 Landmarks to define the plane: ')
        #
        # label1 = qt.QLabel('Landmark 1: ')
        # self.Landmark1ComboBox = qt.QComboBox()
        # self.Landmark1ComboBox.addItem("List of fiducials")
        # landmark1Layout = qt.QHBoxLayout()
        # landmark1Layout.addWidget(label1)
        # landmark1Layout.addWidget(self.Landmark1ComboBox)
        #
        # label2 = qt.QLabel('Landmark 2: ')
        # self.Landmark2ComboBox = qt.QComboBox()
        # self.Landmark2ComboBox.addItem("List of fiducials")
        # landmark2Layout = qt.QHBoxLayout()
        # landmark2Layout.addWidget(label2)
        # landmark2Layout.addWidget(self.Landmark2ComboBox)

        labelLandmark = qt.QLabel('Choose 3 Landmarks to define the plane: ')

        label1 = qt.QLabel('Landmark 1: ')
        self.Landmark1ComboBox = qt.QComboBox()
        self.Landmark1ComboBox.addItem("List of fiducials")
        landmark1Layout = qt.QHBoxLayout()
        landmark1Layout.addWidget(label1)
        landmark1Layout.addWidget(self.Landmark1ComboBox)


        label2 = qt.QLabel('Landmark 2: ')
        self.Landmark2ComboBox = qt.QComboBox()
        self.Landmark2ComboBox.addItem("List of fiducials")
        landmark2Layout = qt.QHBoxLayout()
        landmark2Layout.addWidget(label2)
        landmark2Layout.addWidget(self.Landmark2ComboBox)

        label3 = qt.QLabel('Landmark 3: ')
        self.Landmark3ComboBox = qt.QComboBox()
        self.Landmark3ComboBox.addItem("List of fiducials")
        landmark3Layout = qt.QHBoxLayout()
        landmark3Layout.addWidget(label3)
        landmark3Layout.addWidget(self.Landmark3ComboBox)

        self.placePlaneButton = qt.QPushButton("Define and Place Planes")
        self.placePlaneButton.connect('clicked()', self.onValueChanged)


        nodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLMarkupsFiducialNode')

        if nodes.GetNumberOfItems() == 0:
            # first fiducial list
            displayNode1 = slicer.vtkMRMLMarkupsDisplayNode()
            slicer.mrmlScene.AddNode(displayNode1)

            fidNode1 = slicer.vtkMRMLMarkupsFiducialNode()
            fidNode1.SetName("P-1")
            slicer.mrmlScene.AddNode(fidNode1)
            fidNode1.AddObserver(vtk.vtkCommand.ModifiedEvent, self.OnFiducialModified)
                

        self.slider = ctk.ctkSliderWidget()
        self.slider.singleStep = 0.1
        self.slider.minimum = 0.1
        self.slider.maximum = 100
        self.slider.value = 1.0
        self.slider.toolTip = "Set the size of your plane."

        self.slideOpacity = ctk.ctkSliderWidget()
        self.slideOpacity.singleStep = 0.1
        self.slideOpacity.minimum = 0.1
        self.slideOpacity.maximum = 1
        self.slideOpacity.value = 1.0
        self.slider.toolTip = "Set the opacity of your plane."

        sampleFormLayout.addRow(landmarkFrame)
        sampleFormLayout.addRow(labelLandmark)
        sampleFormLayout.addRow(landmark1Layout)
        sampleFormLayout.addRow(landmark2Layout)
        sampleFormLayout.addRow(landmark3Layout)
        sampleFormLayout.addRow(self.placePlaneButton)
        sampleFormLayout.addRow("Size of your plane", self.slider)
        sampleFormLayout.addRow("Opacity of your plane", self.slideOpacity)


        self.CollapsibleButtonPlane = ctk.ctkCollapsibleButton()
        self.CollapsibleButtonPlane.text = "Choose planes"
        self.layout.addWidget(self.CollapsibleButtonPlane)
        sampleFormLayoutPlane = qt.QFormLayout(self.CollapsibleButtonPlane)


        self.planeComboBox1 = qt.QComboBox()
        self.planeComboBox1.addItem("red")
        self.planeComboBox1.addItem("yellow")
        self.planeComboBox1.addItem("green")
        self.planeComboBox1.addItem("Landmarks")
        sampleFormLayoutPlane.addRow("Select plane 1: ", self.planeComboBox1)


        self.planeComboBox2 = qt.QComboBox()
        self.planeComboBox2.addItem("red")
        self.planeComboBox2.addItem("yellow")
        self.planeComboBox2.addItem("green")
        self.planeComboBox2.addItem("Landmarks")
        sampleFormLayoutPlane.addRow("Select plane 2: ", self.planeComboBox2)


        self.CollapsibleButton2 = ctk.ctkCollapsibleButton()
        self.CollapsibleButton2.text = "Results"
        self.layout.addWidget(self.CollapsibleButton2)
        sampleFormLayout2 = qt.QFormLayout(self.CollapsibleButton2)

        self.results = qt.QPushButton("Results")
        self.results.connect('clicked()', self.angleValue)
        sampleFormLayout2.addWidget(self.results)

        label_RL = qt.QLabel("R-L View")
        self.getAngle_RL = qt.QLabel("0")

        label_SI = qt.QLabel("S-I View")
        self.getAngle_SI = qt.QLabel("0")

        label_AP = qt.QLabel("A-P View")
        self.getAngle_AP = qt.QLabel("0")


        self.getAngle_RL_comp = qt.QLabel("0")
        self.getAngle_SI_comp = qt.QLabel("0")
        self.getAngle_AP_comp = qt.QLabel("0")


        tableResult = qt.QTableWidget(3, 3)
        tableResult.setColumnCount(3)
        tableResult.setHorizontalHeaderLabels([' View ', 'Angle', 'Complementary angle'])
        tableResult.setColumnWidth(0, 80)
        tableResult.setColumnWidth(1, 80)
        tableResult.setColumnWidth(2, 180)

        tableResult.setRowCount(1)
        tableResult.setCellWidget(0, 0, label_RL)
        tableResult.setCellWidget(0, 1, self.getAngle_RL)
        tableResult.setCellWidget(0, 2, self.getAngle_RL_comp)

        tableResult.setRowCount(2)
        tableResult.setCellWidget(1, 0, label_SI)
        tableResult.setCellWidget(1, 1, self.getAngle_SI)
        tableResult.setCellWidget(1, 2, self.getAngle_SI_comp)

        tableResult.setRowCount(3)
        tableResult.setCellWidget(2, 0, label_AP)
        tableResult.setCellWidget(2, 1, self.getAngle_AP)
        tableResult.setCellWidget(2, 2, self.getAngle_AP_comp)


        # Add vertical spacer
        self.layout.addStretch(1)

        sampleFormLayout2.addWidget(tableResult)

        self.CollapsibleButton3 = ctk.ctkCollapsibleButton()
        self.CollapsibleButton3.text = "Save"
        self.layout.addWidget(self.CollapsibleButton3)
        sampleFormLayout3 = qt.QFormLayout(self.CollapsibleButton3)
        self.CollapsibleButton3.checked = False

        buttonFrame = qt.QFrame(self.parent)
        buttonFrame.setLayout(qt.QVBoxLayout())
        sampleFormLayout3.addWidget(buttonFrame)

        #-------------------------------- PLANES --------------------------------#
        save_plane = qt.QLabel("Save the planes you create as a txt file.")
        buttonFrame.layout().addWidget(save_plane)
        save = qt.QPushButton("Save plane")
        buttonFrame.layout().addWidget(save)

        # load_plane = qt.QLabel("Load the file with the plane you saved.")
        # buttonFrame.layout().addWidget(load_plane)
        read = qt.QPushButton("Load plane")
        buttonFrame.layout().addWidget(read)

        #-------------------------------- CONNECTIONS --------------------------------#
        self.planeComboBox1.connect('currentIndexChanged(QString)', self.valueComboBox)
        self.planeComboBox2.connect('currentIndexChanged(QString)', self.valueComboBox)


        self.slider.connect('valueChanged(double)', self.onValueChanged)
        self.slideOpacity.connect('valueChanged(double)', self.onValueChanged)

        save.connect('clicked(bool)', self.logic.savePlane)
        read.connect('clicked(bool)', self.logic.readPlane)
                                                                                                                
        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)
    
    def OnFiducialModified(self, obj, event):
        
        print "evt"
        self.Landmark1ComboBox.addItem(self.i+1)
        self.Landmark2ComboBox.addItem(self.i+1)
        self.Landmark3ComboBox.addItem(self.i+1)
        self.i = self.i+1
    
    def onComputeBox(self):
        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        for i in range (3,numNodes):
            self.elements = slicer.mrmlScene.GetNthNodeByClass(i,"vtkMRMLModelNode" )
        #--------------------------- Box around the model --------------------------#
        node = slicer.util.getNode(self.elements.GetName())
        polydata = node.GetPolyData()
        bound = polydata.GetBounds()
        print "bound", bound
        
        dimX = bound[1]-bound[0]
        dimY = bound[3]-bound[2]
        dimZ = bound[5]-bound[4]
        
        print "dimension X :", dimX
        print "dimension Y :", dimY
        print "dimension Z :", dimZ
        
        dimX = dimX + 10
        dimY = dimY + 20
        dimZ = dimZ + 20
        
        center = polydata.GetCenter()
        print "Center polydata :", center
        
        # Creation of an Image
        self.image = sitk.Image(int(dimX), int(dimY), int(dimZ), sitk.sitkInt16)
        
        dir = (-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0)
        self.image.SetDirection(dir)
        
        spacing = (1,1,1)
        self.image.SetSpacing(spacing)
        
        tab = [-center[0]+dimX/2,-center[1]+dimY/2,center[2]-dimZ/2]
        print tab
        self.image.SetOrigin(tab)
        
        
        writer = sitk.ImageFileWriter()
        tempPath = slicer.app.temporaryPath
        filename = "Box.nrrd"
        filenameFull=os.path.join(tempPath,filename)
        print filenameFull
        writer.SetFileName(str(filenameFull))
        writer.Execute(self.image)
        
        
        slicer.util.loadVolume(filenameFull)
        
        #------------------------ Slice Intersection Visibility ----------------------#
        numDisplayNode = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelDisplayNode")
        for i in range (3,numDisplayNode):
            self.slice = slicer.mrmlScene.GetNthNodeByClass(i,"vtkMRMLModelDisplayNode" )
            self.slice.SetSliceIntersectionVisibility(1)
    
    def addLandMarkClicked(self):
        print "Add landmarks"
        # # Place landmarks in the 3D scene
        landmarks = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        landmarks.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
        
        interactionLandmarks = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        interactionLandmarks.SetCurrentInteractionMode(1)
        self.Landmark1ComboBox.addItem(self.i+1)
        self.Landmark2ComboBox.addItem(self.i+1)
        self.Landmark3ComboBox.addItem(self.i+1)
        self.i = self.i+1
    
    def midPoint(self):
        print "Calculate midpoint "
    
    def placePlaneClicked(self):
        self.logic.planeLandmarks(self.Landmark1ComboBox.currentText, self.Landmark2ComboBox.currentText, self.Landmark3ComboBox.currentText, self.slider.value, self.slideOpacity.value)
    
    def onCloseScene(self, obj, event):
        self.logic.renderer.RemoveActor(self.logic.actor)
        print "Scene Close"
        globals()[self.moduleName] = slicer.util.reloadScriptedModule(self.moduleName)

    def onValueChanged(self):
        self.logic.initialize()
        if self.logic.renderer:
            self.logic.renderer.RemoveActor(self.logic.actor)
        self.placePlaneClicked()
    
    def angleValue(self):
        self.valueComboBox()
        
        self.getAngle_RL.setText(self.logic.angle_degre_RL)
        self.getAngle_RL_comp.setText(self.logic.angle_degre_RL_comp)
        
        self.getAngle_SI.setText(self.logic.angle_degre_SI)
        self.getAngle_SI_comp.setText(self.logic.angle_degre_SI_comp)
        
        self.getAngle_AP.setText(self.logic.angle_degre_AP)
        self.getAngle_AP_comp.setText(self.logic.angle_degre_AP_comp)
    
    def valueComboBox(self):
        
        colorPlane1 = self.planeComboBox1.currentText
        colorPlane2 = self.planeComboBox2.currentText
        
        print colorPlane1
        print colorPlane2
        
        redslice = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        redslice.SetWidgetVisible(False)
        
        yellowslice = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
        yellowslice.SetWidgetVisible(False)
        
        greenslice = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
        greenslice.SetWidgetVisible(False)
        
        self.logic.defineAngle(colorPlane1,colorPlane2)
    
    def modify(self, obj, event):
        self.logic.defineAngle(self.planeComboBox1.currentText,self.planeComboBox2.currentText)


class AnglePlanesLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        self.ColorNodeCorrespondence = {'red': 'vtkMRMLSliceNodeRed',
            'yellow': 'vtkMRMLSliceNodeYellow',
            'green': 'vtkMRMLSliceNodeGreen'}


    def initialize(self):
        self.layoutManager=slicer.app.layoutManager()
        self.threeDWidget=self.layoutManager.threeDWidget(0)
        self.threeDView=self.threeDWidget.threeDView()
        self.renderWindow=self.threeDView.renderWindow()
        self.renderers=self.renderWindow.GetRenderers()
        self.renderer=self.renderers.GetFirstRenderer()
        self.actor = vtk.vtkActor()
    
    def getMatrix(self, slice):
        self.mat = slice.GetSliceToRAS()
        print self.mat
        #---------------------- RED SLICE -----------------------#
        # Matrix with the elements of SliceToRAS
        m = numpy.matrix([[self.mat.GetElement(0,0), self.mat.GetElement(0,1), self.mat.GetElement(0,2), self.mat.GetElement(0,3)],
                          [self.mat.GetElement(1,0), self.mat.GetElement(1,1), self.mat.GetElement(1,2), self.mat.GetElement(1,3)],
                          [self.mat.GetElement(2,0), self.mat.GetElement(2,1), self.mat.GetElement(2,2), self.mat.GetElement(2,3)],
                          [self.mat.GetElement(3,0), self.mat.GetElement(3,1), self.mat.GetElement(3,2), self.mat.GetElement(3,3)]])
        return m
    
    def defineNormal(self, matrix):
        
        # Normal vector to the Red slice:
        n_vector = numpy.matrix([[0],[0],[1],[1]])
        
        # point on the Red slice:
        A = numpy.matrix([[0], [0], [0], [1]])
        
        normalVector = matrix * n_vector
        print "n : \n", normalVector
        A = matrix * A
        
        
        normalVector1 = normalVector
        
        
        normalVector1[0] = normalVector[0] - A[0]
        normalVector1[1] = normalVector[1] - A[1]
        normalVector1[2] = normalVector[2] - A[2]
        print normalVector1
        
        return normalVector1
    
    def savePlane(self):
        sliceRed = slicer.util.getNode(self.ColorNodeCorrespondence['red'])
        self.m_Red = self.getMatrix(sliceRed)
        
        sliceYellow = slicer.util.getNode(self.ColorNodeCorrespondence['yellow'])
        self.m_Yellow = self.getMatrix(sliceYellow)
        
        sliceGreen = slicer.util.getNode(self.ColorNodeCorrespondence['green'])
        self.m_Green = self.getMatrix(sliceGreen)
        
        
        filename = qt.QFileDialog.getSaveFileName(parent=self, caption='Save file')
        fichier = open(filename, "w")
        fichier.write("SliceToRAS Red Slice: \n")
        fichier.write(str(self.m_Red) + '\n')
        fichier.write('\n')
        
        fichier.write("SliceToRAS Yellow Slice: \n")
        fichier.write(str(self.m_Yellow) + '\n')
        fichier.write('\n')
        
        fichier.write("SliceToRAS Green Slice: \n")
        fichier.write(str(self.m_Green) + '\n')
        fichier.write('\n')
        
        fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
        if fidNode:
            
            fichier.write("Fiducial: \n")
            listCoord = list()
            fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
            self.coord = numpy.zeros(3)
            fidNode.GetNthFiducialPosition(0, self.coord)
            listCoord.insert(0,self.coord)
            fichier.write(str(self.coord) + '\n')
            fichier.write('\n')
            
            listCoord = list()
            fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
            self.coord = numpy.zeros(3)
            fidNode.GetNthFiducialPosition(1, self.coord)
            listCoord.insert(0,self.coord)
            fichier.write(str(self.coord) + '\n')
            fichier.write('\n')
            
            listCoord = list()
            fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
            self.coord = numpy.zeros(3)
            fidNode.GetNthFiducialPosition(2, self.coord)
            listCoord.insert(0,self.coord)
            fichier.write(str(self.coord) + '\n')
            fichier.write('\n')
        
        fichier.close()
    
    def readPlane(self):
        filename = qt.QFileDialog.getOpenFileName(parent=self,caption='Open file')
        print 'filename:', filename
        fichier2 = open(filename, 'r')
        fichier2.readline()
        NodeRed = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        matRed = NodeRed.GetSliceToRAS()
        
        for i in range(0, 4):
            ligne = fichier2.readline()
            ligne = ligne.replace('[', '')
            ligne = ligne.replace('   ', ' ')
            ligne = ligne.replace(']', '')
            ligne = ligne.replace('\n', '')
            print ligne
            items = ligne.split()
            print items
            for j in range(0, 4):
                matRed.SetElement(i, j, float(items[j]))
        
        
        print matRed
        compare_red = 0
        for i in range(0,4):
            for j in range(0,4):
                if matRed.GetElement(i,j) == self.matRed_init[i,j]:
                    compare_red = compare_red + 1
        
        print compare_red
        
        if compare_red != 16:
            self.redslice = slicer.util.getNode('vtkMRMLSliceNodeRed')
            if self.red_plane_box.isChecked():
                self.red_plane_box.setChecked(False)
                self.redslice.SetWidgetVisible(False)
            self.red_plane_box.setChecked(True)
            self.redPlaneCheckBoxClicked()
        
        fichier2.readline()
        fichier2.readline()
        
        
        NodeGreen = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
        matGreen = NodeGreen.GetSliceToRAS()
        for i in range (0,4):
            ligne = fichier2.readline()
            ligne = ligne.replace('[', '')
            ligne = ligne.replace('   ', ' ')
            ligne = ligne.replace(']', '')
            ligne = ligne.replace('\n', '')
            print ligne
            items = ligne.split()
            print items
            for j in range(0, 4):
                matGreen.SetElement(i, j, float(items[j]))
        
        
        print matGreen
        
        
        compare_green = 0
        for i in range(0,4):
            for j in range(0,4):
                if matGreen.GetElement(i,j) == self.matGreen_init[i,j]:
                    compare_green = compare_green + 1
        
        print compare_green
        
        if compare_green != 16:
            self.greenslice = slicer.util.getNode('vtkMRMLSliceNodeGreen')
            if self.green_plane_box.isChecked():
                self.green_plane_box.setChecked(False)
                self.greenslice.SetWidgetVisible(False)
            
            self.green_plane_box.setChecked(True)
            self.greenPlaneCheckBoxClicked()
        
        
        fichier2.readline()
        fichier2.readline()
        
        displayNode = slicer.vtkMRMLMarkupsDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        fidNode = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(fidNode)
        fidNode.SetAndObserveDisplayNodeID(displayNode.GetID())
        
        ligne = fichier2.readline()
        ligne = ligne.replace('[', '')
        ligne = ligne.replace('   ', ' ')
        ligne = ligne.replace(']', '')
        ligne = ligne.replace('\n', '')
        print ligne
        items = ligne.split()
        print items
        
        r = float(items[0])
        a = float(items[1])
        s = float(items[2])
        fidNode.AddFiducial(r,a,s)
        
        fichier2.readline()
        
        displayNode = slicer.vtkMRMLMarkupsDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        fidNode = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(fidNode)
        fidNode.SetAndObserveDisplayNodeID(displayNode.GetID())
        
        ligne = fichier2.readline()
        ligne = ligne.replace('[', '')
        ligne = ligne.replace('   ', ' ')
        ligne = ligne.replace(']', '')
        ligne = ligne.replace('\n', '')
        print ligne
        items = ligne.split()
        print items
        
        r = float(items[0])
        a = float(items[1])
        s = float(items[2])
        fidNode.AddFiducial(r,a,s)
        
        fichier2.readline()
        
        displayNode = slicer.vtkMRMLMarkupsDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        fidNode = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(fidNode)
        fidNode.SetAndObserveDisplayNodeID(displayNode.GetID())
        
        ligne = fichier2.readline()
        ligne = ligne.replace('[', '')
        ligne = ligne.replace('   ', ' ')
        ligne = ligne.replace(']', '')
        ligne = ligne.replace('\n', '')
        print ligne
        items = ligne.split()
        print items
        
        r = float(items[0])
        a = float(items[1])
        s = float(items[2])
        fidNode.AddFiducial(r,a,s)
        
        fichier2.close()
    
    def getAngle(self, normalVect1, normalVect2):
        
        norm1 = sqrt(normalVect1[0]*normalVect1[0]+normalVect1[1]*normalVect1[1]+normalVect1[2]*normalVect1[2])
        print "norme 1: \n", norm1
        norm2 =sqrt(normalVect2[0]*normalVect2[0]+normalVect2[1]*normalVect2[1]+normalVect2[2]*normalVect2[2])
        print "norme 2: \n", norm2
        
        
        scalar_product = (normalVect1[0]*normalVect2[0]+normalVect1[1]*normalVect2[1]+normalVect1[2]*normalVect2[2])
        print "scalar product : \n", scalar_product
        
        angle = acos(scalar_product/(norm1*norm2))
        print "radian angle : ", angle
        
        angle_degree = angle*180/pi
        print "Angle in degree", angle_degree
        
        
        norm1_RL = sqrt(normalVect1[1]*normalVect1[1]+normalVect1[2]*normalVect1[2])
        print "norme RL: \n", norm1_RL
        norm2_RL =sqrt(normalVect2[1]*normalVect2[1]+normalVect2[2]*normalVect2[2])
        print "norme RL: \n", norm2_RL
        
        if (norm1_RL ==0 or norm1_RL ==0):
            self.angle_degre_RL = 0
            self.angle_degre_RL_comp = 0
        else:
            scalar_product_RL = (normalVect1[1]*normalVect2[1]+normalVect1[2]*normalVect2[2])
            print "scalar product : \n", scalar_product_RL
            
            angleRL = acos(scalar_product_RL/(norm1_RL*norm2_RL))
            print "radian angle : ", angleRL
            
            self.angle_degre_RL = angleRL*180/pi
            self.angle_degre_RL = round(self.angle_degre_RL,2)
            print self.angle_degre_RL
            self.angle_degre_RL_comp = 180-self.angle_degre_RL
        
        
        norm1_SI = sqrt(normalVect1[0]*normalVect1[0]+normalVect1[1]*normalVect1[1])
        print "norme1_SI : \n", norm1_SI
        norm2_SI =sqrt(normalVect2[0]*normalVect2[0]+normalVect2[1]*normalVect2[1])
        print "norme2_SI : \n", norm2_SI
        
        if (norm1_SI ==0 or norm2_SI ==0):
            self.angle_degre_SI = 0
            self.angle_degre_SI_comp = 0
        else:
            scalar_product_SI = (normalVect1[0]*normalVect2[0]+normalVect1[1]*normalVect2[1])
            print "scalar product_SI : \n", scalar_product_SI
            
            angleSI = acos(scalar_product_SI/(norm1_SI*norm2_SI))
            print "radian angle : ", angleSI
            
            self.angle_degre_SI = angleSI*180/pi
            self.angle_degre_SI = round(self.angle_degre_SI,2)
            print self.angle_degre_SI
            self.angle_degre_SI_comp = 180-self.angle_degre_SI
            print self.angle_degre_SI_comp
        
        norm1_AP = sqrt(normalVect1[0]*normalVect1[0]+normalVect1[2]*normalVect1[2])
        print "norme1_SI : \n", norm1_AP
        norm2_AP =sqrt(normalVect2[0]*normalVect2[0]+normalVect2[2]*normalVect2[2])
        print "norme2_SI : \n", norm2_AP
        
        if (norm1_AP ==0 or norm2_AP ==0):
            self.angle_degre_AP = 0
            self.angle_degre_AP_comp = 0
        else:
            scalar_product_AP = (normalVect1[0]*normalVect2[0]+normalVect1[2]*normalVect2[2])
            print "scalar product_SI : \n", scalar_product_AP
            
            print "VALUE :", scalar_product_AP/(norm1_AP*norm2_AP)
            
            angleAP = acos(scalar_product_AP/(norm1_AP*norm2_AP))
            
            print "radian angle : ", angleAP
            
            self.angle_degre_AP = angleAP*180/pi
            self.angle_degre_AP = round(self.angle_degre_AP,2)
            print self.angle_degre_AP
            self.angle_degre_AP_comp = 180-self.angle_degre_AP
    
    def normalLandmarks(self, GA, GB):
        Vn = numpy.matrix([[0],[0],[0]])
        Vn[0] = GA[1]*GB[2] - GA[2]*GB[1]
        Vn[1] = GA[2]*GB[0] - GA[0]*GB[2]
        Vn[2] = GA[0]*GB[1] - GA[1]*GB[0]
        
        print "Vn = ",Vn
        
        norm_Vn = sqrt(Vn[0]*Vn[0]+Vn[1]*Vn[1]+Vn[2]*Vn[2])
        
        Normal = Vn/norm_Vn
        
        print "N = ",Normal
        
        return Normal
    
    def defineNormal(self, matrix):
        
        # Normal vector to the Red slice:
        n_vector = numpy.matrix([[0],[0],[1],[1]])
        
        # point on the Red slice:
        A = numpy.matrix([[0], [0], [0], [1]])
        
        normalVector = matrix * n_vector
        print "n : \n", normalVector
        A = matrix * A
        
        normalVector1 = normalVector
        
        normalVector1[0] = normalVector[0] - A[0]
        normalVector1[1] = normalVector[1] - A[1]
        normalVector1[2] = normalVector[2] - A[2]
        print normalVector1
        
        return normalVector1
    
    def defineAngle(self, colorPlane1, colorPlane2):
        print "DEFINE ANGLE"
        print colorPlane1
        if colorPlane1 != "Landmarks":
            self.slice1 = slicer.util.getNode(self.ColorNodeCorrespondence[colorPlane1])
            self.getMatrix(self.slice1)
            print "Slice test", self.slice1
            self.slice1.SetWidgetVisible(True)
            matrix1 = self.getMatrix(self.slice1)
            normal1 = self.defineNormal(matrix1)
        else:
            normal1 = self.N
        
        print colorPlane2
        if colorPlane2 != "Landmarks":
            self.slice2 = slicer.util.getNode(self.ColorNodeCorrespondence[colorPlane2])
            self.getMatrix(self.slice2)
            print "Slice test", self.slice2
            print "test"
            self.slice2.SetWidgetVisible(True)
            matrix2 = self.getMatrix(self.slice2)
            normal2 = self.defineNormal(matrix2)
        else:
            normal2 = self.N
        
        self.getAngle(normal1, normal2)
    
    def planeLandmarks(self, Landmark1Value, Landmark2Value, Landmark3Value, slider, sliderOpacity):
        self.initialize()
        # Limit the number of 3 landmarks to define a plane
        # Keep the coordinates of the landmarks
        listCoord = list()
        fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
        self.coord = numpy.zeros(3)
        if Landmark1Value != "List of fiducials":
            fidNode.GetNthFiducialPosition(int(Landmark1Value)-1, self.coord)
            listCoord.append(self.coord)
        
        print self.coord
        print listCoord
        
        r1 = self.coord[0]
        a1 = self.coord[1]
        s1 = self.coord[2]
        
        # Limit the number of 3 landmarks to define a plane
        # Keep the coordinates of the landmarks
        listCoord = list()
        fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
        self.coord = numpy.zeros(3)
        if Landmark2Value != "List of fiducials":
            fidNode.GetNthFiducialPosition(int(Landmark2Value)-1, self.coord)
            listCoord.append(self.coord)
        
        print self.coord
        print listCoord
        
        r2 = self.coord[0]
        a2 = self.coord[1]
        s2 = self.coord[2]
        
        # Limit the number of 3 landmarks to define a plane
        # Keep the coordinates of the landmarks
        listCoord = list()
        fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
        self.coord = numpy.zeros(3)
        if Landmark3Value != "List of fiducials":
            fidNode.GetNthFiducialPosition(int(Landmark3Value)-1, self.coord)
            listCoord.append(self.coord)
        
        print self.coord
        print listCoord
        
        r3 = self.coord[0]
        a3 = self.coord[1]
        s3 = self.coord[2]
        
        
        A = (r1,a1,s1)
        B = (r2,a2,s2)
        C = (r3,a3,s3)
        # Vn = Vectorial Product (AB, BC)
        # Normal N = Vn/norm(Vn)
        
        points = vtk.vtkPoints()
        points.InsertNextPoint(r1,a1,s1)
        points.InsertNextPoint(r2,a2,s2)
        points.InsertNextPoint(r3,a3,s3)
        
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        
        centerOfMass = vtk.vtkCenterOfMass()
        centerOfMass.SetInputData(polydata)
        centerOfMass.SetUseScalarsAsWeights(False)
        centerOfMass.Update()
        
        G = centerOfMass.GetCenter()
        
        print "Center of mass = ",G
        
        # Vector GA
        GA = numpy.matrix([[0],[0],[0]])
        GA[0] = A[0]-G[0]
        GA[1] = A[1]-G[1]
        GA[2] = A[2]-G[2]
        
        print "GA = ", GA
        
        # Vector BG
        GB = numpy.matrix([[0],[0],[0]])
        GB[0] = B[0]-G[0]
        GB[1] = B[1]-G[1]
        GB[2] = B[2]-G[2]
        
        print "GB = ", GB
        
        # Vector CG
        GC = numpy.matrix([[0],[0],[0]])
        GC[0] = C[0]-G[0]
        GC[1] = C[1]-G[1]
        GC[2] = C[2]-G[2]
        
        print "GC = ", GC
        
        self.N = self.normalLandmarks(GA,GB)
        
        D = numpy.matrix([[0],[0],[0]])
        E = numpy.matrix([[0],[0],[0]])
        F = numpy.matrix([[0],[0],[0]])
        
        
        D[0] = slider*GA[0] + G[0]
        D[1] = slider*GA[1] + G[1]
        D[2] = slider*GA[2] + G[2]
        
        print "Slider value : ", slider
        
        print "D = ",D
        
        E[0] = slider*GB[0] + G[0]
        E[1] = slider*GB[1] + G[1]
        E[2] = slider*GB[2] + G[2]
        
        print "E = ",E
        
        F[0] = slider*GC[0] + G[0]
        F[1] = slider*GC[1] + G[1]
        F[2] = slider*GC[2] + G[2]
        
        print "F = ",F
        
        self.renderWindow.AddRenderer(self.renderer)
        
        planeSource = vtk.vtkPlaneSource()
        planeSource.SetNormal(self.N[0],self.N[1],self.N[2])
        
        planeSource.SetOrigin(D[0],D[1],D[2])
        planeSource.SetPoint1(E[0],E[1],E[2])
        planeSource.SetPoint2(F[0],F[1],F[2])
        
        planeSource.Update()
        
        plane = planeSource.GetOutput()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(plane)
        
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetColor(0, 0.4, 0.8)
        self.actor.GetProperty().SetOpacity(sliderOpacity)
        
        self.renderer.AddActor(self.actor)
        
        self.renderWindow.Render()


class AnglePlanesTest(ScriptedLoadableModuleTest):
    def setUp(self):
        # reset the state - clear scene
        slicer.mrmlScene.Clear(0)
    
    def runTest(self):
        # run all tests needed
        self.setUp()
        self.test_AnglePlanes()
    
    def test_AnglePlanes(self):
        
        self.delayDisplay('Starting the test')
        logic = AnglePlanesLogic()

        matrix = numpy.matrix([[0.572236,0.192876,0.797085,0],
                               [-0.819942,0.152968,0.551631,0],
                               [0.0155322,0.969226,-0.245681,0],
                               [0,0,0,1]])

        normalVector1 = logic.defineNormal(matrix)

        fidNode = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(fidNode)

        r1=32
        a1=10
        s1=4

        r2=-9
        a2=7
        s2=19

        r3=9
        a3=-4
        s3=46

        fidNode.AddFiducial(r1,a1,s1)
        fidNode.AddFiducial(r2,a2,s2)
        fidNode.AddFiducial(r3,a3,s3)

        logic.planeLandmarks(1,2,3,1,1)

        GA = numpy.matrix([[5],[-2],[3]])
        GB = numpy.matrix([[6],[1],[9]])

        Normal = logic.normalLandmarks(GA, GB)

        logic.getAngle(normalVector1, Normal)

        self.delayDisplay('Test passed!')


