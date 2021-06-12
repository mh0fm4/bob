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

        codeWorkspace = {}
        codeWorkspace["folders"] = []

        for package, scan in self.packages.items():
            # print("package: {0}".format(package))
            # print("  isRoot: {0}".format(scan.isRoot))
            # print("  packagePath: {0}".format(scan.stack))
            workspacePath = winPwd.joinpath(PureWindowsPath(scan.workspacePath)).as_posix()
            # print("  workspacePath: {0}".format(workspacePath))
            codeWorkspace["folders"].append({"name": package, "path": workspacePath})

        # print("codeWorkspace: {0}".format(json.dumps(codeWorkspace, indent = 4)))

        self.writeWorkspace(winDestination, codeWorkspace)

    def writeWorkspace(self, destDir, workspace):
        newWorkspace = {}
        codeWorkspaceFile = destDir.joinpath("project.code-workspace")

        # read existing workspace
        try:
            with open(codeWorkspaceFile.as_poisx(), "r") as file:
                newWorkspace = json.load(file)
        except:
            pass

        # merge existing with new workspace
        newWorkspace.update(workspace)

        # write new workspace
        with open(codeWorkspaceFile.as_posix(), "w") as outfile:
            json.dump(newWorkspace, outfile, indent = 4)

def vsCodeProjectGenerator(package, argv, extra, bobRoot):
    generator = VsCodeGenerator()
    generator.configure(package, argv)
    generator.generate(extra, bobRoot)
