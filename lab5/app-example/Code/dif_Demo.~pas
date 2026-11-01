unit dif_Demo;

interface

uses
  Windows, Messages, SysUtils, Variants, Classes, Graphics, Controls, Forms,
   Dialogs, GIFImage, ExtCtrls, StdCtrls, ComCtrls, Gauges, jpeg;

type
  TDemoForm = class(TForm)
    btnStart: TButton;
    timerExperiment: TTimer;
    Label1: TLabel;
    btnReset: TButton;
    Label3: TLabel;
    Label4: TLabel;
    Label5: TLabel;
    Label6: TLabel;
    tiPhoto: TImage;
    gProgress: TGauge;
    Label2: TLabel;
    electronsNumber: TEdit;
    Label7: TLabel;
    Label8: TLabel;
    Label9: TLabel;
    Label10: TLabel;
    Label11: TLabel;
    Label12: TLabel;
    Label13: TLabel;
    tiPhoto2: TImage;
    btnStop: TButton;
    pushka: TImage;
    Image1: TImage;
    GroupBox1: TGroupBox;
    Panel1: TPanel;
    imgRayFirst: TImage;
    imgRayTwo: TImage;
    CheckBox1: TCheckBox;
    procedure Ferum;
    procedure ResetAndCreatAction;
    procedure btnStartClick(Sender: TObject);
    procedure FormCreate(Sender: TObject);
    procedure timerExperimentTimer(Sender: TObject);
    procedure btnStopClick(Sender: TObject);
    procedure btnResetClick(Sender: TObject);
    procedure FormClose(Sender: TObject; var Action: TCloseAction);
    procedure electronsNumberChange(Sender: TObject);
    procedure CheckBox1Click(Sender: TObject);
  public
    { Public declarations }
  end;

var
  DemoForm: TDemoForm;
  N,K,K1,X0,Y0,X00,Y00: Word;
  RM,A,B,Y,F,CoefPlosk,CoefPlosk2,S: Extended;
  temp, tempp1, tempp2, CoefChastota: Integer;
  colorEmulsii, colorPen: TColor;

implementation

Const
  R0 = 0.071;
  R1 = 0.326;
  R2 = 0.459;
  R3 = 0.561;
  R4 = 0.653;
  R5 = 0.714;
  R6 = 0.857;
  R7 = 0.97;
{$R *.DFM}

{$R myresource.res}

