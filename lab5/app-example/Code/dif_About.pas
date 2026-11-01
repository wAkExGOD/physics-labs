unit dif_About;

interface

uses Windows, SysUtils, Classes, Graphics, Forms, Controls, StdCtrls,
  Buttons, ExtCtrls;

type
  TAboutDlg = class(TForm)
    Bevel1: TBevel;
    Label5: TLabel;
    Label1: TLabel;
    Label3: TLabel;
    Label6: TLabel;
    OKBtn: TButton;
    GroupBox1: TGroupBox;
    Label2: TLabel;
    procedure CreateForm(Sender: TObject);
  public
    procedure MakeSplash;
    procedure MakeAbout;
  end;

var
  AboutDlg: TAboutDlg;

implementation

{$R *.DFM}

procedure TAboutDlg.MakeSplash;
var
  lStyle: LongInt;
begin
  lStyle := GetWindowLong(Handle, GWL_STYLE);
  lStyle := lStyle and (not WS_CAPTION);
  SetWindowLong(Handle, GWL_STYLE, lStyle);
  Height := Height - GetSystemMetrics(SM_CYCAPTION);
  Refresh;
end;

procedure TAboutDlg.MakeAbout;
var
  lStyle: LongInt;
begin
  lStyle := GetWindowLong(Handle, GWL_STYLE);
  lStyle := lStyle or WS_CAPTION;
  SetWindowLong(Handle, GWL_STYLE, lStyle);
  Height := Height + GetSystemMetrics(SM_CYCAPTION);
  Refresh;
end;

procedure TAboutDlg.CreateForm(Sender: TObject);
begin
  MakeSplash;
end;

end.
