<!DOCTYPE html>
<html>
    <% from datetime import date %>
    <head>
        <style type="text/css">
                ${css}
                #box-top-left{
                    position: relative;
                    float: left;
                    width: 80mm;
                    margin-bottom: 2mm;
                    margin-right: 20mm;
                    border-bottom: 1px solid #ededed;

                }
                #box-top-right{
                    position: relative;
                    float:left;
                    width: 80mm;
                    margin-bottom: 2mm;
                    border-bottom: 1px solid #ededed;
                }
                #mark-company {
                    position: relative;
                    float:left;
                    width:50mm;
                    min-height:20mm;
                    margin-right:20mm;
                }
                #mark-customer {
                    position: relative;
                    float:left;
                    width:50mm;
                    min-height:20mm;
                    margin: 0 auto;
                }
        </style>
        <meta charset="utf-8">
    </head>
    <body>
        %for o in objects:
            <% setLang(o.company_id.partner_id.lang) %>
            %for line in o.payslip_ids:
                %if not line.cywilnoprawna_id:
                    <% continue %>
                %endif
                <div id="header_webkit">
                    %if company.logo:
                        <div id="logo">
                            <img src="data:image;base64,${company.logo}"/>
                        </div>
                    %endif
                </div>
                <div id="date" align="right">Dnia: ${date.today()}</div>
                <div id="header-company">${company.name} </div>
                %if company.street:
                    <div id="header-company">${company.street} </div>
                %endif
                %if company.zip and company.city:
                    <div id="header-company">${company.zip} ${company.city} </div>
                %endif
                <div id="document-title" >
                    <h1>${"RACHUNEK DO UMOWY CYWILNOPRAWNEJ"} </h1>
                </div>

                <div id="container">
                    <div id="box-top-left">
                        <h2> ${"NUMER UMOWY"}</h2>
                        ${o.name}
                    </div>
                    <div id="box-top-right">
                        <h2> ${"DATA RACHUNKU"}</h2>
                        ${o.date}
                    </div>
                    <div id="box-top-left">
                        <h2> ${"ZAMAWIAJĄCY"}</h2>
                        ${company.name} <br/>
                        %if company.street:
                            ${company.street} <br/>
                        %endif
                        %if company.zip and company.city:
                            ${company.zip} ${company.city}
                         %endif
                    </div>
                    <div id="box-top-right">
                        <h2> ${"ZLECENIOBIORCA"}</h2>
                        ${line.employee_id.employee_surname} ${line.employee_id.employee_name}<br/>
                        %if line.employee_id.address_home_id.street:
                            ${line.employee_id.address_home_id.street}
                        %endif
                        %if line.employee_id.address_home_id.street2:
                            ${line.employee_id.address_home_id.street2}
                        %endif
                        %if line.employee_id.address_home_id.zip:
                            ${line.employee_id.address_home_id.zip}
                        %endif
                        %if line.employee_id.address_home_id.city:
                            ${line.employee_id.address_home_id.city}
                        %endif
                    </div>
                    <div id="content">
                        <h2> ${"WARTOŚĆ RACHUNKU"}</h2>
                        ${"KWOTA:"} ${formatLang(line.brutto)} <br/>
                        ${"SŁOWNIE:"} ${kwotaslownie(abs(line.brutto), company.currency_id.name)}
                    </div>
                    <div id="content">
                        <h2> ${"Oświadczenie Zleceniobiorcy dla celów podatkowych:"}</h2>
                        <table class="dane">
                            <tr class="title-table">
                                <td>${"Imię pierwsze"}</td>
                                <td>${"Imię drugie"}</td>
                                <td>${"Nazwisko"}</td>
                                <td>${"Nazwisko rodowe"}</td>
                                <td>${"Data urodzenia"}</td>
                                <td>${"Miejsce urodzenia"}</td>
                                <td>${"PESEL"}</td>
                                <td>${"NIP"}</td>
                            </tr>
                            <tr align="center">
                                <td>${line.employee_id.employee_name or ''}</td>
                                <td>${line.employee_id.second_name or ''}</td>
                                <td>${line.employee_id.employee_surname or ''}</td>
                                <td>${line.employee_id.family_surname or ''}</td>
                                <td>${line.employee_id.birthday or ''}</td>
                                <td>${line.employee_id.city or ''}</td>
                                <td>${line.employee_id.ssnid or ''}</td>
                                <td>${line.employee_id.sinid or ''}</td>
                            </tr>
                        </table>
                    </div>
                    <div id="box-top-left">
                        <h2> ${"Składki ZUS Płatnika"}</h2>
                        ${"Emerytalna:"} ${formatLang(line.emr_pracodawca)}<br/>
                        ${"Rentowa:"} ${formatLang(line.rent_pracodawca)}<br/>
                        ${"Wypadkowa:"} ${formatLang(line.wyp_pracodawca)}<br/>
                    </div>
                    <div id="box-top-right">
                        <% amount = 0.0 %>
                        %for deduction in line.deductions_ids:
                            <% amount += deduction.amount %>
                        %endfor
                        <h2> ${"Dane"}</h2>
                        ${"Kwota rachunku:"} ${formatLang(line.brutto)}<br/>
                        ${"Stawka podatku:"} ${formatLang(line.cywilnoprawna_id.procent_zaliczki_PIT)}<br/>
                        ${"Podatek do zapłaty:"} ${formatLang(line.kwota_US)}<br/>
                        ${"Potrącenia:"} ${formatLang(amount)}<br/>
                        ${"Koszty uzyskania przychodu:"} ${formatLang(line.koszty_uzyskania)}<br/>
                    </div>
                    <div id="box-top-left">
                        <h2> ${"Składki ZUS Ubezpieczonego"}</h2>
                        ${"Emerytalna:"} ${formatLang(line.emr_pracownik)}<br/>
                        ${"Rentowa:"} ${formatLang(line.rent_pracownik)}<br/>
                        ${"Chorobowa:"} ${formatLang(line.chor_pracownik)}<br/>
                    </div>
                    <div id="box-top-right">
                        <h2> ${"Do Wypłaty"}</h2>
                        %if line.cywilnoprawna_id.cash:
                            ${"Przelewem:"} ${"0,00"}<br/>
                            ${"Gotówką:"} ${formatLang(line.do_wyplaty)}<br/>
                        %else:
                            ${"Przelewem:"} ${formatLang(line.do_wyplaty)}<br/>
                            ${"Gotówką:"} ${"0,00"}<br/>
                        %endif
                    </div>
                    <div id="box-top-left">
                        <h2> ${"Składki na Ubezp. Zdrowotne"}</h2>
                        ${"Pobrana:"} ${formatLang(line.skladka_zdrowotna_od_netto)}<br/>
                        ${"Odliczona:"} ${formatLang(line.skladka_zdrowotna_odliczona)}<br/>
                    </div>
                </div>
                    <div id="mark-company">
                        <table class="center-box">
                            <h5>${"Rachunek sprawdzono pod względem merytorycznym"}</h5>
                            <hr/>
                            <td>${"data i podpis"}</td>
                          </table>
                    </div>
                    <div id="mark-customer">
                        <table class="center-box">
                        </table>
                    </div>

                    <div id="mark-customer">
                        <table class="center-box">
                            <h5>${"Potwierdzam zgodność danych"}</h5>
                            <hr/>
                            <td>${"podpis Zleceniodawcy"}</td>
                        </table>
                    </div>
                    <div id="mark-company">
                        <table class="center-box">
                            <h5>${"Rachunek sprawdzono pod względem formalno prawnym"}</h5>
                            <hr/>
                            <td>${"data i podpis"}</td>
                          </table>
                    </div>
                    <div id="mark-customer">
                        <table class="center-box">
                            <h5>${"Zatwierdzono do wypłaty"}</h5>
                            <hr/>
                            <td>${"data i podpis"}</td>
                          </table>
                    </div>
                    <div id="mark-customer">
                        <table class="center-box">
                            <h5>${"Kwotę powyższą otrzymałem"}</h5>
                            <hr/>
                            <td>${"podpis Zleceniobiorcy"}</td>
                        </table>
                    </div>
                <div id="break">&nbsp;</div>
            %endfor
        %endfor
    </body>
</html>