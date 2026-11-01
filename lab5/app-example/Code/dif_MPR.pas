unit dif_MPR;

interface

uses
  Windows, Messages, SysUtils, Variants, Classes, Graphics, Controls, Forms,
  Dialogs, StdCtrls, jpeg, ExtCtrls, StrUtils, Math;

type
  TMPRForm = class(TForm)
    lblTitle: TLabel;
    elements: TComboBox;
    lblChoseElement: TLabel;
    Button1: TButton;
    table1: TImage;
    resultPanel: TPanel;
    table2: TImage;
    l1: TEdit;
    l2: TEdit;
    l3: TEdit;
    l4: TEdit;
    n1: TLabel;
    n2: TLabel;
    n3: TLabel;
    n4: TLabel;
    n5: TLabel;
    r11: TEdit;
    r21: TEdit;
    r31: TEdit;
    r41: TEdit;
    r51: TEdit;
    Label1: TLabel;
    Label2: TLabel;
    Label3: TLabel;
    Label4: TLabel;
    v1: TEdit;
    v2: TEdit;
    v3: TEdit;
    v4: TEdit;
    r12: TEdit;
    r22: TEdit;
    r32: TEdit;
    r42: TEdit;
    r52: TEdit;
    r13: TEdit;
    r23: TEdit;
    r33: TEdit;
    r43: TEdit;
    r53: TEdit;
    r14: TEdit;
    r24: TEdit;
    r34: TEdit;
    r44: TEdit;
    r54: TEdit;
    d1: TLabel;
    d2: TLabel;
    d3: TLabel;
    d4: TLabel;
    d5: TLabel;
    p1: TLabel;
    p2: TLabel;
    p3: TLabel;
    p4: TLabel;
    p5: TLabel;
    procedure FormCreate(Sender: TObject);
    procedure elementsChange(Sender: TObject);
    procedure Button1Click(Sender: TObject);
  private
    { Private declarations }
  public
    { Public declarations }
  end;

var
  MPRForm: TMPRForm;

implementation

{$R *.dfm}

Const
  L = 757;

procedure TMPRForm.FormCreate(Sender: TObject);
begin
  Left:=(Screen.Width-Width)  div 2;
  Top:=(Screen.Height-Height) div 2;
end;

procedure TMPRForm.elementsChange(Sender: TObject);
begin
  if(elements.ItemIndex = 0) then
      begin
        n1.Caption:='1';
        n2.Caption:='1';
        n3.Caption:='1';
        n4.Caption:='2';
        n5.Caption:='1';
      end;
    if(elements.ItemIndex = 1) then
      begin
        n1.Caption:='1';
        n2.Caption:='1';
        n3.Caption:='1';
        n4.Caption:='1';
        n5.Caption:='2';
      end;
end;

function StringToNormalFloat(text_value: string) : Extended;
  var
    res: Extended;
  begin
    if ((text_value = '') OR (text_value = '0')) then res := 1 else res := StrToFloat(AnsiReplaceStr(text_value, '.', ','));
    Result := res;
  end;

function StringToNormalFloatWithNull(text_value: string) : Extended;
  var
    res: Extended;
  begin
    if text_value = '' then res := 0 else res := StrToFloat(AnsiReplaceStr(text_value, '.', ','));
    Result := res;
  end;

procedure TMPRForm.Button1Click(Sender: TObject);
var
  do1, do2, do3, do4, do5, d11,d12,d13,d14,d21,d22,d23,d24,d31,d32,d33,d34,d41,d42,d43,d44,d51,d52,d53,d54: Extended;
  v1_val, v2_val, v3_val, v4_val: Extended;
  l1_val, l2_val, l3_val, l4_val: Extended;
  r11_val, r12_val, r13_val, r14_val: Extended;
  r21_val, r22_val, r23_val, r24_val: Extended;
  r31_val, r32_val, r33_val, r34_val: Extended;
  r41_val, r42_val, r43_val, r44_val: Extended;
  r51_val, r52_val, r53_val, r54_val: Extended;
  n1_val, n2_val, n3_val, n4_val, n5_val: Integer;
  f: System.Text;
  text: string;
