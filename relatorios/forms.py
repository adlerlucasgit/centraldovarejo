from django import forms


class FiltroRelatorioForm(forms.Form):
    data_inicial = forms.DateField(
        required=True,
        label="Data inicial",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            },
            format="%Y-%m-%d",
        ),
        input_formats=["%Y-%m-%d"],
    )

    data_final = forms.DateField(
        required=True,
        label="Data final",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            },
            format="%Y-%m-%d",
        ),
        input_formats=["%Y-%m-%d"],
    )

    def clean(self):
        dados = super().clean()

        data_inicial = dados.get("data_inicial")
        data_final = dados.get("data_final")

        if data_inicial and data_final:
            if data_inicial > data_final:
                raise forms.ValidationError(
                    "A data inicial não pode ser posterior à data final."
                )

        return dados