procedure TDemoForm.Ferum;
  begin
    gProgress.Progress:=Round((K/N)*100);
    A:=Random;
    B:=Random;
    CoefPlosk:=Random;
    CoefPlosk2:=Random;
    if(Random>0.5)then tempp1:=1 else tempp1:=-1;
    if(Random>0.5)then tempp2:=1 else tempp2:=-1;
    F:=B*6.2832;
{1} If Abs(A-R1)<0.05 then
      begin
        If (A-R1)<0 then temp:=-1
          else temp:=1;
          Y:=(R1+8.000001E-3)*temp*Exp(-Sqr((A-R1)*3.5));
          tiPhoto.Canvas.Pixels[X0+Round(Y*RM*Cos(F)),Y0+Round(Y*RM*Sin(F))]:=colorPen;
          if((K mod CoefChastota) = 0) then begin
            tiPhoto2.Canvas.Pixels[X00+tempp1*Round(RM*R1)+Round(1*CoefPlosk),Y00+tempp2*Round(2*CoefPlosk2)]:=colorPen;
          end;
          K1:=K1+1;
        end;
{2} If Abs(A-R2)<0.015 then
      begin
        If (A-R2)<0 then temp:=-1
          else temp:=1;
          Y:=(R2+0.007)*temp*Exp(-Sqr((A-R2)*3.5));
          tiPhoto.Canvas.Pixels[X0+Round(Y*RM*Cos(F)),Y0+Round(Y*RM*Sin(F))]:=colorPen;
          if((K mod CoefChastota) = 0) then begin
            tiPhoto2.Canvas.Pixels[X00+tempp1*Round(RM*R2)+Round(1*CoefPlosk),Y00+tempp2*Round(2*CoefPlosk2)]:=colorPen;
          end;
          K1:=K1+1;
        end;
{3} If Abs(A-R3)<0.015 then
      begin
        If (A-R3)<0 then temp:=-1
          else temp:=1;
          Y:=(R3+0.002)*temp*Exp(-Sqr((A-R3)*3.5));
          tiPhoto.Canvas.Pixels[X0+Round(Y*RM*Cos(F)),Y0+Round(Y*RM*Sin(F))]:=colorPen;
          if((K mod CoefChastota) = 0) then begin
            tiPhoto2.Canvas.Pixels[X00+tempp1*Round(RM*R3)+Round(1*CoefPlosk),Y00+tempp2*Round(2*CoefPlosk2)]:=colorPen;
          end;
          K1:=K1+1;
        end;
{4} If Abs(A-R4)<0.005 then
      begin
        If A-R4<0 then temp:=-1
          else temp:=1;
          Y:=(R4+0.002)*temp*Exp(-Sqr((A-R4)*3.5));
          tiPhoto.Canvas.Pixels[X0+Round(Y*RM*Cos(F)),Y0+Round(Y*RM*Sin(F))]:=colorPen;
          if((K mod CoefChastota) = 0) then begin
            tiPhoto2.Canvas.Pixels[X00+tempp1*Round(RM*R4)+Round(1*CoefPlosk),Y00+tempp2*Round(2*CoefPlosk2)]:=colorPen;
          end;
          K1:=K1+1;
        end;
{5} If Abs(A-R5)<0.01 then
      begin
        If (A-R5)<0 then temp:=-1
          else temp:=1;
          Y:=(R5+0.002)*temp*Exp(-Sqr((A-R5)*3.5));
          tiPhoto.Canvas.Pixels[X0+Round(Y*RM*Cos(F)),Y0+Round(Y*RM*Sin(F))]:=colorPen;
          if((K mod CoefChastota) = 0) then begin
            tiPhoto2.Canvas.Pixels[X00+tempp1*Round(RM*R5)+Round(1*CoefPlosk),Y00+tempp2*Round(2*CoefPlosk2)]:=colorPen;
          end;
          K1:=K1+1;
        end;
{6} If Abs(A-R6)<0.005 then
      begin
        If (A-R6)<0 then temp:=-1
          else temp:=1;
          Y:=(R6+0.002)*temp*Exp(-Sqr((A-R6)*3.5));
          tiPhoto.Canvas.Pixels[X0+Round(Y*RM*Cos(F)),Y0+Round(Y*RM*Sin(F))]:=colorPen;
          if((K mod CoefChastota) = 0) then begin
            tiPhoto2.Canvas.Pixels[X00+tempp1*Round(RM*R6)+Round(1*CoefPlosk),Y00+tempp2*Round(2*CoefPlosk2)]:=colorPen;
          end;
          K1:=K1+1;
        end;
{7} If Abs(A-R7)<0.003 then
      begin
        If A-R7<0 then temp:=-1
          else temp:=1;
          Y:=(R7+0.002)*temp*Exp(-Sqr((A-R7)*3.5));
          tiPhoto.Canvas.Pixels[X0+Round(Y*RM*Cos(F)),Y0+Round(Y*RM*Sin(F))]:=colorPen;
          if((K mod CoefChastota) = 0) then begin
            tiPhoto2.Canvas.Pixels[X00+tempp1*Round(RM*R7)+Round(1*CoefPlosk),Y00+tempp2*Round(2*CoefPlosk2)]:=colorPen;
          end;
          K1:=K1+1;
        end;
      If A<R0 then
        begin
          Y:=A*1.4;
          tiPhoto.Canvas.Pixels[X0+Round(Y*RM*Cos(F)),Y0+Round(Y*RM*Sin(F))]:=colorPen;
          if((K mod Round(CoefChastota/2)) = 0) then begin
            tiPhoto2.Canvas.Pixels[X00+tempp1*Round(RM*CoefPlosk*R0),Y00+tempp2*Round(2*CoefPlosk2)]:=colorPen;
          end;
          K1:=K1+1;
        end;
  end;



