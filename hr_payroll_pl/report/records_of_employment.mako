<!DOCTYPE html>
<html>
    <% from datetime import date %>

    <%def name="start_page()">
        <div id="container">
            <table>
                <tr class="intro">
                    <td>Lp.</td>
                    <td>Imię i nazwisko</td>
                    <td>Imię ojca / imię matki</td>
                    <td>Miejsce zamieszkania</td>
                    <td>PESEL</td>
                    <td>NIP</td>
                    <td>Data przyjęcia do pracy</td>
                    <td>Data zwolnienia z pracy</td>
                    <td>Uwagi dot. przerw w zatrudnieniu</td>
                </tr>
    </%def>

    <%def name="print_line(line)">
        <tr>
            <td>${line[0]}</td>
            <td class="left">${line[1]}</td>
            <td class="left">${line[2]}</td>
            <td class="left">${line[3]}</td>
            <td>${line[4]}</td>
            <td>${line[5]}</td>
            <td>${line[6]}</td>
            <td>${line[7]}</td>
            <td class="left">${line[8]}</td>
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
        <div id="document-title">
            <br/>
            <p class="center">Ewidencja zatrudnienia w roku podatkowym ${year}.</p>
        </div>
        ${start_page()}
        %for line in datas:
            ${print_line(line)}

            ## Split page after 20 lines.
            %if not line[0] % 20:
                ${end_page()}
                ${start_page()}
            %endif
        %endfor
        ${end_page()}
    </body>
</html>
