# coding=utf-8

import maya.cmds as cmds
import os
import params
from mayaExporterReady import storage
import utility


def getRebuildOption():
    return cmds.radioButtonGrp("rebuildNormalOption", q=True, select=True) == 3 and cmds.checkBox("rebuildNormals",
                                                                                                  q=True, v=True)


def enableCustomAngle(value):
    if value:
        cmds.intField("customNormalAngle", e=True, enable=getRebuildOption())
    else:
        cmds.intField("customNormalAngle", e=True, enable=False)


def enableRebuildOption(value):
    cmds.radioButtonGrp("rebuildNormalOption", e=True, enable=value)
    enableCustomAngle(value)


def onEnableExport(value):
    cmds.checkBox("exportAsOneObject", e=True, enable=value)
    cmds.button("exportFolderBrowserButton", e=True, enable=value)
    cmds.textField("exportFolderInput", e=True, enable=value)
    cmds.textField("exportNameInput", e=True, enable=value)
    cmds.text("radioColExtentionLabel", e=True, enable=value)
    cmds.text("exportNameLabel", e=True, enable=value)
    cmds.text("exportFolderInput", e=True, enable=value)
    cmds.radioButton("exportFbx", e=True, enable=value)
    cmds.radioButton("exportObj", e=True, enable=value)


# Open file dialog to choose the reference directory
def searchRefs(*args):
    directory = cmds.fileDialog2(ds=2, fm=3, dir=storage.values.unityRefDir)
    if directory is not None:
        directory = directory[0]
        storage.values.unityRefDir = directory
        displayRefs(directory)
        utility.setUnityRefDir()
        return

    info("Search reference", "No folder selected")


# Open file dialog to choose the export folder
def searchExportFolder(*args):
    directory = cmds.fileDialog2(ds=2, fm=2, dir=storage.values.exportFolder)
    if directory is not None:
        directory = directory[0]
        storage.values.exportFolder = directory
        utility.setExportFolder()
        cmds.textField("exportFolderInput", e=True, text=directory)
        return

    info("Search export folder", "No folder selected")


# Store references into the storage with formated names
# and create the apropriate layout
def refStorage(refs):
    if len(refs) > 0:
        cmds.text(l="")
        cmds.text(l="FBX:")
        if len(refs) > 7:
            cmds.scrollLayout(
                horizontalScrollBarThickness=16, borderVisible=True,
                verticalScrollBarThickness=16, height=150, width=storage.scrollRefWidth)

        for ref in refs:
            refName, refExt = os.path.splitext(ref)
            refExt = refExt.replace(".", "")
            cmds.radioButton(refName + "_" + refExt, l=refName)
            # format reference name to make easier imports
            modifiedRefName = refName.replace(" ", "_")
            modifiedRefName = modifiedRefName.replace("-", "_")
            storage.unityRefs[modifiedRefName + "_" + refExt] = [refName, refExt]

        if len(refs) > 7:
            cmds.setParent("..")


# Searches 'obj' or 'fbx' references into the specified folder and displays it into the 'mayaExporterReady' window
def displayRefs(refDir):
    if cmds.columnLayout("refContainer", q=True, exists=True):
        cmds.deleteUI("refContainer", layout=True)

    storage.unityRefs.clear()
    cmds.columnLayout("refContainer", p="refWraper")
    cmds.radioCollection("unityRefs")
    refFbx = cmds.getFileList(folder=refDir, filespec="*.fbx") or []
    refObj = cmds.getFileList(folder=refDir, filespec="*.obj") or []
    cmds.button('unityImportRef', e=True, enable=len(refFbx) > 0 or len(refObj))

    refStorage(refFbx)
    refStorage(refObj)

    cmds.text(l="")
    cmds.setParent('..')
    cmds.setParent('..')


# Import in open scene the selected reference
def importRef(*args):
    refController = cmds.radioCollection("unityRefs", q=True, select=True)
    if refController != "NONE":
        path = os.path.join(storage.values.unityRefDir,
                            storage.unityRefs[refController][0] + "." + storage.unityRefs[refController][1])
        importedNodes = cmds.file(path, i=True, mergeNamespacesOnClash=True, returnNewNodes=True)
        cmds.select(clear=True)
        for node in importedNodes:
            cmds.select(node, add=True)

    else:
        info("Import error", "You have to select an element to import")


# Check if the folder specified to the export folder, exists
def checkExportFolder(path):
    # Register the new export folder
    if cmds.file(path, q=True, exists=True):
        # print("in check export folder", path)
        storage.values.exportFolder = path
        utility.setExportFolder()
        cmds.textField("exportFolderInput", e=True, text=path)

    # Reset the export folder by the saved one
    else:
        cmds.textField("exportFolderInput", e=True, text=storage.values.exportFolder)


def onFbxExtension(value):
    storage.values.exportExtension = "exportFbx"
    utility.setExportExtension()


def onObjExtension(value):
    storage.values.exportExtension = "exportObj"
    utility.setExportExtension()


def updateExportName(name):
    storage.values.exportName = name
    utility.setExportName()


