<!DOCTYPE html>
<html>

<% from math import ceil %>
<% from datetime import datetime %>
<% from lacan_tools.lacan_tools import lacan_round %>

<% date_format = "%Y-%m-%d" %>
<% date_format_html = "%Y<br>%m-%d" %>

<%def name="empty(x)">
    %for i in range(1,x):
    <tr class="benefit_card">
        %for j in range(1,17):
        <td></td>
        %endfor
    </tr>
    %endfor
</%def>

<%def name="line(x,y,z)">
    <tr class="intro">
        <td colspan="3" class="benefit_card">
            Lista wypłat
        </td>
        <td colspan="3" class="benefit_card">
            Okres niezdolności do pracy
        </td>
        <td rowspan="2" class="benefit_card_16 benefit_card">
            Dzienny zasiłek<br><br>zł, gr
        </td>
        <td rowspan="2" class="benefit_card_16 benefit_card">
            Zasiłek (brutto)<br><br>zł, gr
        </td>
        <td rowspan="2" class="benefit_card_16 benefit_card">
            Przypis podatku<br><br>zł, gr
        </td>
        <td rowspan="2" class="benefit_card_18 benefit_card">
            Kwota potrąconej zaliczki na podatek<br><br>zł, gr
        </td>
        <td rowspan="2" class="benefit_card_16 benefit_card">
            Zasiłek (netto)<br><br>zł, gr
        </td>
        <td rowspan="2" class="benefit_card_20 benefit_card">
            Rodzaj i procent zasiłku
        </td>
        <td rowspan="2" class="benefit_card_16 benefit_card">
            Kod literowy
        </td>
        <td colspan="2" class="benefit_card">
            Wynagrodzenie lub przychód przyjęty do obliczenia zasiłku
        </td>
        <td rowspan="2" class="benefit_card_18 benefit_card">
            Z okresu zasiłkowego wypłac. za dni
        </td>
    </tr>
    <tr id="blank">
        <td></td>
    </tr>
    <tr class="intro">
        <td class="benefit_card_12 benefit_card">Nr</td>
        <td class="benefit_card_8 benefit_card">Data</td>
        <td class="benefit_card_8 benefit_card">Nr poz.</td>
        <td class="benefit_card_8 benefit_card">od</td>
        <td class="benefit_card_8 benefit_card">do</td>
        <td class="benefit_card_8 benefit_card">dni</td>
        <td class="benefit_card_16 benefit_card">za miesiące</td>
        <td class="benefit_card_16 benefit_card">przeciętny</td>
    </tr>
    <tr class="intro">
        %for i in range(1,17):
        <td class="benefit_card">${i}</td>
        %endfor
    </tr>
    
    <% lines = line_datas(z['lines']) %>
    
    %for number in range(x, y):
	    <% pos16 = 0 %>
	    <% absences = find_absences(udata['employee_id'], lines[number]['date_start'], lines[number]['date_stop']) %>
	    
	    %for absence in absences:
		    <% date_from_days = datetime.strptime(absence['date_from_days'], date_format) %>
		    <% date_to_days = datetime.strptime(absence['date_to_days'], date_format) %>
		    <% pos16 += (date_to_days-date_from_days).days+1 %>
	    %endfor
    
	    <% pos06 = lines[number]['number_of_days']%>
	    <% pos07 = lacan_round(lines[number]['value']/pos06, 2) %>
	    <% pos08 = lines[number]['value'] %>
	    <% pos09 = lacan_round(lacan_round(pos08, 0) * tax(udata['employee_id'], lines[number]['date_start'][5:7], lines[number]['date_start'][:4], lines[number]['date_stop']), 2) %>
	    <% pos10 = lacan_round(pos09, 0) %>
	    <% pos11 = pos08-pos10 %>
	    <% pos12 = absences[0]['name'] + ' ' + str(absences[0]['rate'])+'%' %>
	    <% pos14_1 = str(absences[0]['base_month_start']) + '/' + str(absences[0]['base_year_start']) %>
	    <% pos14_2 = str(absences[0]['base_month_stop']) + '/' + str(absences[0]['base_year_stop']) %>
	    <% pos15 = lines[number]['base'] %>
	    
	    <tr class="benefit_card">
	    	%if lines[number]['zasilek'] != 'Sick pay':
		        <td class="benefit_card">${lines[number]['name']}</td>
		        <td class="benefit_card">${lines[number]['date']}</td>
		        <td class="benefit_card">${lines[number]['number']}</td>
		    %else:
	        	<td></td>
	        	<td></td>
	        	<td></td>
		    %endif
		    
	        <td class="benefit_card">${datetime.strptime(lines[number]['date_start'], date_format).strftime(date_format_html)}</td>
	        <td class="benefit_card">${datetime.strptime(lines[number]['date_stop'], date_format).strftime(date_format_html)}</td>
	        <td class="benefit_card">${pos06}</td>
	
	        %if lines[number]['zasilek'] != 'Sick pay':
		        <td class="benefit_card">${formatLang(pos07)}</td>
		        <td class="benefit_card">${formatLang(pos08)}</td>
		        <td class="benefit_card">${formatLang(pos09)}</td>
		        <td class="benefit_card">${formatLang(pos10)}</td>
		        <td class="benefit_card">${formatLang(pos11)}</td>
		        <td class="benefit_card">${pos12}</td>
		    %else:
		    	<td></td>
	        	<td></td>
	        	<td></td>
	        	<td></td>
	        	<td></td>
	        	<td></td>
		    %endif
		    
	        <td class="benefit_card"></td>
	        <td class="benefit_card">${pos14_1} - ${pos14_2}</td>
	        <td class="benefit_card">${formatLang(pos15)}</td>
	        <td class="benefit_card">${pos16}</td>
	    </tr>
    %endfor
