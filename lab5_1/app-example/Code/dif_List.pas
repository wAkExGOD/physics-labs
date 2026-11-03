unit dif_List;

interface

uses
  Windows, Messages, SysUtils, Classes, Graphics, Controls, Forms, Dialogs,
  StdCtrls, Buttons;

type
  TListForm = class(TForm)
    GroupBox1: TGroupBox;
    Label1: TLabel;
    edVoltage: TEdit;
    Label2: TLabel;
    edNumber: TEdit;
    Label5: TLabel;
    edStep: TEdit;
    OkBtn: TButton;
    CancelBtn: TButton;
  private
    { Private declarations }
  public
    { Public declarations }
  end;

var
  ListForm: TListForm;

implementation

{$R *.DFM}

end.
