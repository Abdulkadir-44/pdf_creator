#define MyAppName "Soru Otomasyon Sistemi"
#define MyAppVersion "2.0"
#define MyAppPublisher "Abdulkadir Özenç"
#define MyAppExeName "main_win7.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={commonpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=Setup_Win7
Compression=lzma
SolidCompression=yes
MinVersion=6.1sp1
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek görevler:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; DestName: "SoruOtomasyonSistemi.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\SoruOtomasyonSistemi.exe"
Name: "{group}\{#MyAppName} Kaldır"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\SoruOtomasyonSistemi.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SoruOtomasyonSistemi.exe"; Description: "Uygulamayı şimdi başlat"; Flags: nowait postinstall skipifsilent
