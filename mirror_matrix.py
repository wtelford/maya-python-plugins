"""mirrorMatrix node plugin for Maya"""
import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import math
import plugin

NODE_NAME = 'mirrorMatrix'
NODE_ID = OpenMaya.MTypeId(0x0012F1C0)

AUTHOR = 'Will Telford'
VERSION = '1.0'
API_VERSION = 'Any'


class node(OpenMayaMPx.MPxNode):
    """
    Defines the Maya dependency node.
    """

    def __init__(self):
        """Init function."""
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, plug, data):
        """Recompute the given output based on the nodes inputs."""
        space = OpenMaya.MSpace.kWorld
        matrix1Handle = data.inputValue(node.matrixIn)
        m1 = OpenMaya.MTransformationMatrix(matrix1Handle.asMatrix())

        matrix2Handle = data.inputValue(node.planeMatrix)
        m2 = OpenMaya.MTransformationMatrix(matrix2Handle.asMatrix())

        mode = data.inputValue(node.mode).asShort()
        flipAxis = data.inputValue(node.flipAxis).asShort()
        planeNormal = data.inputValue(node.planeNormal).asDouble3()
        planeNormal = OpenMaya.MVector(planeNormal[0], planeNormal[1],
                                       planeNormal[2])
        planeNormal.normalize()

        # establish mirror plane orientation
        xVec = OpenMaya.MVector.xAxis
        rot = xVec.rotateTo(planeNormal)
        m2.rotateBy(rot, OpenMaya.MSpace.kObject)

        # create -1 X scale matrix
        valueList = [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        mNegX = OpenMaya.MMatrix()
        OpenMaya.MScriptUtil.createMatrixFromList(valueList, mNegX)

        # calculate base reflection matrix
        reflectMatrix = m1.asMatrix() * m2.asMatrix().inverse(
        ) * mNegX * m2.asMatrix()

        # modify reflection matrix to repersent the correct mode
        mirrorMatrix = reflectMatrix
        if mode == 0:
            behaviorMatrix = mNegX * reflectMatrix
            mirrorMatrix = behaviorMatrix
        elif mode == 1:
            newTMat = m1
            tran = OpenMaya.MTransformationMatrix(
                reflectMatrix).getTranslation(space)
            newTMat.setTranslation(tran, space)
            orientationMatrix = newTMat.asMatrix()
            mirrorMatrix = orientationMatrix

        # apply 180 degree flip to chosen axis
        valueList = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        if flipAxis == 1:
            valueList = [1, 0, 0, 0, 0, -1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1]
        elif flipAxis == 2:
            valueList = [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1]
        elif flipAxis == 3:
            valueList = [-1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        flipMatrix = OpenMaya.MMatrix()
        OpenMaya.MScriptUtil.createMatrixFromList(valueList, flipMatrix)

        # set output matrix
        outputMatrix = flipMatrix * mirrorMatrix
        hOutput = data.outputValue(node.aOutput)
        hOutput.setMMatrix(outputMatrix)
        hOutput.setClean()

        data.setClean(plug)


# creates the object for maya/
def Creator():
    """Function that returns an instance of the class"""
    return OpenMayaMPx.asMPxPtr(node())


def initialize():
    """Will initialize all the attributes of the new node type"""
    nAttr = OpenMaya.MFnNumericAttribute()
    mAttr = OpenMaya.MFnMatrixAttribute()
    eAttr = OpenMaya.MFnEnumAttribute()

    # Create the output attribute for the node
    node.aOutput = mAttr.create('outputMatrix', 'outM')
    mAttr.setWritable(False)
    mAttr.setStorable(False)

    # Add output to the node
    node.addAttribute(node.aOutput)

    # Create input Attributes
    node.matrixIn = mAttr.create('matrixIn', 'matrixIn')
    node.planeMatrix = mAttr.create('planeMatrix', 'planeMatrix')

    node.flipAxis = eAttr.create('flipAxis', 'flipAxis')
    eAttr.setKeyable(True)
    eAttr.addField('None', 0)
    eAttr.addField('X Axis', 1)
    eAttr.addField('Y Axis', 2)
    eAttr.addField('Z Axis', 3)

    node.mode = eAttr.create('mode', 'mode')
    eAttr.setKeyable(True)
    eAttr.addField('Behavior', 0)
    eAttr.addField('Orientation', 1)
    eAttr.addField('Reflect', 2)

    node.planeNormalX = nAttr.create("planeNormalX", "planeNormalX",
                                     OpenMaya.MFnNumericData.kDouble, 1.0)
    node.planeNormalY = nAttr.create("planeNormalY", "planeNormalY",
                                     OpenMaya.MFnNumericData.kDouble, 0.0)
    node.planeNormalZ = nAttr.create("planeNormalZ", "planeNormalZ",
                                     OpenMaya.MFnNumericData.kDouble, 0.0)
    node.planeNormal = nAttr.create("planeNormal", "planeNormal",
                                    node.planeNormalX, node.planeNormalY,
                                    node.planeNormalZ)
    nAttr.setKeyable(True)

    inputAttrs = [
        node.mode, node.flipAxis, node.planeNormal, node.matrixIn,
        node.planeMatrix
    ]
    for inputAttr in inputAttrs:
        # Add input Attributes
        node.addAttribute(inputAttr)

        # Define what is input and what is output
        node.attributeAffects(inputAttr, node.aOutput)


def initializePlugin(obj):
    """Registers all of the services that this plugin provides with Maya.

    Arguments:
        obj {mobject} -- a handle to the plug-in object (use MFnPlugin to access it)
    """
    mplugin = OpenMayaMPx.MFnPlugin(obj, AUTHOR, VERSION, API_VERSION)
    mplugin.registerNode(NODE_NAME, NODE_ID, Creator, initialize)


def uninitializePlugin(obj):
    """Deregisters all of the services that this plugin provided from Maya.

    Arguments:
        obj {mobject} -- a handle to the plug-in object (use MFnPlugin to access it)
    """
    mplugin = OpenMayaMPx.MFnPlugin(obj)
    mplugin.deregisterNode(NODE_ID)
