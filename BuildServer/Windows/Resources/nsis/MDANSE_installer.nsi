!include "MUI.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"

!ifndef ARCH
  !error "No architecture defined (win32 or win-amd64)"
!endif


!ifndef VERSION
  !define VERSION 'DEV'
!endif

; The name of the installer
Name "MDANSE ${VERSION}"

; The name of the installer file to write
OutFile "${TARGET_DIR}\MDANSE-${VERSION}-${ARCH}.exe"

RequestExecutionLevel admin #NOTE: You still need to check user rights with UserInfo!

; The default installation directory
InstallDir "$PROGRAMFILES\MDANSE"

; Registry key to check for directory (so if you install again, it will overwrite the old one automatically)
InstallDirRegKey HKLM "Software\MDANSE" "Install_Dir"

; Will show the details of installation
ShowInstDetails show

; Will show the details of uninstallation
ShowUnInstDetails show

!define PUBLISHER "ISIS Neutron and Muon Source"
!define WEB_SITE "http://www.mdanse.org"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\MDANSE"
!define UNINST_ROOT_KEY "HKLM"

!define ICONS_DIR $INSTDIR\icons

; Prompt the user in case he wants to cancel the installation
!define MUI_ABORTWARNING

; define the icon for the installer file and the installer 'bandeau'
!define MUI_ICON   "icons\MDANSE.ico"
!define MUI_UNICON "icons\MDANSE_uninstall.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "icons\MDANSE_resized.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "icons\MDANSE_uninstall_resized.bmp"

!define WEB_ICON   "icons\website.ico"

!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of \
MDANSE release ${VERSION}.\
\n\nMDANSE (Molecular Dynamics ANalysis for Neutron Scattering Experiments) is an program for the analysis of Molecular Dynamics simulations. \
It is especially designed for the computation and decomposition of neutron scattering spectra. \
The structure and dynamics of the simulated systems can be characterized in terms of various space \
and time correlation functions."

; Insert a "Welcome" page in the installer
!insertmacro MUI_PAGE_WELCOME

; Insert a "License" page in the installer
!insertmacro MUI_PAGE_LICENSE "LICENSE"

; Insert a page to browse for the installation directory
!insertmacro MUI_PAGE_DIRECTORY

; Insert a page for actual installation (+display) of MDANSE
!insertmacro MUI_PAGE_INSTFILES

; Insert in the finish page the possibility to run MDANSE
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!define MUI_FINISHPAGE_RUN_TEXT "Start MDANSE ${VERSION}"
!define MUI_FINISHPAGE_RUN "$INSTDIR\MDANSE_launcher.bat"
; Insert in the finish page the possibility to view the changelog
!define MUI_FINISHPAGE_LINK_LOCATION "$INSTDIR\CHANGELOG.txt"
!define MUI_FINISHPAGE_LINK "View CHANGELOG"
; Insert in the finish page the possibility to create desktop shortcut
Function CreateDesktopShortCut
  CopyFiles /SILENT "$INSTDIR\MDANSE.lnk" "$DESKTOP"
FunctionEnd
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create desktop shortcut"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateDesktopShortCut
; Actually insert the finish page to the installer
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Set the installer language to english
!insertmacro MUI_LANGUAGE "English"

;RequestExecutionLevel user

Function .onInit
  ${If} ${ARCH} == "win-amd64"
    StrCpy $INSTDIR "$PROGRAMFILES64\MDANSE"
  ${Else}
    StrCpy $INSTDIR "$PROGRAMFILES\MDANSE"
  ${EndIf}
FunctionEnd

Section "MDANSE ${VERSION}" SEC01
  SetShellVarContext all
  SetOutPath "$INSTDIR"
  SetOverwrite on
  File /r /x *.pyc /x *.pyo /x *.log /x *.egg-info "${TARGET_DIR}\*"
  File "CHANGELOG.txt"
  File "LICENSE"
  File "MDANSE_launcher.bat"
  File "MDANSE_command_shell.bat"
  CreateDirectory "${ICONS_DIR}"
  SetOutPath "${ICONS_DIR}"
  SetOverwrite on
  File /oname=run.ico "${MUI_ICON}"
  File /oname=uninstall.ico "${MUI_UNICON}"
  File /oname=web.ico "${WEB_ICON}"
  File /oname=terminal.ico "icons\MDANSE_terminal.ico"
  SetOutPath "$INSTDIR"
  SetOverwrite on
  CreateDirectory "$SMPROGRAMS\MDANSE"
  CreateShortCut "$INSTDIR\MDANSE.lnk" "$INSTDIR\MDANSE_launcher.bat" "" "${ICONS_DIR}\run.ico" 0
  CreateShortCut "$INSTDIR\MDANSE_command_shell.lnk" \
					"$SYSDIR\cmd.exe" \
					'/K "$INSTDIR\MDANSE_command_shell.bat"' \
					"${ICONS_DIR}\terminal.ico" 0
  WriteIniStr "$INSTDIR\MDANSE.url" "InternetShortcut" "URL" "${WEB_SITE}"
  CreateShortCut "$INSTDIR\Website.lnk" "$INSTDIR\MDANSE.url" "" "${ICONS_DIR}\web.ico" 0
  CreateShortCut "$INSTDIR\Uninstall.lnk" "$INSTDIR\uninst.exe" "" "${ICONS_DIR}\uninstall.ico" 0

  WriteRegStr ${UNINST_ROOT_KEY} "${UNINST_KEY}" "DisplayName" "MDANSE"
  WriteRegStr ${UNINST_ROOT_KEY} "${UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${UNINST_ROOT_KEY} "${UNINST_KEY}" "DisplayIcon" "${ICONS_DIR}\run.ico"
  WriteRegStr ${UNINST_ROOT_KEY} "${UNINST_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr ${UNINST_ROOT_KEY} "${UNINST_KEY}" "URLInfoAbout" "${WEB_SITE}"
  WriteRegStr ${UNINST_ROOT_KEY} "${UNINST_KEY}" "Publisher" "${PUBLISHER}"

  WriteUninstaller "$INSTDIR\uninst.exe"
  SetAutoClose false
SectionEnd

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you really sure you want to uninstall MDANSE ?" IDYES +2
  Abort
FunctionEnd

Section uninstall
  SetShellVarContext all
  Delete "$INSTDIR\MDANSE.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\CHANGELOG.txt"
  Delete "$INSTDIR\MDANSE_launcher.bat"
  Delete "$INSTDIR\MDANSE_command_shell.bat"
  Delete "$INSTDIR\python27.dll"
  Delete "${ICONS_DIR}\run.ico"
  Delete "${ICONS_DIR}\terminal.ico"
  Delete "${ICONS_DIR}\uninstall.ico"
  Delete "${ICONS_DIR}\web.ico"

  Delete "$DESKTOP\MDANSE.lnk"

  Delete "$SMPROGRAMS\MDANSE\MDANSE_command_shell.lnk"
  Delete "$SMPROGRAMS\MDANSE\Uninstall.lnk"
  Delete "$SMPROGRAMS\MDANSE\Website.lnk"
  Delete "$SMPROGRAMS\MDANSE\MDANSE.lnk"
  RMDir /r "$SMPROGRAMS\MDANSE"
  RMDir /r "$INSTDIR"

  DeleteRegKey ${UNINST_ROOT_KEY} "${UNINST_KEY}"
  SetAutoClose false
SectionEnd