def updateExportNameLabel(value):
    label = ""
    if value:
        label = "Object name:"
        cmds.text("exportNameLabel", e=True, l=label)

    else:
        label = "Destination folder name:"
        cmds.text("exportNameLabel", e=True, l=label)

    return label


def savePreferences(*args):
    params.getParams()
    settings = utility.JsonUtility.createJsonData()
    utility.JsonUtility.write(storage.prefsFile, settings)
    utility.setAllMetadata()


def resetToPrefs(*args):
    streamsName = storage.streams.keys()
    prefs = utility.JsonUtility.read(storage.prefsFile)
    for stream in streamsName:
        setattr(storage.values, stream, prefs[stream])

    cmds.deleteUI(storage.values.win)
    storage.values.win = createWindow("MayaExporterReady", lambda command: params.launchScript())


# Create the UI for the mayaExporterReady
def createWindow(name, callback):
    # check if the window exists already
    if cmds.window("mayaExporterReady", exists=True):
        cmds.deleteUI("mayaExporterReady")
    _win = cmds.window("mayaExporterReady", title=name)

    cmds.rowColumnLayout("global", adjustableColumn=True, columnOffset=[1, "both", storage.globalColumnOffset])
    cmds.shelfTabLayout('mainShelfTab', w=storage.shelfWidth)

    # GENERAL PANEL
    cmds.columnLayout("General", adj=False, columnOffset=["both", storage.inShelfOffset])
    cmds.text(l='<span style="font-size:18px">General options</span>', font="boldLabelFont")
    cmds.text(l="")
    cmds.checkBox("freezeTransform", l="Freeze transformations",
                  ann="Allow the script to freeze the transformation of your selection",
                  v=storage.values.freezeTransform)
    cmds.checkBox("deleteHistory", l="Delete history",
                  ann="Allow the script to delete the construction history of your selection",
                  v=storage.values.deleteHistory)
    cmds.checkBox("selectionOnly", l="Selection only",
                  ann="Restrict the script to process only your selection\nIf false, the all scene will be processed",
                  v=storage.values.selectionOnly)
    cmds.checkBox("cleanUpMesh", l="Clean up meshes", ann="Allow the script to go through a clean up your meshes",
                  v=storage.values.cleanUpMesh)
    cmds.checkBox("checkNonManyfold", l="Check for non-manyfold meshes",
                  ann="Allow the script to check non-manifold meshes and giving feedback if found",
                  v=storage.values.checkNonManyfold)
    cmds.text(l="")
    cmds.setParent('..')

    # NORMAL PANEL
    cmds.columnLayout("Normal", adj=False, columnOffset=["both", storage.inShelfOffset])
    cmds.text(l='<span style="font-size:18px">Normals options</span>', font="boldLabelFont")
    cmds.text(l="")
    cmds.checkBox("conformNormals", l="Conform normals",
                  ann="Conform the normals of your meshes.\nSet the normal to the average normal direction",
                  v=storage.values.conformNormals)
    cmds.checkBox("rebuildNormals", l="Rebuild normals",
                  ann="Rebuilds all normals of the mesh with custom angles\nSoft: angle = 30\nHard: angle = 0",
                  v=storage.values.rebuildNormals, cc=enableRebuildOption)
    cmds.text(label="")
    cmds.text(label="Rebuild options:", align="left")
    cmds.radioButtonGrp("rebuildNormalOption", labelArray3=['Soft', 'Hard', 'Custom'],
                        numberOfRadioButtons=3,
                        select=storage.values.rebuildNormalOption,
                        vertical=True,
                        enable=storage.values.rebuildNormals,
                        cc=enableCustomAngle)
    cmds.intField("customNormalAngle", min=0, max=180, v=storage.values.customNormalAngle, enable=getRebuildOption())
    cmds.text(l="")
    cmds.setParent('..')

    # PIVOT PANEL
    cmds.columnLayout("Pivot", adj=False, columnOffset=["both", storage.inShelfOffset])
    cmds.text(l='<span style="font-size:18px">Pivot options</span>', font="boldLabelFont")
    cmds.text(l="")
    cmds.radioButtonGrp("pivotOption",
                        labelArray4=['Untouched', 'Mesh center', 'Scene center', 'Base center'],
                        numberOfRadioButtons=4,
                        an1="Don't modify the pivot parameters",
                        an2="Set the pivot position at the center of every meshes",
                        an3="Set the pivot of every meshes at the center of the scene",
                        an4="Set the pivot of every meshes at the center of the mesh for XZ coordinates\nand at the lowest vertex position for the Y coordinate",
                        select=storage.values.pivotOption,
                        vertical=True)
    cmds.text(l="")
    cmds.setParent('..')

    # EXPORT PANEL
    cmds.columnLayout("Export", adj=False, columnOffset=["both", storage.inShelfOffset])
    cmds.text(l='<span style="font-size:18px">Export settings</span>', font="boldLabelFont")
    cmds.text(l="")
    cmds.checkBox("exportResult", l="Export result", ann="Allow the script to export the result of the process",
                  v=storage.values.exportResult, cc=onEnableExport)
    cmds.checkBox("exportAsOneObject", l="Export as one object",
                  ann="The script will export the selection as one only object", v=storage.values.exportAsOneObject,
                  cc=updateExportNameLabel)
    cmds.text(l="")
    cmds.text("exportFolderInput", l="Export path:")
    cmds.rowLayout(adjustableColumn=2, numberOfColumns=2)
    cmds.textField("exportFolderInput", ann="Path of the folder where the exported files will drop",
                   fi=storage.values.exportFolder, w=300, h=26, cc=checkExportFolder)
    cmds.button("exportFolderBrowserButton", ann="Open dialog to search an export folder", l="Browse",
                c=searchExportFolder)
    cmds.setParent('..')
    cmds.text(l="")
    cmds.text("exportNameLabel", l="")
    cmds.text("exportNameLabel", e=True, l=updateExportNameLabel(storage.values.exportAsOneObject))
    storage.scene = cmds.file(q=True, sn=True)
    storage.sceneName, storage.sceneExt = os.path.splitext(os.path.basename(storage.scene))
    # print("sceneName", storage.sceneName)
    cmds.textField("exportNameInput", text=storage.values.exportName,
                   ann="Name that will have the folder or the file that will be exported", w=351, h=26,
                   cc=updateExportName,
                   pht=storage.sceneName if storage.sceneName != "" else "untitled")
    cmds.text(l="")
    cmds.radioCollection("exportExtension")
    cmds.text("radioColExtentionLabel", l="Export as")
    cmds.radioButton("exportFbx", ann="The script will export the meshes as FBX", l="FBX", onCommand=onFbxExtension)
    cmds.radioButton("exportObj", ann="The script will export the meshes as OBJ", l="OBJ", onCommand=onObjExtension)
    cmds.radioCollection("exportExtension", e=True, select=storage.values.exportExtension)

    onEnableExport(cmds.checkBox("exportResult", q=True, v=True))
    cmds.text(l="")
    cmds.setParent('..')

    # REFERENCE PANEL
    cmds.columnLayout("References", adj=False, columnOffset=["both", storage.inShelfOffset])
    cmds.text(l='<span style="font-size:18px">Search and import references</span>', font="boldLabelFont")
    cmds.columnLayout("refWraper")
    cmds.setParent('..')
    cmds.rowLayout(adjustableColumn=2, numberOfColumns=2)
    cmds.button(label="Search", ann="Open dialog to search a folder with\nFBX or OBJ files in it", c=searchRefs, w=150)
    cmds.button('unityImportRef', l='Import reference', ann="Import the selected reference into the active scene",
                c=importRef, w=150)
    cmds.setParent('..')
    cmds.text(l="")
    displayRefs(storage.values.unityRefDir)
    cmds.setParent('..')

    # SETTINGS PANEL
    cmds.columnLayout("Settings", adj=False, columnOffset=["both", storage.inShelfOffset])
    cmds.text(l='<span style="font-size:18px">Settings options</span>', font="boldLabelFont")
    cmds.text(l="")
    cmds.checkBox("alwaysOverrideExport", l="Override existing export file",
                  ann="The script will override, by default, the corresponding export file if it exists",
                  v=storage.values.alwaysOverrideExport)
    cmds.checkBox("stayInScene", l="Stay in active scene",
                  ann="True: the script will end on the active scene\nFalse:the script will end on the export file of the active scene",
                  v=storage.values.stayInScene)
    cmds.checkBox("displayInfo", l="Display informations",
                  ann="Allow the script to gives you mass informations on what is happening during the process",
                  v=storage.values.displayInfo)
    cmds.text(l="")
    cmds.text(l="Preferences:")
    cmds.button("saveAsPrefs", l="Save settings", c=savePreferences, w=125)
    cmds.text(l="")
    cmds.button("resetToPrefs", l="Reset to preferences", c=resetToPrefs, w=125)
    cmds.text(l="")

    cmds.setParent('|')
    cmds.text(l="")
    cmds.button(l="Go", c=callback)
    cmds.rowColumnLayout("global", e=True, rowOffset=[(1, "top", storage.globalRowOffset), (
        len(cmds.rowColumnLayout("global", q=True, childArray=True)), "bottom", storage.globalRowOffset)])

    # Display the window
    cmds.showWindow(_win)

    return _win


"""
CREATE MODAL
"""


# Create confirm modal with 'Yes' / 'No' buttons
def confirm(title, message):
    # print("Display " + title + " confirm")
    res = cmds.confirmDialog(title=title,
                             message=message,
                             button=["Yes", "No"],
                             defaultButton='Yes',
                             cancelButton='No',
                             dismissString='No')

    if res == "Yes":
        # print("Answer => YES")
        return True

    else:
        # display results
        # print("Answer => NO")
        return False


# Create info modal with just an 'ok' button
def info(title, message):
    cmds.confirmDialog(title=title,
                       message=message,
                       button=["Ok"],
                       defaultButton='Ok',
                       dismissString='Ok')
