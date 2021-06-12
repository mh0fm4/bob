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
        self.packages = []

    def addPackage(self, name, path):
        self.packages.append((name, path))

    def makeWorkspaceConfig(self):
        workspaceConfig = {}
        workspaceConfig["folders"] = []
        workspaceConfig["settings"] = {}
        workspaceConfig["settings"]["C_Cpp.default.includePath"] = []

        for (name, path) in self.packages:
            workspaceConfig["folders"].append({"name": name, "path": path})
            workspaceConfig["settings"]["C_Cpp.default.includePath"].append(
                "${{workspaceFolder:{0}}}/**".format(name)
            )

        return workspaceConfig

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
        workspace.update(newWorkspace)
        # print("workspace: {0}".format(json.dumps(workspace, indent = 4)))

        # write new workspace
        with open(workspaceFile.as_posix(), "w") as file:
            json.dump(workspace, file, indent = 4)

        return True

    def generate(self, destinationDir):
        self.writeWorkspace(destinationDir)

class VsCodeGenerator(CommonIDEGenerator):
    def __init__(self):
        super().__init__("vscode", "Generate VS Code Workspace")

    def configure(self, package, argv):
        super().configure(package, argv)

    def generate(self, extra, bobRoot):
        super().generate()

        # gather root paths
        bobPwd = Path(os.getcwd())
        if sys.platform == 'msys':
            winPwd = PureWindowsPath(os.popen('pwd -W').read().strip())
            winDestination = PureWindowsPath(os.popen('cygpath -w {}'.format(quoteBash(self.destination))).read().strip())
        else:
            winPwd = bobPwd
            winDestination = Path(self.destination).resolve()

        # print("winDestination: {0}".format(winDestination))

        ws = VsCodeWorkspace()

        for package, scan in self.packages.items():
            # print("package: {0}".format(package))
            # print("  isRoot: {0}".format(scan.isRoot))
            # print("  packagePath: {0}".format(scan.stack))
            workspacePath = winPwd.joinpath(PureWindowsPath(scan.workspacePath)).as_posix()
            # print("  workspacePath: {0}".format(workspacePath))
            ws.addPackage(package, workspacePath)

        ws.generate(winDestination)

def vsCodeProjectGenerator(package, argv, extra, bobRoot):
    generator = VsCodeGenerator()
    generator.configure(package, argv)
    generator.generate(extra, bobRoot)
