unit dif_Quest;

interface

uses
  Windows, Messages, SysUtils, Classes, Graphics, Controls, Forms, Dialogs,
  ComCtrls, ExtCtrls, StdCtrls, Buttons;

type
  TQuestDlg = class(TForm)
    PageControl1: TPageControl;
    TabSheet1: TTabSheet;
    TabSheet2: TTabSheet;
    TabSheet3: TTabSheet;
    TabSheet4: TTabSheet;
    TabSheet5: TTabSheet;
    TabSheet6: TTabSheet;
    TabSheet7: TTabSheet;
    TabSheet8: TTabSheet;
    TabSheet9: TTabSheet;
    RadioGroup1: TRadioGroup;
    Label1: TLabel;
    RadioGroup2: TRadioGroup;
    Label2: TLabel;
    RadioGroup3: TRadioGroup;
    RadioGroup4: TRadioGroup;
    RadioGroup5: TRadioGroup;
    RadioGroup6: TRadioGroup;
    RadioGroup7: TRadioGroup;
    RadioGroup8: TRadioGroup;
    Label3: TLabel;
    RadioGroup9: TRadioGroup;
    Label4: TLabel;
    Label5: TLabel;
    Label6: TLabel;
    Label7: TLabel;
    Label8: TLabel;
    Label9: TLabel;
    Label10: TLabel;
    Label11: TLabel;
    Label12: TLabel;
    Label13: TLabel;
    Label14: TLabel;
    Label15: TLabel;
    Label16: TLabel;
    Label17: TLabel;
    Label18: TLabel;
    Label19: TLabel;
    Label20: TLabel;
    Label21: TLabel;
    Label22: TLabel;
    Label23: TLabel;
    Image1: TImage;
    Image2: TImage;
    Image3: TImage;
    Image4: TImage;
    Image5: TImage;
    Image6: TImage;
    Image7: TImage;
    Image8: TImage;
    Image9: TImage;
    Image10: TImage;
    Image11: TImage;
    Image12: TImage;
    Image13: TImage;
    Image14: TImage;
    Image15: TImage;
    Image16: TImage;
    Label24: TLabel;
    Label25: TLabel;
    Label26: TLabel;
    Label27: TLabel;
    Label28: TLabel;
    Label29: TLabel;
    Label30: TLabel;
    RichEdit1: TRichEdit;
    RichEdit2: TRichEdit;
    RichEdit3: TRichEdit;
    RichEdit4: TRichEdit;
    RichEdit5: TRichEdit;
    RichEdit6: TRichEdit;
    RichEdit7: TRichEdit;
    RichEdit8: TRichEdit;
    RichEdit9: TRichEdit;
    HelpBtn: TButton;
    ReadyBtn: TButton;
    CancelBtn: TButton;
    procedure ReadyBtnClick(Sender: TObject);
    procedure HelpBtnClick(Sender: TObject);
    procedure FormClose(Sender: TObject; var Action: TCloseAction);
  end;

var
  QuestDlg: TQuestDlg;

implementation

{$R *.DFM}

procedure TQuestDlg.ReadyBtnClick(Sender: TObject);
begin
  If (RadioGroup1.ItemIndex=1) and (RadioGroup2.ItemIndex=3) and
     (RadioGroup3.ItemIndex=0) and (RadioGroup4.ItemIndex=3) and
     (RadioGroup5.ItemIndex=1) and (RadioGroup6.ItemIndex=0) and
     (RadioGroup7.ItemIndex=1) and (RadioGroup8.ItemIndex=2) and
     (RadioGroup9.ItemIndex=2) then ModalResult := mrOk
  else begin
    MessageDlg('Вы неправильно ответили на некоторые контрольные вопросы. Вы не можете приступить к выполнению работы пока не ответите на все вопросы. Выучите теорию.', mtInformation, [mbOk], 0);
    ModalResult := mrNone;
  end; 
end;

procedure TQuestDlg.HelpBtnClick(Sender: TObject);
begin
//  Application.HelpCommand(HELP_CONTENTS, 0);
  WinExec(PChar('C:\Program Files\Internet Explorer\Iexplore.exe '+GetCurrentDir+'\difHelp.htm'),SW_SHOW);
end;

procedure TQuestDlg.FormClose(Sender: TObject; var Action: TCloseAction);
begin
//  Application.HelpCommand(HELP_QUIT,0);
end;

end.
