<!DOCTYPE html>
<html>
    <% from datetime import date %>
    <head>
        <style>
                ${css}
        </style>
        <meta charset="utf-8">
    </head>
    <body>
            <% setLang('pl_PL') %>
            <%
                LP=0
                payslip_sum_values = {}
            %>
            <div id="header">
	        <p id="header-company">${company.rml_header1 or company.partner_id.name or '&nbsp;'}</p>
	        <p id="date">${formatLang(str(date.today()),date=True)}</p>
	    </div>
        <div>
            <table>
                <tr class="intro">
                    <td colspan="21"> Paski listy płac </td>
                </tr>
                <tr></tr>
                <tr class="intro">
                    <td >LP</td>
                    <td >Imię nazwisko </td>
                    <td >Wynagrodzenie zasadnicze</td>
                    <td >Pomniejszenia za czas nieobecności</td>
                    <td >Dodatki</td>
                    <td >Wynagrodzenie za czas pracy</td>
                    <td >Wynagrodzenie za nieobecność</td>
                    <td >Zasiłki</td>
                    <td >Wysokość świadczeń nieodpłatnych</td>
                    <td >Składki na ubezpieczenie emerytalne</td>
                    <td >Składki na ubezpieczenie rentowe</td>
                    <td >Składki na ubezpieczenie chorobowe</td>
                    <td >Koszty uzyskania przychodu</td>
                    <td >Zmniejszenie zaliczki</td>
                    <td >Składka zdrowotna odliczona od zaliczki na PIT</td>
                    <td >Składka zdrowotna odliczona od wypłaty</td>
                    <td >Podatek do wpłaty</td>
                    <td >Ekwiwalenty</td>
                    <td >Kwota netto</td>
                    <td >Potrącenia</td>
                    <td >Do wypłaty</td>
                </tr>
                    %for payslip in objects:

                    <%
                        print payslip
                        LP+=1
                        payslip_data_values = payslip_data(payslip)
                        payslip_sum_values = sum_values(payslip_data_values, payslip_sum_values, payslip)
                        payslip_employee_name = employee_name(payslip)
                    %>
                    <tr>
                        <td>${LP}</td>
                        <td>${payslip_employee_name}</td>
                        <td>${formatLang(payslip_data_values['podstawa'] or '')}</td>
                        <td>${formatLang(payslip_data_values['pomniejszenie_za_nieobecnosc'] or '')}</td>
                        <td>${formatLang(payslip_data_values['dodatki'] or '')}</td>
                        <td>${formatLang(payslip_data_values['wynagrodzenie_praca'] or '')}</td>
                        <td>${formatLang(payslip_data_values['chorobowe'] or '')}</td>
                        <td>${formatLang(payslip_data_values['zasilki'] or '')}</td>
                        <td>${formatLang(payslip_data_values['swiadczenia'] or '')}</td>
                        <td>${payslip.emr_pracownik or ''}</td>
                        <td>${payslip.rent_pracownik or ''}</td>
                        <td>${payslip.chor_pracownik or ''}</td>
                        <td>${payslip.koszty_uzyskania or ''}</td>
                        <td>${payslip.zmniejszenie_zaliczki or ''}</td>
                        <td>${payslip.skladka_zdrowotna_odliczona or ''}</td>
                        <td>${payslip.skladka_zdrowotna_od_netto or ''}</td>
                        <td>${payslip.kwota_US or ''}</td>
                        <td>${formatLang(payslip_data_values['ekwiwalenty'] or '')}</td>
                        <td>${payslip.wyplata_przed_potraceniami or ''}</td>
                        <td>${formatLang(payslip_data_values['potracenia'] or '')}</td>
                        <td>${payslip.do_wyplaty or ''}</td>
                    </tr>
                          %endfor
                    <tr>
                        <td><b>Suma</b></td>
                        <td></td>
                        <td>${formatLang(payslip_sum_values['podstawa'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['pomniejszenie_za_nieobecnosc'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['dodatki'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['wynagrodzenie_praca'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['chorobowe'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['zasilki'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['swiadczenia'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['emr_pracownik'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['rent_pracownik'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['chor_pracownik'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['koszty_uzyskania'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['zmniejszenie_zaliczki'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['skladka_zdrowotna_odliczona'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['skladka_zdrowotna_od_netto'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['kwota_zaliczki_na_PIT'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['ekwiwalenty'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['wyplata_przed_potraceniami'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['potracenia'] or '')}</td>
                        <td>${formatLang(payslip_sum_values['do_wyplaty'] or '')}</td>
                    </tr>

            </table>
        </div>
        <div id="break"></div>

    </body>
</html>