begin
  //replace and check if empty block START
  n1_val:= StrToInt(n1.Caption);
  n2_val:= StrToInt(n2.Caption);
  n3_val:= StrToInt(n3.Caption);
  n4_val:= StrToInt(n4.Caption);
  n5_val:= StrToInt(n5.Caption);

  v1_val:= StringToNormalFloatWithNull(v1.Text);
  v2_val:= StringToNormalFloatWithNull(v2.Text);
  v3_val:= StringToNormalFloatWithNull(v3.Text);
  v4_val:= StringToNormalFloatWithNull(v4.Text);

  l1_val:= StringToNormalFloatWithNull(l1.Text);
  l2_val:= StringToNormalFloatWithNull(l2.Text);
  l3_val:= StringToNormalFloatWithNull(l3.Text);
  l4_val:= StringToNormalFloatWithNull(l4.Text);

  r11_val:= StringToNormalFloat(r11.Text);
  r12_val:= StringToNormalFloat(r12.Text);
  r13_val:= StringToNormalFloat(r13.Text);
  r14_val:= StringToNormalFloat(r14.Text);

  r21_val:= StringToNormalFloat(r21.Text);
  r22_val:= StringToNormalFloat(r22.Text);
  r23_val:= StringToNormalFloat(r23.Text);
  r24_val:= StringToNormalFloat(r24.Text);

  r31_val:= StringToNormalFloat(r31.Text);
  r32_val:= StringToNormalFloat(r32.Text);
  r33_val:= StringToNormalFloat(r33.Text);
  r34_val:= StringToNormalFloat(r34.Text);

  r41_val:= StringToNormalFloat(r41.Text);
  r42_val:= StringToNormalFloat(r42.Text);
  r43_val:= StringToNormalFloat(r43.Text);
  r44_val:= StringToNormalFloat(r44.Text);

  r51_val:= StringToNormalFloat(r51.Text);
  r52_val:= StringToNormalFloat(r52.Text);
  r53_val:= StringToNormalFloat(r53.Text);
  r54_val:= StringToNormalFloat(r54.Text);

  r51_val:= StringToNormalFloat(r51.Text);
  r52_val:= StringToNormalFloat(r52.Text);
  r53_val:= StringToNormalFloat(r53.Text);
  r54_val:= StringToNormalFloat(r54.Text);
  //replace and check if empty block END

  d11:= RoundTo(n1_val*(L/r11_val)*l1_val,-4);
  d12:= RoundTo(n1_val*(L/r12_val)*l2_val,-4);
  d13:= RoundTo(n1_val*(L/r13_val)*l3_val,-4);
  d14:= RoundTo(n1_val*(L/r14_val)*l4_val,-4);
  do1:= RoundTo((d11+d12+d13+d14)/4,-4);
  d1.Caption:= FloatToStr(RoundTo(do1,-2));

  d21:= RoundTo(n2_val*(L/r21_val)*l1_val,-4);
  d22:= RoundTo(n2_val*(L/r22_val)*l2_val,-4);
  d23:= RoundTo(n2_val*(L/r23_val)*l3_val,-4);
  d24:= RoundTo(n2_val*(L/r24_val)*l4_val,-4);
  do2:= RoundTo((d21+d22+d23+d24)/4,-4);
  d2.Caption:= FloatToStr(RoundTo(do2,-2));

  d31:= RoundTo(n3_val*(L/r31_val)*l1_val,-4);
  d32:= RoundTo(n3_val*(L/r32_val)*l2_val,-4);
  d33:= RoundTo(n3_val*(L/r33_val)*l3_val,-4);
  d34:= RoundTo(n3_val*(L/r34_val)*l4_val,-4);
  do3:= RoundTo((d31+d32+d33+d34)/4,-4);
  d3.Caption:= FloatToStr(RoundTo(do3,-2));

  d41:= RoundTo(n4_val*(L/r41_val)*l1_val,-4);
  d42:= RoundTo(n4_val*(L/r42_val)*l2_val,-4);
  d43:= RoundTo(n4_val*(L/r43_val)*l3_val,-4);
  d44:= RoundTo(n4_val*(L/r44_val)*l4_val,-4);
  do4:= RoundTo((d41+d42+d43+d44)/4,-4);
  d4.Caption:= FloatToStr(RoundTo(do4,-2));

  d51:= RoundTo(n5_val*(L/r51_val)*l1_val,-4);
  d52:= RoundTo(n5_val*(L/r52_val)*l2_val,-4);
  d53:= RoundTo(n5_val*(L/r53_val)*l3_val,-4);
  d54:= RoundTo(n5_val*(L/r54_val)*l4_val,-4);
  do5:= RoundTo((d51+d52+d53+d54)/4,-4);
  d5.Caption:= FloatToStr(RoundTo(do5,-2));

  p1.Caption:= '±'+FloatToStr(RoundTo( (Sqrt((Sqr(d11-do1)+Sqr(d12-do1)+Sqr(d13-do1)+ Sqr(d14-do1))/12 )) ,-3));
  p2.Caption:= '±'+FloatToStr(RoundTo( (Sqrt((Sqr(d21-do2)+Sqr(d22-do2)+Sqr(d23-do2)+ Sqr(d24-do2))/12 )) ,-3));
  p3.Caption:= '±'+FloatToStr(RoundTo( (Sqrt((Sqr(d31-do3)+Sqr(d32-do3)+Sqr(d33-do3)+ Sqr(d34-do3))/12 )) ,-3));
  p4.Caption:= '±'+FloatToStr(RoundTo( (Sqrt((Sqr(d41-do4)+Sqr(d42-do4)+Sqr(d43-do4)+ Sqr(d44-do4))/12 )) ,-3));
  p5.Caption:= '±'+FloatToStr(RoundTo( (Sqrt((Sqr(d51-do5)+Sqr(d52-do5)+Sqr(d53-do5)+ Sqr(d54-do5))/12 )) ,-3));


  AssignFile(f,'mpr_result.txt');
  Rewrite(f);
  //Reset(f); //ןנמסעמ מעךנûגאול פאיכ הכÿ נוהאךעטנמגאםטÿ
  WriteLn(f,'Äאםםûו ןמ נאסק¸עאל ÌÏÐ (מבנאחוצ ' + elements.Text + ')');
  WriteLn(f,'');

  Write(f,'V1 = '+v1.Text+'ךÂ; ');
  Write(f,'V2 = '+v2.Text+'ךÂ; ');
  Write(f,'V3 = '+v3.Text+'ךÂ; ');
  WriteLn(f,'V4 = '+v4.Text+'ךÂ; ');

  Write(f,'L1 = '+l1.Text+'Àםדסענול; ');
  Write(f,'L2 = '+l2.Text+'Àםדסענול; ');
  Write(f,'L3 = '+l3.Text+'Àםדסענול; ');
  WriteLn(f,'L4 = '+l4.Text+'Àםדסענול; ');

  Write(f,'R11 = '+r11.Text+'לל; ');
  Write(f,'R12 = '+r12.Text+'לל; ');
  Write(f,'R13 = '+r13.Text+'לל; ');
  Write(f,'R14 = '+r14.Text+'לל; ');
  WriteLn(f,'<d1> = ('+d1.Caption+p1.Caption+')Àםדסענול; ');

  Write(f,'R21 = '+r21.Text+'לל; ');
  Write(f,'R22 = '+r22.Text+'לל; ');
  Write(f,'R23 = '+r23.Text+'לל; ');
  Write(f,'R24 = '+r24.Text+'לל; ');
  WriteLn(f,'<d2> = ('+d2.Caption+p2.Caption+')Àםדסענול; ');

  Write(f,'R31 = '+r31.Text+'לל; ');
  Write(f,'R32 = '+r32.Text+'לל; ');
  Write(f,'R33 = '+r33.Text+'לל; ');
  Write(f,'R34 = '+r34.Text+'לל; ');
  WriteLn(f,'<d3> = ('+d3.Caption+p3.Caption+')Àםדסענול; ');

  Write(f,'R41 = '+r41.Text+'לל; ');
  Write(f,'R42 = '+r42.Text+'לל; ');
  Write(f,'R43 = '+r43.Text+'לל; ');
  Write(f,'R44 = '+r44.Text+'לל; ');
  WriteLn(f,'<d4> = ('+d4.Caption+p4.Caption+')Àםדסענול; ');

  Write(f,'R51 = '+r51.Text+'לל; ');
  Write(f,'R52 = '+r52.Text+'לל; ');
  Write(f,'R53 = '+r53.Text+'לל; ');
  Write(f,'R54 = '+r54.Text+'לל; ');
  WriteLn(f,'<d5> = ('+d5.Caption+p5.Caption+')Àםדסענול; ');

  CloseFile(f); //חאךנûגאול פאיכ
end;

end.
