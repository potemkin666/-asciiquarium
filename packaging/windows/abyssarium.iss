; Inno Setup script for Abyssarium.
;
; Inputs (relative to the repository root, which is the working directory the
; release workflow invokes ISCC from):
;   dist\Abyssarium\Abyssarium.exe   <- staged by scripts/build-windows.ps1
;   dist\Abyssarium\README.md        (optional)
;   dist\Abyssarium\LICENSE          (optional)
;   dist\Abyssarium\CREDITS.md       (optional)
;   dist\Abyssarium\icon.ico         (optional)
;
; Output:
;   dist\installer\Abyssarium-Setup-Windows.exe
;
; The version string can be overridden from the command line:
;   iscc /DMyAppVersion=1.2.3 packaging\windows\abyssarium.iss

#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif

#define MyAppName        "Abyssarium"
#define MyAppPublisher   "potemkin666"
#define MyAppURL         "https://github.com/potemkin666/-asciiquarium"
#define MyAppExeName     "Abyssarium.exe"
#define StagingDir       "..\..\dist\Abyssarium"
#define OutputDir        "..\..\dist\installer"

[Setup]
; A stable, randomly-generated AppId so future versions upgrade in place.
AppId={{B6F4B6F2-8C2F-4F4A-9F8E-AB22B2D5C0A1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases

; Install per-user by default — no admin prompt, no UAC dance for the
; non-technical user who just wants to double-click the installer.
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

OutputDir={#OutputDir}
OutputBaseFilename=Abyssarium-Setup-Windows
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; The LICENSE / Info files are picked up only if present in the staging dir.
#if FileExists(AddBackslash(SourcePath) + StagingDir + "\LICENSE")
  LicenseFile={#StagingDir}\LICENSE
#endif
#if FileExists(AddBackslash(SourcePath) + StagingDir + "\README.md")
  InfoAfterFile={#StagingDir}\README.md
#endif
#if FileExists(AddBackslash(SourcePath) + StagingDir + "\icon.ico")
  SetupIconFile={#StagingDir}\icon.ico
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#StagingDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#StagingDir}\README.md";       DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#StagingDir}\LICENSE";         DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#StagingDir}\CREDITS.md";      DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "{#StagingDir}\icon.ico";        DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu shortcut (always created).
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
; Desktop shortcut named "Start Abyssarium" (optional, off by default).
Name: "{autodesktop}\Start {#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
; Uninstaller entry under the Start Menu group.
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Offer to launch Abyssarium once installation finishes. The checkbox is on
; by default; the user can untick it.
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