</%def>

    <head>
        <meta charset="utf-8" />
        <style type="text/css">
            ${css}
        </style>
    </head>
    <body>
    %for o in objects:
        <% setLang(user.context_lang) %>
        <% udata = get_data(data['lines_ids'][str(o.id)]) %>
        <% data_length = len(udata["lines"]) %>
        <div id="container">
	        <table id="benefit_card_header">
	            <tr>
	                <td colspan="4" class="benefit_card">KARTA ZASIŁKOWA</td>
	            </tr>
	            <tr>
	                <td colspan="2" class="benefit_card_header benefit_card">
	                    ${udata["surname"]}&nbsp;${udata["employee_name"]}<br>
	                    <hr class="benefit_card">
	                    Nazwisko i imię ubezp.
	                </td>
	                <td class="benefit_card_46 benefit_card_header benefit_card">
	                    ${"----------" if udata["birthday"]=="----------" else formatLang(udata["birthday"],date=True)}<br>
	                    <hr class="benefit_card">
	                    data urodzenia
	                </td>
	                <td rowspan="2" class="benefit_card_54 benefit_card_header benefit_card">
	                    Poprzednie ubezpieczenie chorobowe ustało dnia<br><br>
	                    <hr class="benefit_card">
	                    <!--${"----------" if udata["previous_insurance_end"]=="----------" else formatLang(udata["previous_insurance_end"],date=True)}-->
	                </td>
	            </tr>
	            <tr>
	                <td class="benefit_card_78 benefit_card">PESEL&nbsp;${udata["ssnid"]}</td>
	                <td class="benefit_card_78 benefit_card">NIP**&nbsp;${udata["sinid"]}</td>
	                <td colspan="2"></td>
	            </tr>
	            <tr>
	                <td colspan="3" class="benefit_card">
	                    Wym. zatrudniony - objęty ubezpieczeniem chorobowym od
	                    ${"----------" if udata["employed_from"]=="----------" else formatLang(udata["employed_from"],date=True)} zwolniony - wyłączony z ubezp. dn.
	                    ${"----------" if udata["employed_to"]=="----------" else formatLang(udata["employed_to"],date=True)}<br><br><br>
	                    <div class="float_left">Uwagi</div>
	                    <hr class="benefit_card"><br><br>
	                    <hr class="benefit_card">
	                </td>
	                <td class="benefit_card_header benefit_card_signature benefit_card">
	                    data, podpis
	                </td>
	            </tr>
	            <tr>
	                <td colspan="4" class="benefit_card">
	                    * Przy wypłacie wynagrodzenia przysługującego z tytułu
	                    niezdolności do pracy wypełnia się rubryki 4-6, 13-16<br>
	                    ** W razie gdy ubezpieczonemu nie nadano PESEL i NIP albo jednego z
	                    nich, należy wpisać serię i numer dowodu osobistego lub
	                    paszportu.
	                </td>
	            </tr>
	        </table>
            <% ind = 10 %>
	        %if data_length < ind:
	            <table>
	                ${line(0,data_length,udata)}
	                ${empty(ind-data_length)}
	            </table>
	        %else:
	            <% cnt = 18 %>
	            <% pages = int(ceil((data_length-ind)/float(cnt)))+1 %>
	            %for page in range(0,pages):
	                %if page:
	                </div>
	                <div id="break"></div>
                    <div id="container">
	                    %if (page+1)*(cnt-1) > data_length:
	                    <table>
	                        ${line(ind-cnt,data_length,udata)}
	                        ${empty(ind-data_length)}
	                    </table>
	                    %else:
	                    <table>
	                        ${line(ind-cnt,ind,udata)}
	                    </table>
	                    %endif
	                %else:
	                <table>
	                    ${line(0,ind,udata)}
	                </table>
	                %endif
	                <% ind += cnt %>
	            %endfor
	        %endif
        </div>
    %endfor
    </body>
</html>