procedure TDemoForm.ResetAndCreatAction;
begin
  X00:=tiPhoto2.Width div 2;
  Y00:=tiPhoto2.Height div 2;
  tiPhoto2.Canvas.Brush.Color:=colorEmulsii;
  tiPhoto2.Canvas.Brush.Style:=bsSolid;
  tiPhoto2.Canvas.FillRect(Rect(0,0,200,5));
  tiPhoto2.Canvas.Pixels[X00,Y00]:=colorEmulsii;
  K:=0;
  K1:=0;
  RM:=Round(600/SQRT(50));
  tiPhoto.Canvas.Brush.Color:=colorEmulsii;
  tiPhoto.Canvas.Brush.Style:=bsSolid;
  //сброс конваса перед рисованием
  //(что бы точки не стакалиськак в пуске с добавлением)
  tiPhoto.Canvas.FillRect(Rect(0,0,200,200));
  N:= StrToInt(electronsNumber.Text);
  X0:=tiPhoto.Width div 2;
  Y0:=tiPhoto.Height div 2;
  //задаем скорость экспиримента (10 нормально)
  S:=5;
  CoefChastota:=10;
  timerExperiment.Enabled:=False;
  timerExperiment.Interval:=trunc(S);
  btnStart.Enabled:=True;
  CheckBox1.Enabled:=True;
  btnStop.Enabled:=False;
  btnReset.Enabled:=False;
  Label12.Visible:=False;
  Label13.Visible:=False;
  Label1.Visible:=True;
  Label5.Visible:=True;
  tiPhoto.Visible:=True;
  imgRayFirst.Visible:=False;
  imgRayTwo.Visible:=False;
  gProgress.Progress:= 0;
end;



procedure TDemoForm.FormCreate(Sender: TObject);
begin
  Left:=(Screen.Width-Width)  div 2;
  Top:=(Screen.Height-Height) div 2;
  if CheckBox1.Checked then begin
    colorEmulsii:=clWhite;
    colorPen:= clBlack;
  end
  else begin
    colorEmulsii:=clBlack;
    colorPen:= clWhite;
  end;
  ResetAndCreatAction();
end;



procedure TDemoForm.timerExperimentTimer(Sender: TObject);
begin
  if K>N then begin
    timerExperiment.Enabled:=False;
    imgRayFirst.Visible:=False;
    imgRayTwo.Visible:=False;
    btnStart.Enabled:=False;
    btnStop.Enabled:=False;
  end;
  if K<=N then begin
    Inc(K);
    Ferum();
    Label13.Caption:=IntToStr(K1);
  end;
end;



procedure TDemoForm.btnStartClick(Sender: TObject);
begin
  timerExperiment.Enabled:=True;
  Label12.Visible:=True;
  Label13.Visible:=True;
  imgRayFirst.Visible:=True;
  imgRayTwo.Visible:=True;
  CheckBox1.Enabled:=False;
  btnStart.Enabled:=False;
  btnStop.Enabled:=True;
  btnReset.Enabled:=True;

end;



procedure TDemoForm.btnStopClick(Sender: TObject);
begin
  timerExperiment.Enabled:=False;
  btnStart.Enabled:=True;
  btnStop.Enabled:=False;
  imgRayFirst.Visible:=False;
  imgRayTwo.Visible:=False;
end;



procedure TDemoForm.btnResetClick(Sender: TObject);
begin
  ResetAndCreatAction();
end;

procedure TDemoForm.FormClose(Sender: TObject; var Action: TCloseAction);
begin
  ResetAndCreatAction();
end;



procedure TDemoForm.electronsNumberChange(Sender: TObject);
begin
  N:= StrToInt(electronsNumber.Text);
end;


procedure TDemoForm.CheckBox1Click(Sender: TObject);
begin
  if CheckBox1.Checked then begin
    colorEmulsii:=clWhite;
    colorPen:= clBlack;
  end
  else begin
    colorEmulsii:=clBlack;
    colorPen:= clWhite;
  end;
  tiPhoto.Canvas.Brush.Color:=colorEmulsii;
  tiPhoto.Canvas.FillRect(Rect(0,0,200,200));
  tiPhoto2.Canvas.Brush.Color:=colorEmulsii;
  tiPhoto2.Canvas.FillRect(Rect(0,0,200,5));
end;

end.
