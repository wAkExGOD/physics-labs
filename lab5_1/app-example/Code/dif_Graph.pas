unit dif_Graph;

interface

uses
  Windows, Messages, SysUtils, Classes, Graphics, Controls, Forms, Dialogs,
  StdCtrls, Buttons, OleCtrls, chartfx3, ExtCtrls, dif_Main;

type
  TGraphForm = class(TForm)
    BitBtn1: TBitBtn;
    imGraph: TImage;
    Label1: TLabel;
    Label2: TLabel;
    LoadImage1: TImage;
    Image1: TImage;
    procedure FormShow(Sender: TObject);
  private
    { Private declarations }
  public
    { Public declarations }
    Procedure DrawGraph;
  end;

var
  GraphForm: TGraphForm;
  GraphTable : Array[1..3,1..20] of real;

implementation

uses dif_List;

{$R *.DFM}

Procedure TGraphForm.DrawGraph;
Var
  i : integer;
begin
  if(ElementAbr = 'Si') then begin
    LoadImage1.Picture:=Image1.Picture;
  end;
  imGraph.Picture.Assign(LoadImage1.Picture);
  imGraph.Canvas.Pen.Color:=clBlue;
  imGraph.Canvas.MoveTo(50,150-Round(GraphTable[1,1]*100));
  i:=2;
  While (i<=20) and (i<=(N div StrToInt(ListForm.edStep.Text))) do
    begin
      imGraph.Canvas.LineTo(50+((i-1)*20),150-Round(GraphTable[1,i]*1000));
      Inc(i);
    end;
  imGraph.Canvas.Pen.Color:=clFuchsia;
  imGraph.Canvas.MoveTo(50,150-Round(GraphTable[2,1]*100));
  i:=2;
  While (i<=20) and (i<=(N div StrToInt(ListForm.edStep.Text))) do
    begin
      imGraph.Canvas.LineTo(50+((i-1)*20),150-Round(GraphTable[2,i]*1000));
      Inc(i);
    end;
  imGraph.Canvas.Pen.Color:=clRed;
  imGraph.Canvas.MoveTo(50,150-Round(GraphTable[3,1]*100));
  i:=2;
  While (i<=20) and (i<=(N div StrToInt(ListForm.edStep.Text))) do
    begin
      imGraph.Canvas.LineTo(50+((i-1)*20),150-Round(GraphTable[3,i]*1000));
      Inc(i);
    end;
  Label2.Caption:='Количество выпущеных электронов равно N*'+ListForm.edStep.Text;
end;

procedure TGraphForm.FormShow(Sender: TObject);
begin
  GraphForm.DrawGraph;
end;

end.
