# Bob build tool
# Copyright (C) 2019  Jan Klötzke
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .common import CommonIDEGenerator
# from ..utils import quoteCmdExe
from pathlib import Path, PureWindowsPath
from shlex import quote as quoteBash
import os
import sys
import json

class VsCodeWorkspace:
    def __init__(self):
        self.bobCmd = "bob"
        self.recipesDir = None
        self.folders = []
        self.packages = []
        self.buildTargets = []
        self.preIncludePaths = []
        self.postIncludePaths = []

    def setBobCmd(self, bobCmd):
        self.bobCmd = bobCmd

    def setRecipesDir(self, recipesDir):
        self.recipesDir = recipesDir

    def addFolder(self, name, path):
        self.folders.append((name, path))

    def addPackage(self, name, path):
        self.packages.append((name, path))

    def addBuildTarget(self, target):
        self.buildTargets.append(target)

    def addPreIncludePaths(self, paths):
        self.preIncludePaths.extend(paths)

    def addPostIncludePaths(self, paths):
        self.postIncludePaths.extend(paths)

    def makeWorkspaceConfig(self):
        workspaceConfig = {}

        workspaceConfig["folders"] = []
        for (name, path) in self.folders + self.packages:
            workspaceConfig["folders"].append({"name": name, "path": path})

        workspaceConfig["settings"] = {}
        includePaths = []
        for p in self.preIncludePaths:
            includePaths.append(p)
        for (name, path) in self.packages:
            includePaths.append("${{workspaceFolder:{0}}}/**".format(name))
        for p in self.postIncludePaths:
            includePaths.append(p)
        workspaceConfig["settings"]["C_Cpp.default.includePath"] = includePaths

        return workspaceConfig

    def makeTask(self, name, recipe, params):
        task = {
            "label": name,
            "type": "process",
            "command": "sh",
            "args": [
                "-c",
                "{0} dev {1}{2}".format(self.bobCmd, recipe, (" " if len(params) > 0 else "") + params)
            ],
            "options": {
                "cwd": self.recipesDir.as_posix()
            },
            "group": {
                "kind": "build"
            }
        }
        return task
        

    def makeTasksConfig(self):
        tasksConfig = {}
        tasksConfig["version"] = "2.0.0"
        tasksConfig["tasks"] = []

        # Debug task
        # tasksConfig["tasks"].append(
        # {
        #     "label": "echo",
        #     "type": "shell",
        #     "command": "echo ${input:recipeName}"
        # })

        target = self.buildTargets[0]

        buildConfigs = [
            ("", ["-v"]),
            (" (build only)", ["-v", "-b"]),
            (" (checkout only)", ["-v", "-B"]),
            (" (force, clean build)", ["-v", "-f", "--clean"])
        ]

        for c in buildConfigs:
            task = self.makeTask("Bob dev {0}{1}".format(target, c[0]), target, " ".join(c[1]))
            tasksConfig["tasks"].append(task)

        tasksConfig["tasks"][0]["group"]["isDefault"] = True

        if len(self.buildTargets) > 1:
            for c in buildConfigs:
                task = self.makeTask("Bob dev {0}".format(c[0]), "${input:recipeName}", " ".join(c[1]))
                tasksConfig["tasks"].append(task)

            tasksConfig["inputs"] = [{
                "type": "pickString",
                "id": "recipeName",
                "description": "What recipe do you want to build?",
                "options": self.buildTargets,
                "default": self.buildTargets[0]
            }]

        return tasksConfig
    
    def writeWorkspace(self, destinationDir):
        workspace = {}
        workspaceFile = destinationDir.joinpath("project.code-workspace")

        # read existing workspace
        try:
            with open(workspaceFile.as_poisx(), "r") as file:
                workspace = json.load(file)
        except:
            pass

        # make new workspace
        newWorkspace = self.makeWorkspaceConfig()
        newTasks = self.makeTasksConfig()
        # newWorkspace["folders"].insert(0, {"name": "workspace", "path": destinationDir.as_posix()})
        workspace.update(newWorkspace)
        if "tasks" in workspace:
            workspace["tasks"].update(newTasks)
        else:
            workspace["tasks"] = newTasks
        # print("workspace: {0}".format(json.dumps(workspace, indent = 4)))

        # write new workspace
        with open(workspaceFile.as_posix(), "w") as file:
            json.dump(workspace, file, indent = 4)

        return True

    def writeTasks(self, destinationDir):
    
        tasksDir = destinationDir.joinpath(".vscode")
        if not os.path.exists(tasksDir.as_posix()):
            os.mkdir(tasksDir.as_posix())
        tasksFile = tasksDir.joinpath("tasks.json")
    
        # make new tasks
        newTasks = self.makeTasks()
        # print("newTasks: {0}".format(json.dumps(newTasks, indent = 4)))
    
        # write new tasks
        with open(tasksFile.as_posix(), "w") as file:
            json.dump(newTasks, file, indent = 4)
    
        return True

    def generate(self, destinationDir):
        self.writeWorkspace(destinationDir)
        # self.writeTasks(destinationDir)

class VsCodeGenerator(CommonIDEGenerator):
    def __init__(self):
        super().__init__("vscode", "Generate VS Code Workspace")
        self.parser.add_argument("--recipes", default = False, action = "store_true",
                        help = "Add recipes directory as workspace folder.")

    def configure(self, package, argv):
        super().configure(package, argv)

    def generate(self, extra, bobRoot):
        super().generate()

        # print("extra: {0}".format(extra))
        # print("bobRoot: {0}".format(bobRoot))

        # gather root paths
        bobPwd = Path(os.getcwd())
        if sys.platform == 'msys':
            winPwd = PureWindowsPath(os.popen('pwd -W').read().strip())
            winDestination = PureWindowsPath(os.popen('cygpath -w {}'.format(quoteBash(self.destination))).read().strip())
        else:
            winPwd = bobPwd
            winDestination = Path(self.destination).resolve()
        # print("winPwd: {0}".format(winPwd))
        # print("winDestination: {0}".format(winDestination))

        bobCmd = bobRoot

        # create workspace
        ws = VsCodeWorkspace()

        ws.setBobCmd(bobCmd)

        ws.setRecipesDir(winPwd)
        if self.args.recipes:
            ws.addFolder("recipes", winPwd.as_posix())

        # print(self.prependIncludeDirectories)
        ws.addPreIncludePaths(self.prependIncludeDirectories)
        # print(self.appendIncludeDirectories)
        ws.addPostIncludePaths(self.appendIncludeDirectories)

        firstPackage = True
        for package, scan in self.packages.items():
            # print("package: {0}".format(package))
            # print("  isRoot: {0}".format(scan.isRoot))
            # print("  packagePath: {0}".format(scan.stack))
            workspacePath = winPwd.joinpath(PureWindowsPath(scan.workspacePath)).as_posix()
            # print("  workspacePath: {0}".format(workspacePath))
            ws.addPackage(package, workspacePath)
            if firstPackage:
                firstPackage = False
                ws.addBuildTarget(package)

        ws.generate(winDestination)

def vsCodeProjectGenerator(package, argv, extra, bobRoot):
    generator = VsCodeGenerator()
    generator.configure(package, argv)
    generator.generate(extra, bobRoot)
