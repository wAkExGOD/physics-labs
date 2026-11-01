program difraction;



uses
  Forms,
  Windows,
  Controls,
  dif_Main in 'dif_Main.pas' {MainForm},
  dif_About in 'dif_About.pas' {AboutDlg},
  dif_Quest in 'dif_Quest.pas' {QuestDlg},
  dif_List in 'dif_List.pas' {ListForm},
  dif_Graph in 'dif_Graph.pas' {GraphForm},
  dif_Demo in 'dif_Demo.pas' {DemoForm},
  dif_MPR in 'dif_MPR.pas' {MPRForm};

{$R *.RES}

var
  Result: TModalResult;

begin
  Application.Initialize;
  Application.Title := 'Дифракция электронов';
  Application.HelpFile := 'difraction.hlp';
  AboutDlg := TAboutDlg.Create(Application);
  AboutDlg.ShowModal;
  AboutDlg.MakeAbout;
  QuestDlg := TQuestDlg.Create(Application);

  if (ParamCount > 0) and (ParamStr(1) <> 'noquest') then Result := mrOk
  else Result := QuestDlg.ShowModal;
  //Result := mrOk;
  if Result = mrOk then
  begin
    Application.CreateForm(TMainForm, MainForm);
  Application.CreateForm(TListForm, ListForm);
  Application.CreateForm(TGraphForm, GraphForm);
  Application.CreateForm(TDemoForm, DemoForm);
  Application.CreateForm(TMPRForm, MPRForm);
  end;
  Application.Run;
end.
