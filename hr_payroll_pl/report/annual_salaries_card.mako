<!DOCTYPE html>
<html>
    <% from datetime import date %>

    <%def name="start_page()">
        <div id="container">
    </%def>

    <%def name="print_header()">
        <table>
            <tr class="intro">
                <td rowspan="2">Lp.</td>
                <td rowspan="2">Miesiąc wypłaty wynagrodzenia</td>
                <td rowspan="2">Suma przychodów brutto, w gotówce i w naturze</td>
                <td rowspan="2">Koszty uzyskania przychodów</td>
                <td colspan="3">Składki na ubezpieczenie społeczne w części finansowanej przez pracownika</td>
                <td rowspan="2">Podstawa obliczenia zaliczki na podatek</td>
                <td rowspan="2">Dochód narastająco od początku roku</td>
                <td rowspan="2">Kwota należnej zaliczki na podatek</td>
                <td rowspan="2">Kwota należnej składki zdrowotnej</td>
                <td rowspan="2">Kwota składki zdrowotnej podlegającej odliczeniu</td>
                <td rowspan="2">Kwota zaliczki na podatek do zapłaty</td>
                <td rowspan="2">Data przekazania zaliczki na podatek do urzędu skarbowego</td>
            </tr>
            <tr class="intro" style="background-color:#ececec;">
                <td>emerytalna</td>
                <td>rentowa</td>
                <td>chorobowa</td>
            </tr>
            <tr></tr>
    </%def>

    <%def name="print_employee_info(info)">
        <div style="margin-bottom: 50px">
            <div style="float:left;">
                <b>Imię i nazwisko pracownika:</b><br/>
                <b>NIP:</b><br/>
                <b>PESEL:</b><br/>
            </div>
            <div style="float:left; margin-left: 10px;">
                ${info[0]}<br/>
                ${info[1]}<br/>
                ${info[2]}<br/>
            </div>
        </div>
    </%def>

    <%def name="print_lines(data)">
        %for line in data[1]:
            <tr>
                %for val in line:
                    <td>${val}</td>
                %endfor
            </tr>
        %endfor
        <tr>
            <td colspan="2"><center><b>SUMA</b></center></td>
            %for val in data[2]:
                <td><b>${val}</b></td>
            %endfor
        </tr>
    </%def>

    <%def name="end_page()">
            </table>
        </div>
        <div id="break"></div>
    </%def>

    <head>
        <style>
                ${css}
        </style>
        <meta charset="utf-8">
    </head>
    <body>
        <% setLang('pl_PL') %>
        <div id="header">
	        <p id="header-company">${company.rml_header1 or company.partner_id.name or '&nbsp;'}</p>
	        <p id="date">${formatLang(str(date.today()),date=True)}</p>
	    </div>

        ## Print page for each employee.
        %for line in datas:
            <div id="document-title">
                <br/>
                <p class="center">KARTA PRZYCHODÓW PRACOWNIKA ZA ROK PODATKOWY ${year}.</p>
            </div>

            ${start_page()}
            ${print_employee_info(line[0])}
            ${print_header()}
            ${print_lines(line)}
            ${end_page()}
        %endfor
    </body>
</html>
