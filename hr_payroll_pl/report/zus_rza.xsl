<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

	<xsl:template match="/">
		<KEDU wersja_schematu="1" xmlns="http://www.zus.pl/2013/KEDU_4"
		xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
		xsi:schemaLocation="http://www.zus.pl/bip/pliki/kedu_4.xsd">
			<naglowek.KEDU>
				<program>
					<producent>Asseco Poland SA</producent>
					<symbol>Płatnik</symbol>
					<wersja>901001</wersja>
				</program>
			</naglowek.KEDU>
            <ZUSRCA status_kontroli="0" status_weryfikacji="P">
				<xsl:attribute name="id_dokumentu">
					<xsl:value-of select="report/employer/RCA_id" />
				</xsl:attribute>
				<I>
					<p1>
						<p1><xsl:value-of select="report/employer/I02_1"/></p1>
						<p2><xsl:value-of select="report/employer/I02_2"/></p2>
					</p1>
				</I>
				<II>
					<p1><xsl:value-of select="report/employer/II01"/></p1>
					<p2><xsl:value-of select="report/employer/II02"/></p2>
					<p6><xsl:value-of select="report/employer/II06"/></p6>
				</II>
				<xsl:for-each select="report/employees/employee">
				<III status_kontroli="0" status_weryfikacji="P">
					<xsl:attribute name="id_bloku">
						<xsl:value-of select="id" />
					</xsl:attribute>
					<A>
						<p1><xsl:value-of select="IIIA01"/></p1>
						<p2><xsl:value-of select="IIIA02"/></p2>
						<p3><xsl:value-of select="IIIA03"/></p3>
						<p4><xsl:value-of select="IIIA04"/></p4>
					</A>
					<B>
						<p1>
							<p1><xsl:value-of select="IIIB01_1"/></p1>
							<p2><xsl:value-of select="IIIB01_2"/></p2>
							<p3><xsl:value-of select="IIIB01_3"/></p3>
						</p1>
						<p3>
							<p1><xsl:value-of select="IIIB03_1"/></p1>
							<p2><xsl:value-of select="IIIB03_2"/></p2>
						</p3>
						<p4><xsl:value-of select="IIIB04"/></p4>
						<p5><xsl:value-of select="IIIB04"/></p5>
						<p6><xsl:value-of select="IIIB04"/></p6>
						<p7><xsl:value-of select="IIIB07"/></p7>
						<p8><xsl:value-of select="IIIB08"/></p8>
						<p9><xsl:value-of select="IIIB09"/></p9>
						<p10><xsl:value-of select="IIIB10"/></p10>
						<p11><xsl:value-of select="IIIB11"/></p11>
						<p12><xsl:value-of select="IIIB12"/></p12>
						<p13><xsl:value-of select="IIIB13"/></p13>
						<p14><xsl:value-of select="IIIB14"/></p14>
						<p15><xsl:value-of select="IIIB15"/></p15>
						<p16><xsl:value-of select="IIIB16"/></p16>
						<p17><xsl:value-of select="IIIB17"/></p17>
						<p18><xsl:value-of select="IIIB18"/></p18>
						<p19><xsl:value-of select="IIIB19"/></p19>
						<p20><xsl:value-of select="IIIB20"/></p20>
						<p21><xsl:value-of select="IIIB21"/></p21>
						<p22><xsl:value-of select="IIIB22"/></p22>
						<p23><xsl:value-of select="IIIB23"/></p23>
						<p24><xsl:value-of select="IIIB24"/></p24>
						<p25><xsl:value-of select="IIIB25"/></p25>
						<p26><xsl:value-of select="IIIB26"/></p26>
						<p27><xsl:value-of select="IIIB27"/></p27>
						<p28><xsl:value-of select="IIIB28"/></p28>
					</B>
					<C>
						<p1><xsl:value-of select="IIIC01"/></p1>
						<p2><xsl:value-of select="IIIC02"/></p2>
						<p3><xsl:value-of select="IIIC03"/></p3>
						<p4><xsl:value-of select="IIIC04"/></p4>
						<p5><xsl:value-of select="IIIC05"/></p5>
					</C>
					<D>
						<p1><xsl:value-of select="IIID01"/></p1>
						<p2><xsl:value-of select="IIID02"/></p2>
						<p3><xsl:value-of select="IIID03"/></p3>
						<p4><xsl:value-of select="IIID04"/></p4>
					</D>
				</III>
				</xsl:for-each>
				<V>
					<p1><xsl:value-of select="report/employer/XI01"/></p1>
				</V>
			</ZUSRCA>
			
            <ZUSRZA status_kontroli="0" status_weryfikacji="P">
				<xsl:attribute name="id_dokumentu">
					<xsl:value-of select="report/employer/RZA_id" />
				</xsl:attribute>
				<I>
					<p1>
						<p1><xsl:value-of select="report/employer/I02_1"/></p1>
						<p2><xsl:value-of select="report/employer/I02_2"/></p2>
					</p1>
				</I>
				<II>
					<p1><xsl:value-of select="report/employer/II01"/></p1>
					<p2><xsl:value-of select="report/employer/II02"/></p2>
					<p6><xsl:value-of select="report/employer/II06"/></p6>
				</II>
				<xsl:for-each select="report/employees/employee">
				<III status_kontroli="0" status_weryfikacji="P">
					<xsl:attribute name="id_bloku">
						<xsl:value-of select="id" />
					</xsl:attribute>
					<A>
						<p1><xsl:value-of select="IIIA01"/></p1>
						<p2><xsl:value-of select="IIIA02"/></p2>
						<p3><xsl:value-of select="IIIA03"/></p3>
						<p4><xsl:value-of select="IIIA04"/></p4>
					</A>
					<B>
						<p1>
							<p1><xsl:value-of select="IIIB01_1"/></p1>
							<p2><xsl:value-of select="IIIB01_2"/></p2>
							<p3><xsl:value-of select="IIIB01_3"/></p3>
						</p1>
						<p2><xsl:value-of select="IIIC01"/></p2>
						<p5><xsl:value-of select="IIIC04"/></p5>
					</B>
				</III>
				</xsl:for-each>
				<VIII>
					<p1><xsl:value-of select="report/employer/XI01"/></p1>
				</VIII>
			</ZUSRZA>

            <ZUSDRA status_kontroli="0" status_weryfikacji="P">
				<xsl:attribute name="id_dokumentu">
					<xsl:value-of select="report/employer/DRA_id" />
				</xsl:attribute>
				<I>
					<p1><xsl:value-of select="report/employer/I01"/></p1>
					<p2>
						<p1><xsl:value-of select="report/employer/I02_1"/></p1>
						<p2><xsl:value-of select="report/employer/I02_2"/></p2>
					</p2>
				</I>
				<II>
					<p1><xsl:value-of select="report/employer/II01"/></p1>
					<p2><xsl:value-of select="report/employer/II02"/></p2>
					<p6><xsl:value-of select="report/employer/II06"/></p6>
				</II>
				<III>
					<p1><xsl:value-of select="report/employer/III01"/></p1>
					<p2><xsl:value-of select="report/employer/III02"/></p2>
					<p3><xsl:value-of select="report/employer/III03"/></p3>
				</III>
				<IV>
					<p1><xsl:value-of select="report/employer/IV01"/></p1>
					<p2><xsl:value-of select="report/employer/IV02"/></p2>
					<p3><xsl:value-of select="report/employer/IV03"/></p3>
					<p4><xsl:value-of select="report/employer/IV04"/></p4>
					<p5><xsl:value-of select="report/employer/IV05"/></p5>
					<p6><xsl:value-of select="report/employer/IV06"/></p6>
					<p7><xsl:value-of select="report/employer/IV07"/></p7>
					<p8><xsl:value-of select="report/employer/IV08"/></p8>
					<p9><xsl:value-of select="report/employer/IV09"/></p9>
					<p10><xsl:value-of select="report/employer/IV10"/></p10>
					<p11><xsl:value-of select="report/employer/IV11"/></p11>
					<p12><xsl:value-of select="report/employer/IV12"/></p12>
					<p13><xsl:value-of select="report/employer/IV13"/></p13>
					<p14><xsl:value-of select="report/employer/IV14"/></p14>
					<p15><xsl:value-of select="report/employer/IV15"/></p15>
					<p16><xsl:value-of select="report/employer/IV16"/></p16>
					<p17><xsl:value-of select="report/employer/IV17"/></p17>
					<p18><xsl:value-of select="report/employer/IV18"/></p18>
					<p19><xsl:value-of select="report/employer/IV19"/></p19>
					<p20><xsl:value-of select="report/employer/IV20"/></p20>
					<p21><xsl:value-of select="report/employer/IV21"/></p21>
					<p22><xsl:value-of select="report/employer/IV22"/></p22>
					<p23><xsl:value-of select="report/employer/IV23"/></p23>
					<p24><xsl:value-of select="report/employer/IV24"/></p24>
					<p25><xsl:value-of select="report/employer/IV25"/></p25>
					<p26><xsl:value-of select="report/employer/IV26"/></p26>
					<p27><xsl:value-of select="report/employer/IV27"/></p27>
					<p28><xsl:value-of select="report/employer/IV28"/></p28>
					<p29><xsl:value-of select="report/employer/IV29"/></p29>
					<p30><xsl:value-of select="report/employer/IV30"/></p30>
					<p31><xsl:value-of select="report/employer/IV31"/></p31>
					<p32><xsl:value-of select="report/employer/IV32"/></p32>
					<p33><xsl:value-of select="report/employer/IV33"/></p33>
					<p34><xsl:value-of select="report/employer/IV34"/></p34>
					<p35><xsl:value-of select="report/employer/IV35"/></p35>
					<p36><xsl:value-of select="report/employer/IV36"/></p36>
					<p37><xsl:value-of select="report/employer/IV37"/></p37>
				</IV>
				<V>
					<p1><xsl:value-of select="report/employer/V01"/></p1>
					<p2><xsl:value-of select="report/employer/V02"/></p2>
					<p3><xsl:value-of select="report/employer/V03"/></p3>
					<p4><xsl:value-of select="report/employer/V04"/></p4>
					<p5><xsl:value-of select="report/employer/V05"/></p5>
				</V>
				<VI>
					<p1><xsl:value-of select="report/employer/VI01"/></p1>
					<p2><xsl:value-of select="report/employer/VI02"/></p2>
				</VI>
				<VII>
					<p1><xsl:value-of select="report/employer/VII01"/></p1>
					<p2><xsl:value-of select="report/employer/VII02"/></p2>
					<p3><xsl:value-of select="report/employer/VII03"/></p3>
					<p4><xsl:value-of select="report/employer/VII04"/></p4>
					<p5><xsl:value-of select="report/employer/VII05"/></p5>
					<p6><xsl:value-of select="report/employer/VII06"/></p6>
					<p7><xsl:value-of select="report/employer/VII07"/></p7>
				</VII>
				<VIII>
					<p1><xsl:value-of select="report/employer/VIII01"/></p1>
					<p2><xsl:value-of select="report/employer/VIII02"/></p2>
					<p3><xsl:value-of select="report/employer/VIII03"/></p3>
				</VIII>
				<IX>
					<p1>0</p1>
					<p2>0</p2>
				</IX>
				<XI>
					<p1><xsl:value-of select="report/employer/XI01"/></p1>
				</XI>
			</ZUSDRA>
		</KEDU>
	</xsl:template>
</xsl:stylesheet>