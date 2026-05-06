; ============================================================================
; SujinsInvestment — Inno Setup 6 Installer Script
;
; Requires:  Inno Setup 6.x  https://jrsoftware.org/isinfo.php
; Build:     Run build-release.bat  (or compile manually in Inno Setup IDE)
; Output:    installer\Output\SujinsInvestment-Setup-1.0.0.exe
; ============================================================================

#define AppName        "Sujin's Investment"
#define AppShortName   "SujinsInvestment"
#define AppVersion     "1.0.0"
#define AppPublisher   "Sujin M"
#define AppURL         "https://github.com/sujin-m"
#define AppExeName     "SujinsInvestment.exe"
#define AppDescription "Portfolio management console — Upstox & eToro"
#define SourceDir      "..\bin\publish\win-x64"

[Setup]
; ── Installer identity ──────────────────────────────────────────────────────
AppId={{8B3F2E1A-7C4D-4F9E-A2B5-1D6E8F3C0A9B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
AppCopyright=Copyright (C) 2026 {#AppPublisher}. All rights reserved.
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppDescription}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}

; ── Paths ───────────────────────────────────────────────────────────────────
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=Output
OutputBaseFilename={#AppShortName}-Setup-{#AppVersion}
SetupIconFile=..\Assets\app.ico
UninstallDisplayIcon={app}\{#AppExeName}

; ── UI & compression ────────────────────────────────────────────────────────
WizardStyle=modern
WizardResizable=no
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64

; ── Privileges ──────────────────────────────────────────────────────────────
; PrivilegesRequired=lowest means it installs per-user (no admin needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; ── Misc ────────────────────────────────────────────────────────────────────
DisableProgramGroupPage=yes
DisableWelcomePage=no
LicenseFile=..\LICENSE
CloseApplications=yes
RestartApplications=no
ChangesEnvironment=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Main executable (single-file self-contained)
Source: "{#SourceDir}\{#AppExeName}";   DestDir: "{app}"; Flags: ignoreversion
; Config files (user can edit these)
Source: "{#SourceDir}\appsettings.json"; DestDir: "{app}"; Flags: ignoreversion
; Development config — skip if not present
Source: "{#SourceDir}\appsettings.Development.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu
Name: "{group}\{#AppName}";             Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}";   Filename: "{uninstallexe}"
; Desktop (optional — controlled by task above)
Name: "{autodesktop}\{#AppName}";       Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch app after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up log/cache files left by the app on uninstall
Type: filesandordirs; Name: "{app}\logs"

[Code]
// Show a warning if .NET 8 Runtime is not present (self-contained so not strictly needed,
// but the Visual C++ Redistributable may be required on very old Windows 10 builds).
function InitializeSetup(): Boolean;
var
  Ver: TWindowsVersion;
begin
  GetWindowsVersionEx(Ver);
  // Windows 10 (build 17763+) or Windows 11 required
  if (Ver.Major < 10) or ((Ver.Major = 10) and (Ver.Build < 17763)) then
  begin
    MsgBox(
      'Sujin''s Investment requires Windows 10 (version 1809 or later) or Windows 11.' + #13#10 +
      'Please upgrade your operating system and try again.',
      mbError, MB_OK
    );
    Result := False;
  end
  else
    Result := True;
end;
